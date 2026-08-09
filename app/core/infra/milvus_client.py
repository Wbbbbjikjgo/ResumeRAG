"""Milvus client singleton."""

from pymilvus import (
    MilvusClient,
    CollectionSchema,
    FieldSchema,
    DataType,
)
from loguru import logger

from app.core.config import get_settings


class MilvusClientWrapper:
    """Milvus client wrapper."""

    _instance: MilvusClient | None = None

    @classmethod
    def get_client(cls) -> MilvusClient:
        """Get Milvus client singleton."""
        if cls._instance is None:
            settings = get_settings()
            cls._instance = MilvusClient(
                uri=f"http://{settings.milvus.host}:{settings.milvus.port}"
            )
            logger.info(f"Milvus client initialized: {settings.milvus.host}:{settings.milvus.port}")
        return cls._instance

    @classmethod
    async def health_check(cls) -> bool:
        """Check Milvus connection health."""
        try:
            client = cls.get_client()
            client.list_collections()
            return True
        except Exception as e:
            logger.error(f"Milvus health check failed: {e}")
            return False

    @classmethod
    def create_collection(cls, collection_name: str | None = None):
        """Create Milvus collection with schema."""
        settings = get_settings()
        client = cls.get_client()
        col_name = collection_name or settings.milvus.collection

        # Check if collection exists
        if client.has_collection(col_name):
            logger.info(f"Collection {col_name} already exists")
            return

        # Create schema
        schema = CollectionSchema()
        schema.add_field(field_name="pk", datatype=DataType.INT64, is_primary=True, auto_id=True)
        schema.add_field(field_name="resume_id", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=settings.milvus.dimension)
        schema.add_field(field_name="doc_type", datatype=DataType.VARCHAR, max_length=16)
        schema.add_field(field_name="section_name", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=4096)

        # Create collection
        client.create_collection(
            collection_name=col_name,
            schema=schema
        )

        # Create index
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type=settings.milvus.index_type,
            metric_type=settings.milvus.metric_type,
            params={
                "M": settings.milvus.hnsw_m,
                "efConstruction": settings.milvus.hnsw_ef_construction
            }
        )
        client.create_index(col_name, index_params)
        logger.info(f"Collection {col_name} created with HNSW index")

    @classmethod
    def close(cls):
        """Close Milvus client."""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
            logger.info("Milvus client closed")
