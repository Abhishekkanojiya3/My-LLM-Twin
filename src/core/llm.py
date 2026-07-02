from openai import OpenAI
from langchain_openai import ChatOpenAI

from core.config import settings

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def build_groq_chat_model(model_name: str, temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name,
        api_key=settings.GROQ_API_KEY,
        openai_api_base=GROQ_BASE_URL,
        temperature=temperature,
    )


def build_groq_client() -> OpenAI:
    return OpenAI(api_key=settings.GROQ_API_KEY, base_url=GROQ_BASE_URL)
