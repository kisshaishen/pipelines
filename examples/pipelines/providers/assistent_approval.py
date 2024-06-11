from typing import List, Union, Generator, Iterator
from schemas import OpenAIChatMessage
from pydantic import BaseModel
import requests
import time
import json
import openai


class Pipeline:
    class Valves(BaseModel):
        # You can add your custom valves here.
        AZURE_OPENAI_API_KEY: str = "your-azure-openai-api-key-here"
        AZURE_OPENAI_ENDPOINT: str = "https://gpt4--0125.openai.azure.com"
        DEPLOYMENT_NAME: str = "gpt-4o"
        API_VERSION: str = "2024-02-15-preview"
        MODEL: str = "gpt-4o"
        pass

    # class State:
    #     ChatId: str = ""
    #     CreateThread: bool = False
    #     AssistantId: str = ""
    #     ThreadId: str = ""
    #     UserName: str = ""

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "assistent_approval"
        self.name = "审批助手"
        self.valves = self.Valves()
        # self.state = self.State()
        self.state = {}
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def list_assistants(self, HEADERS, order="desc", limit=20):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/assistants?order={order}&limit={limit}&api-version={self.valves.API_VERSION}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()["data"]

    def create_assistant(self, HEADERS, name, instructions, tools, file_ids, userName):
        existing_assistants = self.list_assistants(HEADERS)
        for assistant in existing_assistants:
            if userName == "周林":
                if assistant["name"] == "审批助手_周总":
                    return self.update_assistant(HEADERS, assistant["id"], "审批助手_周总", instructions, tools, file_ids)
                    #return assistant
            elif userName == "苏婷":
                if assistant["name"] == "审批助手_财务":
                    return self.update_assistant(HEADERS, assistant["id"], "审批助手_财务", instructions, tools, file_ids)
                    #return assistant
            else:
                if assistant["name"] == "审批助手_财务":
                    return self.update_assistant(HEADERS, assistant["id"], "审批助手_财务", instructions, tools, file_ids)

        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/assistants?api-version={self.valves.API_VERSION}"
        payload = {
            "name": name,
            "instructions": instructions,
            "tools": tools,
            "model": "gpt-4o",
            "file_ids": file_ids,
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def update_assistant(self, HEADERS, assistantId, name, instructions, tools, file_ids): 
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/assistants/{assistantId}?api-version={self.valves.API_VERSION}"
        payload = {
            #"name": name,
            "instructions": instructions,
            "tools": tools,
            "model": "gpt-4o",
            #"file_ids": file_ids,
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def create_thread(self, HEADERS):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads?api-version={self.valves.API_VERSION}"
        response = requests.post(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def create_message(self, HEADERS, thread_id, role, content):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/messages?api-version={self.valves.API_VERSION}"
        payload = {
            "role": role,
            "content": content,
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def create_run(self, HEADERS, thread_id, assistant_id):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/runs?api-version={self.valves.API_VERSION}"
        payload = {
            "assistant_id": assistant_id,
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def retrieve_run(self, HEADERS, thread_id, run_id):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/runs/{run_id}?api-version={self.valves.API_VERSION}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def submit_tool_outputs(self, HEADERS, thread_id, run_id, tool_outputs):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/runs/{run_id}/submit_tool_outputs?api-version={self.valves.API_VERSION}"
        
        print("submit")
        response = requests.post(url, json=tool_outputs, headers=HEADERS)
        response.raise_for_status()
        
        print(response.json())
        
        return response.json()

    def list_messages(self, HEADERS, thread_id):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/messages?api-version={self.valves.API_VERSION}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()["data"]

    def return_messages(self, messages):
        print("messages: ")
        for message in messages:
            if message["content"][0]["type"] == "text":
                print(message)
                # return {"role": message["role"], "message": message["content"][0]["text"]["value"]}
                return message["content"][0]["text"]["value"]

    def projectapproval(self, eisId, approvalStatus, chatId, remark=""):
        """
            项目审批
            @parm eisId: Eis项目的ID
            @parm approvalStatus: 审批状态， 1为通过，3为拒绝
            @parm remark: 审批及拒绝的原因
        """
        #print(f"approve: eisId: {eisId}, approvalStatus: {approvalStatus}, remark: {remark}")
        url = f"https://pbmcron.service.xiaoyangedu.net/api/callback/approval"
        payload = {
            "username": self.state[chatId]["UserName"],
            "EIS_ID": eisId,
            "approval": approvalStatus,
            "remark": remark
        }
        HEADERS = {
                "Content-Type": "application/json",
                #"api-key": self.valves.AZURE_OPENAI_API_KEY,
            }
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()

        print(response.json())

        rst = "审批已完成"
        if response.json()["code"] != 1:
            rst = f'审批失败, 错误信息：{response.json()["msg"]}'

        return rst

        #return "审批已完成"

    def poll_run_till_completion(
        self,
        HEADERS,
        threadId: str,
        runId: str,
        available_functions: dict,
        chatId: str,
        max_steps: int = 10,
        wait: int = 3,
    ) -> None:
        """
        Poll a run until it is completed or failed or exceeds a certain number of iterations (MAX_STEPS)
        with a preset wait in between polls

        @param thread_id: Thread ID
        @param run_id: Run ID
        @param assistant_id: Assistant ID
        @param max_steps: Maximum number of steps to poll
        @param wait: Wait time in seconds between polls

        """

        if (threadId is None) or runId is None:
            print("Thread ID and Run ID are required.")
            return

        try:
            cnt = 0
            while cnt < max_steps:
                
                run_status = self.retrieve_run(HEADERS, thread_id=threadId, run_id=runId)
                cnt += 1
                
                if run_status["status"] == "requires_action":
                    tool_responses = {"tool_outputs": []}
                    if (
                        run_status["required_action"]["type"] == "submit_tool_outputs"
                        and run_status["required_action"]["submit_tool_outputs"]["tool_calls"] is not None
                    ):
                        tool_calls = run_status["required_action"]["submit_tool_outputs"]["tool_calls"]
                        print(f'tool_calls: {tool_calls}')
       
                        for call in tool_calls:
                            if call["type"] == "function":
                                if call["function"]["name"] not in available_functions:
                                    raise Exception("Function requested by the model does not exist")
                                
                                function_to_call = available_functions[call["function"]["name"]]

                                arguments = json.loads(call["function"]["arguments"])
                                arguments["chatId"] = chatId

                                tool_response = function_to_call(**arguments)
                                tool_responses["tool_outputs"].append({"tool_call_id": call["id"], "output": tool_response})
                                print(f"tool_responses: {tool_responses}")

                    print("start submit")
                    self.submit_tool_outputs(
                        HEADERS, thread_id=threadId, run_id=runId, tool_outputs=tool_responses
                    )
                if run_status["status"] == "failed":
                    print("Run failed.")
                    break
                if run_status["status"] == "completed":
                    break
                time.sleep(wait)
            
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: {e}"


    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        HEADERS = {
                "Content-Type": "application/json",
                "api-key": self.valves.AZURE_OPENAI_API_KEY,
            }
        #self.valves.HEADERS.

        print(messages)
        print(user_message)
        print(body)

        '''
            基于WebUI的chatId来判断当前是否为新的thread
        '''
        # if self.state.ChatId == "":
        #     print("first chat!")
        #     self.state.ChatId = body["chat_id"]
        #     self.state.CreateThread = True
        # else:
        #     print("continue chat!")
        #     self.state.CreateThread = False
        #     print(self.state.ThreadId)
        #     if self.state.ChatId != body["chat_id"]:
        #         print("change chat Id!")
        #         self.state.ChatId = body["chat_id"]
        #         self.state.CreateThread = True
        #     if self.state.AssistantId == "" or self.state.ThreadId == "":
        #         print("miss assistant or thread!")
        #         self.state.ChatId = body["chat_id"]
        #         self.state.CreateThread = True

        chatId = body["chat_id"]
        createThread = False
        if chatId not in self.state:
            createThread = True

        print("Start")

        if createThread:
            assistant = self.create_assistant(
                HEADERS,
                name="审批助手_财务",
                instructions='''
                    你是一个审批助手，为相关的审批者提供数据，并通过tools来完成最终的审批数据提交工作，你需要尽量以自然语言来跟用户进行交互，
                    对收集到的数据进行适合的转换，对数据进行文字摘要或表格化处理，以便于用户浏览。
                    当用户想要查看审批数据时，你应该主要以项目表进行，并且应该只读取一条信息出来，并以自然语言形成简报,当用户需要具体表的详细信息时，尽量以表格形式提供
                    ------------------------------------------------------------
                    除项目表之外的关联表查询每次应该只查询出与当前项目相关的所有数据，例如查询一条项目简报中的EisId相关的所有指标数据
                    ------------------------------------------------------------
                    所有数据查询的结果，都需要显示EIS_ID, 但不用特别强调，它将作为Function-Call的重要参数
                    ------------------------------------------------------------
                    目前的数据主要是几个csv文件，几个文件是以EIS_ID进行的关联，每张表的描述如下：
                    1. 项目表，待审批项目的主要数据，也是用户需要查询的主要数据，是所有数据的基础，通过EIS_ID与其他数据文件进行关联
                    2. 指标表，通过EIS_ID与项目表进行关联，当用户需要查询指标数据时应取所有EIS_ID相关的指标数据返回, 并注意指标表中的结果字段以"是"跟"否"来显示
                    3. 利润表，通过EIS_ID与项目表进行关联，当用户需要查询利润数据时应取所有EIS_ID相关的利润数据返回，利润表中相关项目各项数据以表格呈现
                    4. 现金流量表，通过EIS_ID与项目表进行关联，当用户需要查询现金流量信息时，应取所有EIS_ID相关的现金流量数据返回，以表格形式呈现
                    ------------------------------------------------------------
                    注意，当用户要求进行审批时，你必须要把主要信息列举一下，等待用户二次确认，例如：商机名称，销售姓名，立项日期，客户名称，以及EIS_ID, 商机编号等信息，将这些信息组成一个简报
                    展示给用户，等用户再次确认后，再进行Function-Call的调用
                    审批确认完成后，你需要返回审批结果，并再次检查目前还有多少待审批的数据，并引导进行下一条项目的审批工作。       
                    ------------------------------------------------------------      
                ''',
                tools=[
                        {"type": "code_interpreter"},
                        {
                            "type": "function",
                            "function" : {
                                "name": "projectapproval",
                                "description": "对项目数据进行审批，可以是通过审批或拒绝审批",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                    "eisId": {
                                        "type": "integer",
                                        "description": "项目表数据中的EisID, 用于标记是哪个项目"
                                    },
                                    "approvalStatus": {
                                        "type": "integer",
                                        "description": "审批通过对应值为5， 不通过对应值为3"
                                    },
                                    "remark": {
                                        "type": "string",
                                        "description": "描述信息，用于描述通过意见或拒绝意见, 拒绝时remark是必须的"
                                    }
                                    },
                                    "required": [
                                    "eisId", "approvalStatus"
                                    ]
                                }
                            }
                        }
                    ],
                file_ids=["assistant-JKbclOdlDt1CFbAxONi3wMty", 
                        "assistant-t2zSJ0qQ34hthSEmnpvEydJB",
                        "assistant-ZAczI4vLPoTKLQEUJZ98HVYR",
                        "assistant-ourPtuJ8sRnvhFtiFjmZMjeA",
                        "assistant-RU44oWpxiZrDncpOwYZcD9PH"
                        ],
                userName=body["user"]["name"]
                
            )
            # self.state.AssistantId = assistant["id"]

            print("create thread!")
            thread = self.create_thread(HEADERS)
            # self.state.ThreadId = thread["id"]
            # self.state.UserName = body["user"]["name"]
            self.state[chatId] = {"AssistantId": assistant["id"], "ThreadId": thread["id"], "UserName": body["user"]["name"]}

        print("Chat Infomation")
        print(f"ChatID: {chatId}, Data: {self.state[chatId]}")

        print("create message!")
        message = self.create_message(HEADERS, thread_id=self.state[chatId]["ThreadId"], role="user", content=user_message)

        print("create run!")
        run = self.create_run(HEADERS, thread_id=self.state[chatId]["ThreadId"], assistant_id=self.state[chatId]["AssistantId"])

        availableFunctions = {"projectapproval": self.projectapproval}

        print("check function call")
        self.poll_run_till_completion(HEADERS, threadId=self.state[chatId]["ThreadId"], runId=run["id"], available_functions=availableFunctions, chatId=chatId)

        #url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/deployments/{self.valves.DEPL``OYMENT_NAME}/chat/completions?api-version={self.valves.API_VERSION}"

        print("check response!")
        try:
            while True:
                run_status = self.retrieve_run(HEADERS, thread_id=self.state[chatId]["ThreadId"], run_id=run["id"])

                if run_status["status"] == "completed":
                    messages = self.list_messages(HEADERS, thread_id=self.state[chatId]["ThreadId"])                    
                    rst = self.return_messages(messages)
                    print(rst)
                    return rst
                    break
                elif run_status["status"] in ["requires_action", "expired", "failed", "cancelled"]:
                    break
                else:
                    print("in progress...")
                    time.sleep(5)

            # r = requests.post(
            #     url=url,
            #     json={**body, "model": self.valves.MODEL},
            #     headers=headers,
            #     stream=True,
            # )

            # r.raise_for_status()
            # if body["stream"]:
            #     return r.iter_lines()
            # else:
            #     return r.json()
        except Exception as e:
            return f"Error: {e}"
