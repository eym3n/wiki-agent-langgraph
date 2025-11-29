from datetime import datetime
from langchain_core.messages import SystemMessage
from src.agent.state import AgentState
from src.agent.prompts.reply_prompt import get_reply_prompt
from src.core.config import get_settings


def _get_llm():
    settings = get_settings()
    if settings.use_groq:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.7,
            reasoning_format="hidden",
        )
    else:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.7,
        )


class ReplyNode:
    def __init__(self, model_name: str = None):
        self.llm = _get_llm()

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYS = SystemMessage(content=get_reply_prompt(current_datetime))
        messages = [SYS] + state.messages
        response = self.llm.invoke(messages)
        return {"messages": [response]}
