"""Configuration management module."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# 加载项目根目录下的 .env（供 DEEPSEEK_API_KEY 等环境变量使用）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


class MongoDBConfig(BaseModel):
    """MongoDB configuration."""
    host: str = "localhost"
    port: int = 27017
    database: str = "resumerag"
    username: str = ""
    password: str = ""
    collection: str = "resumes"

    @property
    def connection_string(self) -> str:
        """Get MongoDB connection string."""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"mongodb://{self.host}:{self.port}"


class MilvusConfig(BaseModel):
    """Milvus configuration."""
    host: str = "localhost"
    port: int = 19530
    collection: str = "resume_embeddings"
    dimension: int = 1024
    index_type: str = "HNSW"
    metric_type: str = "COSINE"
    hnsw_m: int = 16
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 128


class ElasticsearchConfig(BaseModel):
    """Elasticsearch configuration."""
    hosts: str = "http://localhost:9200"
    index: str = "resumes"
    username: str = ""
    password: str = ""
    analyzer: str = "ik_max_word"
    search_analyzer: str = "ik_smart"


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    temperature: float = 0.3
    max_tokens: int = 2000
    streaming: bool = True


class EmbeddingConfig(BaseModel):
    """Embedding configuration."""
    model_name: str = "BAAI/bge-m3"
    device: str = "cpu"
    batch_size: int = 32


class RerankerConfig(BaseModel):
    """Reranker configuration."""
    enabled: bool = True
    model_name: str = "BAAI/bge-reranker-v2-m3"
    device: str = "cpu"
    top_k: int = 10


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""
    milvus_top_n: int = 100
    es_top_n: int = 100
    rrf_k: int = 60
    hyde_weight: float = 0.7
    final_top_k: int = 10


class ParsingConfig(BaseModel):
    """Parsing configuration."""
    ocr_enabled: bool = True
    ocr_engine: str = "paddleocr"
    confidence_threshold: float = 0.8
    max_text_length: int = 50000


class AppConfig(BaseModel):
    """Application configuration."""
    host: str = "0.0.0.0"
    port: int = 8501
    debug: bool = False
    log_level: str = "INFO"


class Settings(BaseSettings):
    """Application settings."""
    mongodb: MongoDBConfig = MongoDBConfig()
    milvus: MilvusConfig = MilvusConfig()
    elasticsearch: ElasticsearchConfig = ElasticsearchConfig()
    llm: LLMConfig = LLMConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    reranker: RerankerConfig = RerankerConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    parsing: ParsingConfig = ParsingConfig()
    app: AppConfig = AppConfig()

    @classmethod
    def load_from_yaml(cls, config_path: str | Path | None = None) -> "Settings":
        """Load settings from YAML config file."""
        if config_path is None:
            # Find config file
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()

        logger.info(f"Loading config from: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # Process environment variable substitutions
        processed_config = cls._process_env_vars(raw_config)
        #cls(**processed_config) 的意思是：把字典 processed_config 的键值对作为关键字参数，传递给 cls 的构造函数来创建实例。
        return cls(**processed_config)

    @staticmethod
    def _process_env_vars(config: dict[str, Any]) -> dict[str, Any]:
        """Process environment variable substitutions in config."""
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = Settings._process_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Parse ${ENV_VAR:default} format
                env_spec = value[2:-1]
                if ":" in env_spec:
                    env_var, default = env_spec.split(":", 1)
                    result[key] = os.environ.get(env_var, default)
                else:
                    result[key] = os.environ.get(env_spec, "")
            else:
                result[key] = value
        return result


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load_from_yaml()
    return _settings


def reload_settings(config_path: str | Path | None = None) -> Settings:
    """Reload settings from config file."""
    global _settings
    _settings = Settings.load_from_yaml(config_path)
    return _settings
