from config import settings

from core.llm import build_groq_chat_model
from core.rag.prompt_templates import RerankingTemplate


class Reranker:
    @staticmethod
    def generate_response(
        query: str, passages: list[str], keep_top_k: int
    ) -> list[str]:
        reranking_template = RerankingTemplate()
        prompt = reranking_template.create_template(keep_top_k=keep_top_k)
        model = build_groq_chat_model(settings.GROQ_MODEL_ID)
        chain = prompt | model

        stripped_passages = [
            stripped_item for item in passages if (stripped_item := item.strip())
        ]
        passages = reranking_template.separator.join(stripped_passages)
        response = chain.invoke({"question": query, "passages": passages})
        response = response.content

        reranked_passages = response.strip().split(reranking_template.separator)
        reranked_stripped_passages = [
            stripped_item
            for item in reranked_passages
            if (stripped_item := item.strip())
        ]

        # If the model ignored the format instructions and returned commentary
        # instead of the passages themselves, fall back to the original order
        # rather than leaking that commentary into the generation context.
        if len(reranked_stripped_passages) < min(len(stripped_passages), keep_top_k):
            return stripped_passages[:keep_top_k]

        return reranked_stripped_passages[:keep_top_k]
