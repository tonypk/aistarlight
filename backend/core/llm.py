from openai import AsyncOpenAI

from backend.config import settings


def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def chat_completion(
    messages: list[dict],
    system: str = "",
    model: str = "",
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> str:
    """Send a chat completion request to OpenAI."""
    client = get_client()
    model = model or settings.openai_model

    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    response = await client.chat.completions.create(
        model=model,
        messages=full_messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


async def chat_completion_with_tools(
    messages: list[dict],
    tools: list[dict],
    system: str = "",
    model: str = "",
    max_tokens: int = 4096,
) -> dict:
    """Send a chat completion with tool use."""
    client = get_client()
    model = model or settings.openai_model

    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    # Convert tools from Anthropic format to OpenAI format
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {}),
            },
        })

    response = await client.chat.completions.create(
        model=model,
        messages=full_messages,
        tools=openai_tools if openai_tools else None,
        max_tokens=max_tokens,
    )
    return response
