import re
import json
from datetime import datetime
from typing import List, Any
import logging
from langchain_core.tools import StructuredTool
from langchain_core.messages import SystemMessage
from langchain_core.messages.base import BaseMessage
from src.agent.state import AgentState
from src.agent.prompts.context_prompt import get_context_prompt
from src.core.config import get_settings

logger = logging.getLogger(__name__)


WIKIPEDIA_URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+")


def _get_llm():
    settings = get_settings()
    if settings.use_groq:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0,
            reasoning_format="hidden",
        )
    else:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )


def _collect_urls_from_obj(obj: Any, seen: set[str], urls: List[str]):
    if obj is None:
        return
    if isinstance(obj, str):
        # Try to parse as JSON first
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, (dict, list)):
                _collect_urls_from_obj(parsed, seen, urls)
                return
        except json.JSONDecodeError:
            pass

        for match in WIKIPEDIA_URL_PATTERN.findall(obj):
            url = match.rstrip(".,);\"'")
            if "wikipedia.org" in url.lower() and url not in seen:
                seen.add(url)
                urls.append(url)
    elif isinstance(obj, dict):
        for value in obj.values():
            _collect_urls_from_obj(value, seen, urls)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            _collect_urls_from_obj(item, seen, urls)


def _extract_wikipedia_urls(messages: List[BaseMessage]) -> List[str]:
    urls: List[str] = []
    seen: set[str] = set()
    for message in messages:
        _collect_urls_from_obj(getattr(message, "content", None), seen, urls)
        _collect_urls_from_obj(getattr(message, "additional_kwargs", None), seen, urls)
        _collect_urls_from_obj(getattr(message, "tool_calls", None), seen, urls)
        _collect_urls_from_obj(getattr(message, "artifact", None), seen, urls)

        # If we have a tool call with arguments that include a 'title', we can construct the URL as a fallback.
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                if tc.get("name") in [
                    "get_summary",
                    "get_article",
                    "extract_key_facts",
                ]:
                    args = tc.get("args", {})
                    title = args.get("title")
                    if title:
                        safe_title = title.replace(" ", "_")
                        url = f"https://en.wikipedia.org/wiki/{safe_title}"
                        if url not in seen:
                            seen.add(url)
                            urls.append(url)

    return urls


class ContextNode:
    def __init__(self, tools: List[StructuredTool], model_name: str = None):
        self.llm = _get_llm()
        self.llm_with_tools = self.llm.bind_tools(tools)

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYS = SystemMessage(content=get_context_prompt(current_datetime))
        messages = [SYS] + state.messages

        response = self.llm_with_tools.invoke(messages)
        logger.info(f"ContextNode response: {response}")

        # Only extract URLs from the NEW response, not from history
        urls = _extract_wikipedia_urls([response])

        # Merge with URLs already found in this run (from previous context node calls in this run)
        current_urls = state.referenced_article_urls or []
        all_urls = list(dict.fromkeys(current_urls + urls))
        logger.info(f"Extracted URLs: {urls}. Total merged URLs: {all_urls}")

        return {"messages": [response], "referenced_article_urls": all_urls}
