from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from src.agent.state import AgentState
from src.agent.prompts.reply_prompt import get_reply_prompt
from src.core.config import get_settings


class ReplyNode:
    def __init__(self, model_name: str = None):
        settings = get_settings()
        model = model_name or settings.ollama_model
        self.llm = ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=0.7
        )

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYS = SystemMessage(content=get_reply_prompt(current_datetime))
        messages = [SYS] + state.messages
        response = self.llm.invoke(messages)
        return {"messages": [response]}
