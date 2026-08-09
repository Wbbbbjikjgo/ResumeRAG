"""MongoDB client singleton."""

from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from app.core.config import get_settings


class MongoDBClient:
    """MongoDB async client wrapper."""

    _instance: AsyncIOMotorClient | None = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """Get MongoDB client singleton."""
        if cls._instance is None:
            settings = get_settings()
            cls._instance = AsyncIOMotorClient(
                settings.mongodb.connection_string,
                maxPoolSize=50,
                minPoolSize=10
            )
            logger.info(f"MongoDB client initialized: {settings.mongodb.host}:{settings.mongodb.port}")
        return cls._instance

    @classmethod
    def get_database(cls):
        """Get database instance."""
        settings = get_settings()
        client = cls.get_client()
        return client[settings.mongodb.database]

    @classmethod
    def get_collection(cls, collection_name: str | None = None):
        """Get collection instance."""
        settings = get_settings()
        db = cls.get_database()
        return db[collection_name or settings.mongodb.collection]

    @classmethod
    async def health_check(cls) -> bool:
        """Check MongoDB connection health."""
        try:
            client = cls.get_client()
            await client.admin.command("ping")
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False

    @classmethod
    def close(cls):
        """Close MongoDB client."""
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
            logger.info("MongoDB client closed")
