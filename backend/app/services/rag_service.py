import logging

import openai

from app.config import settings
from app.services.chroma_service import chroma_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = (
    "あなたはHair Salon BLOOMのアシスタントです。"
    "以下の参考情報をもとに、お客様の質問に丁寧に回答してください。"
    "参考情報にない内容は推測せず、お電話でのお問い合わせを案内してください。"
    "\n\n電話番号: 03-6789-0123\n\n【参考情報】\n{context}"
)

FALLBACK_MESSAGE = (
    "申し訳ございません。現在応答できません。"
    "お手数ですが、お電話にてお問い合わせください。"
    "\n\U0001F4DE 03-6789-0123"
)


class RAGService:
    """Singleton service for Retrieval-Augmented Generation using OpenAI."""

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE,
        )

    async def generate_answer(
        self, user_message: str, history: list[dict] | None = None
    ) -> str:
        """Generate an answer by retrieving relevant FAQ context and calling OpenAI."""
        try:
            results = chroma_service.query(user_message, n_results=3)

            if results:
                context = "\n\n".join(result["document"] for result in results)
            else:
                context = "参考情報はありません。"

            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": user_message})

            response = await self._client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content

        except Exception:
            logger.exception("Error generating RAG answer for message: %s", user_message)
            return FALLBACK_MESSAGE


rag_service = RAGService()
