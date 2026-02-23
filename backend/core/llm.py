import anthropic

from backend.config import settings


def get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def chat_completion(
    messages: list[dict],
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Send a chat completion request to Claude."""
    client = get_client()
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    response = await client.messages.create(**kwargs)
    return response.content[0].text


async def chat_completion_with_tools(
    messages: list[dict],
    tools: list[dict],
    system: str = "",
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> anthropic.types.Message:
    """Send a chat completion with tool use."""
    client = get_client()
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "tools": tools,
    }
    if system:
        kwargs["system"] = system
    return await client.messages.create(**kwargs)
