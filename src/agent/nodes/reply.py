from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from src.agent.state import AgentState
from src.agent.prompts.reply_prompt import get_reply_prompt


class ReplyNode:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.7)

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYS = SystemMessage(content=get_reply_prompt(current_datetime))
        messages = [SYS] + state.messages
        response = self.llm.invoke(messages)
        return {"messages": [response]}
