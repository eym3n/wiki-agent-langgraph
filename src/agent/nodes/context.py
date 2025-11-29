import re
import json
from datetime import datetime
from typing import List, Iterable, Any
import logging
from langchain_core.tools import StructuredTool
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langchain_core.messages.base import BaseMessage
from src.agent.state import AgentState
from src.agent.prompts.context_prompt import get_context_prompt
from src.core.config import get_settings

logger = logging.getLogger(__name__)


WIKIPEDIA_URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+")


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
        # Log message type and content for debugging
        # logger.info(f"Scanning message type: {type(message)}")

        # For ToolMessage, the content is often the tool output directly
        # But ToolMessage doesn't have a "name" attribute in some versions, it uses "name" or "tool_name" or we check type
        # Actually ToolMessage has 'name' field.
        # Let's check if the message is indeed a ToolMessage or has tool output.

        # The previous check `if hasattr(message, "name") ...` might fail if `name` isn't what we expect or if it's not a ToolMessage.
        # We should check for ToolMessage type explicitly if possible, or just leniently scan everything.

        # Also, the logs show that the tool output MIGHT NOT contain the URL explicitly if it's just a summary.
        # "Request URL: .../api.php..." -> This is wikipediaapi logging the request.
        # The tool output is what the MCP server returns.
        # If the MCP server returns just text, and that text doesn't contain "https://en.wikipedia.org...", then we won't find it.

        # We need to check if `wikipedia-mcp` tool outputs include the URL.
        # If not, we might need to synthesize the URL from the title if available.
        # But let's first ensure we are scanning the right content.

        _collect_urls_from_obj(getattr(message, "content", None), seen, urls)
        _collect_urls_from_obj(getattr(message, "additional_kwargs", None), seen, urls)
        _collect_urls_from_obj(getattr(message, "tool_calls", None), seen, urls)
        _collect_urls_from_obj(getattr(message, "artifact", None), seen, urls)

        # If we have a tool call with arguments that include a 'title', we can construct the URL as a fallback.
        # This is a heuristic.
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
                        # Construct URL
                        # Assuming English wikipedia for now or use logic to determine language
                        # Title needs to be URL encoded (spaces to underscores etc)
                        safe_title = title.replace(" ", "_")
                        url = f"https://en.wikipedia.org/wiki/{safe_title}"
                        if url not in seen:
                            seen.add(url)
                            urls.append(url)

    return urls


class ContextNode:
    def __init__(
        self, tools: List[StructuredTool], model_name: str = None
    ):
        settings = get_settings()
        model = model_name or settings.ollama_model
        self.llm = ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=0
        )
        self.llm_with_tools = self.llm.bind_tools(tools)

    def __call__(self, state: AgentState):
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        SYS = SystemMessage(content=get_context_prompt(current_datetime))
        messages = [SYS] + state.messages

        response = self.llm_with_tools.invoke(messages)
        logger.info(f"ContextNode response: {response}")

        # Only extract URLs from the NEW response, not from history
        # The state.referenced_article_urls should already be reset at the start of each run
        # So we just accumulate URLs found in THIS run
        urls = _extract_wikipedia_urls([response])

        # Merge with URLs already found in this run (from previous context node calls in this run)
        current_urls = state.referenced_article_urls or []
        all_urls = list(dict.fromkeys(current_urls + urls))
        logger.info(f"Extracted URLs: {urls}. Total merged URLs: {all_urls}")

        return {"messages": [response], "referenced_article_urls": all_urls}
