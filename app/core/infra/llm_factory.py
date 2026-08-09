"""LLM, Embedding, and Reranker factory."""

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from loguru import logger

from app.core.config import get_settings


class LLMFactory:
    """Factory for creating LLM, Embedding, and Reranker instances."""

    _llm_instance: ChatOpenAI | None = None
    _llm_nostream_instance: ChatOpenAI | None = None
    _embedding_instance: HuggingFaceEmbeddings | None = None
    _reranker_instance: object | None = None

    @classmethod
    def get_llm(cls, streaming: bool | None = None) -> ChatOpenAI:
        """Get LLM instance.

        Args:
            streaming: None 使用配置默认值；显式传 False 返回非流式实例
                       （DeepSeek 流式 + JSON 结构化输出会阻塞，解析类调用应使用非流式）
        """
        settings = get_settings()
        use_streaming = settings.llm.streaming if streaming is None else streaming
        if not use_streaming:
            if cls._llm_nostream_instance is None:
                cls._llm_nostream_instance = ChatOpenAI(
                    model=settings.llm.model,
                    api_key=settings.llm.api_key,
                    base_url=settings.llm.api_base,
                    temperature=settings.llm.temperature,
                    max_tokens=settings.llm.max_tokens,
                    streaming=False
                )
                logger.info(f"LLM (non-streaming) initialized: {settings.llm.model}")
            return cls._llm_nostream_instance

        if cls._llm_instance is None:
            cls._llm_instance = ChatOpenAI(
                model=settings.llm.model,
                api_key=settings.llm.api_key,
                base_url=settings.llm.api_base,
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens,
                streaming=settings.llm.streaming
            )
            logger.info(f"LLM initialized: {settings.llm.model}")
        return cls._llm_instance

    @classmethod
    def get_embedding(cls) -> HuggingFaceEmbeddings:
        """Get Embedding model instance."""
        if cls._embedding_instance is None:
            settings = get_settings()
            cls._embedding_instance = HuggingFaceEmbeddings(
                model_name=settings.embedding.model_name,
                model_kwargs={"device": settings.embedding.device},
                encode_kwargs={"normalize_embeddings": True}
            )
            logger.info(f"Embedding model initialized: {settings.embedding.model_name}")
        return cls._embedding_instance

    @classmethod
    def get_reranker(cls):
        """Get Reranker model instance."""
        if cls._reranker_instance is None:
            settings = get_settings()
            if not settings.reranker.enabled:
                logger.info("Reranker disabled in config")
                return None

            try:
                from FlagEmbedding import FlagReranker
                cls._reranker_instance = FlagReranker(
                    settings.reranker.model_name,
                    use_fp16=(settings.reranker.device == "cuda")
                )
                logger.info(f"Reranker initialized: {settings.reranker.model_name}")
            except ImportError:
                logger.warning("FlagEmbedding not installed, reranker disabled")
                return None
        return cls._reranker_instance

    @classmethod
    async def embed_documents(cls, texts: list[str]) -> list[list[float]]:
        """Embed documents using the embedding model."""
        embedding = cls.get_embedding()
        return await embedding.aembed_documents(texts)

    @classmethod
    async def embed_query(cls, text: str) -> list[float]:
        """Embed query using the embedding model."""
        embedding = cls.get_embedding()
        return await embedding.aembed_query(text)

    @classmethod
    def rerank(cls, query: str, documents: list[str]) -> list[float]:
        """Rerank documents against query."""
        reranker = cls.get_reranker()
        if reranker is None:
            return [0.0] * len(documents)
        
        pairs = [[query, doc] for doc in documents]
        scores = reranker.compute_score(pairs)
        if isinstance(scores, float):
            scores = [scores]
        return scores
