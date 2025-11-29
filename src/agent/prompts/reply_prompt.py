def get_reply_prompt(current_datetime: str) -> str:
    return f"""You are a helpful, polite, and concise assistant.
Current date and time: {current_datetime}

The user's input does not require external research.
Answer the user directly, engage in conversation, or handle their request (e.g., creative writing) using your internal knowledge.
"""
