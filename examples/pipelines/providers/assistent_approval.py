
from typing import List, Union, Generator, Iterator
from schemas import OpenAIChatMessage
from pydantic import BaseModel
import requests


class Pipeline:
    class Valves(BaseModel):
        # You can add your custom valves here.
        AZURE_OPENAI_API_KEY: str = "your-azure-openai-api-key-here"
        AZURE_OPENAI_ENDPOINT: str = "https://gpt4--0125.openai.azure.com"
        DEPLOYMENT_NAME: str = "gpt-4o"
        API_VERSION: str = "2024-02-15-preview"
        MODEL: str = "gpt-4o"
        pass

    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "azure_openai_pipeline"
        self.name = "审批助手"
        self.valves = self.Valves()
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    HEADERS = {
        "Content-Type": "application/json",
        "api-key": self.values.AZURE_OPENAI_API_KEY,
    }
    def list_assistants(order="desc", limit=20):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/assistants?order={order}&limit={limit}&api-version={self.values.API_VERSION}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()["data"]

    def create_assistant(name, instructions, tools, file_ids):
        existing_assistants = list_assistants()
        for assistant in existing_assistants:
            if assistant["name"] == name:
                return assistant

        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/assistants?api-version={self.values.API_VERSION}"
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

    def create_thread():
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads?api-version={self.values.API_VERSION}"
        response = requests.post(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def create_message(thread_id, role, content):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/messages?api-version={self.values.API_VERSION}"
        payload = {
            "role": role,
            "content": content,
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def create_run(thread_id, assistant_id):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/runs?api-version={self.values.API_VERSION}"
        payload = {
            "assistant_id": assistant_id,
        }
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def retrieve_run(thread_id, run_id):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/runs/{run_id}?api-version={self.values.API_VERSION}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()

    def list_messages(thread_id):
        url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/threads/{thread_id}/messages?api-version={self.values.API_VERSION}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()["data"]

    def return_messages(messages):
        print("messages: ")
        for message in messages:
            if message["content"][0]["type"] == "text":
                return {"role": message["role"], "message": message["content"][0]["text"]["value"]}



    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        print(f"pipe:{__name__}")

        print(messages)
        print(user_message)

        assistant = create_assistant(
            name="审批助手",
            instructions="",
            tools=[{"type": "code_interpreter"}],
            file_ids=["assistant-mu22n2FwSozhavaYyp8sDrOc", "assistant-O2p8phMYlWff6bIKutpSjhvc"]
        )
        thread = create_thread()

        message = create_message(thread_id=thread["id"], role="user", content="我想要看第一个待审批信息")

        run = create_run(thread_id=thread["id"], assistant_id=assistant["id"])

        #url = f"{self.valves.AZURE_OPENAI_ENDPOINT}/openai/deployments/{self.valves.DEPLOYMENT_NAME}/chat/completions?api-version={self.valves.API_VERSION}"

        try:
            while True:
                run_status = retrieve_run(thread_id=thread["id"], run_id=run["id"])

                if run_status["status"] == "completed":
                    messages = list_messages(thread_id=thread["id"])
                    return return_messages(messages)
                    break
                elif run_status["status"] in ["requires_action", "expired", "failed", "cancelled"]:
                    break
                else:
                    print("in progress...")
                    time.sleep(5)
        except Exception as e:
            return f"Error: {e}"
