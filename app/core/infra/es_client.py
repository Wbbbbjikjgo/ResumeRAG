"""Elasticsearch client singleton."""

from elasticsearch import AsyncElasticsearch
from loguru import logger

from app.core.config import get_settings


class ElasticsearchClient:
    """Elasticsearch async client wrapper."""

    _instance: AsyncElasticsearch | None = None

    @classmethod
    def get_client(cls) -> AsyncElasticsearch:
        """Get Elasticsearch client singleton."""
        if cls._instance is None:
            settings = get_settings()
            hosts = settings.elasticsearch.hosts.split(",")
            
            # Build auth if provided
            auth = None
            if settings.elasticsearch.username and settings.elasticsearch.password:
                auth = (settings.elasticsearch.username, settings.elasticsearch.password)
            
            cls._instance = AsyncElasticsearch(
                hosts=hosts,
                basic_auth=auth,
                max_retries=3,
                retry_on_timeout=True
            )
            logger.info(f"Elasticsearch client initialized: {hosts}")
        return cls._instance

    @classmethod
    async def health_check(cls) -> bool:
        """Check Elasticsearch connection health."""
        try:
            client = cls.get_client()
            info = await client.info()
            return info["tagline"] == "You Know, for Search"
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return False

    @classmethod
    async def create_index(cls, index_name: str | None = None):
        """Create Elasticsearch index with mapping."""
        settings = get_settings()
        client = cls.get_client()
        idx_name = index_name or settings.elasticsearch.index

        # Check if index exists
        if await client.indices.exists(index=idx_name):
            logger.info(f"Index {idx_name} already exists")
            return

        # Create index with mapping
        mappings = {
            "mappings": {
                "properties": {
                    "resume_id": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "full_text": {
                        "type": "text",
                        "analyzer": settings.elasticsearch.analyzer,
                        "search_analyzer": settings.elasticsearch.search_analyzer
                    },
                    "skills": {"type": "keyword"},
                    "degree": {"type": "keyword"},
                    "years_of_experience": {"type": "integer"},
                    "upload_time": {"type": "date"}
                }
            }
        }

        await client.indices.create(index=idx_name, body=mappings)
        logger.info(f"Index {idx_name} created with ik analyzer")

    @classmethod
    async def close(cls):
        """Close Elasticsearch client."""
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
            logger.info("Elasticsearch client closed")
