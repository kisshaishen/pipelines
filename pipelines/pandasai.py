from typing import List, Union, Generator, Iterator
from pydantic import BaseModel
import requests


class Pipeline:
    class Valves(BaseModel):
        PANDASAI_ENDPOINT: str = "https://localhost:8000/api/pandasai/chat"
        PROVIDER: str = "qianfan"
        MODEL: str = "ERNIE-4.0-8K"
        # PANDASAI_ENDPOINT: str = "http://127.0.0.1:8000/api/pandasai/chat"

    def __init__(self):
        self.name = "审批助手-PowerByPandasAI"
        self.valves = self.Valves()

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(
            self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        payload = {
            "chat_id": body.get("chat_id"),
            "message": user_message,
            "model": self.valves.MODEL,
            "provider": self.valves.PROVIDER
        }

        response = requests.post(
            self.valves.PANDASAI_ENDPOINT,
            json=payload,
        )

        ret = response.json()
        return str(ret["answer"])
