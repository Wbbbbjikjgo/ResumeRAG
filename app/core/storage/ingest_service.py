"""Ingest service: persist parsed resume into MongoDB, Milvus, Elasticsearch."""

from loguru import logger

from app.core.config import get_settings
from app.core.models import ResumeDocument
from app.core.infra.mongo_client import MongoDBClient
from app.core.infra.milvus_client import MilvusClientWrapper
from app.core.infra.es_client import ElasticsearchClient
from app.core.infra.llm_factory import LLMFactory


class IngestService:
    """Persist a parsed resume into all three stores."""

    @classmethod
    async def store(
        cls,
        doc: ResumeDocument,
        sections: list[dict]
    ) -> dict:
        """
        Store resume into MongoDB, Milvus, Elasticsearch.

        Args:
            doc: Parsed ResumeDocument
            sections: List of sections ({section_name, content})

        Returns:
            dict with per-store status: {"mongodb": bool, "milvus": bool, "elasticsearch": bool}
        """
        status = {"mongodb": False, "milvus": False, "elasticsearch": False}

        # 1. MongoDB - full structured document
        status["mongodb"] = await cls._store_mongodb(doc)

        # 2. Milvus - section embeddings
        status["milvus"] = await cls._store_milvus(doc, sections)

        # 3. Elasticsearch - keyword index
        status["elasticsearch"] = await cls._store_elasticsearch(doc)

        logger.info(f"Ingest status for {doc.resume_id}: {status}")
        return status

    @classmethod
    async def _store_mongodb(cls, doc: ResumeDocument) -> bool:
        """Store full document in MongoDB."""
        try:
            collection = MongoDBClient.get_collection()
            data = doc.model_dump(mode="json")
            await collection.replace_one(
                {"resume_id": doc.resume_id},
                data,
                upsert=True
            )
            logger.info(f"[MongoDB] Stored resume {doc.resume_id}")
            return True
        except Exception as e:
            logger.error(f"[MongoDB] Store failed: {e}")
            return False

    @classmethod
    async def _store_milvus(cls, doc: ResumeDocument, sections: list[dict]) -> bool:
        """Embed sections and store vectors in Milvus."""
        try:
            settings = get_settings()
            MilvusClientWrapper.create_collection()
            client = MilvusClientWrapper.get_client()

            # Build texts to embed: each section, fallback to full_text
            chunks = []
            for sec in sections:
                content = (sec.get("content") or "").strip()
                if content:
                    chunks.append({
                        "section_name": sec.get("section_name", "")[:60],
                        "text": content[:4000],
                        "doc_type": "section"
                    })
            if not chunks:
                chunks.append({
                    "section_name": "full_text",
                    "text": doc.full_text[:4000],
                    "doc_type": "full"
                })

            # Embed all chunks
            texts = [c["text"] for c in chunks]
            embeddings = await LLMFactory.embed_documents(texts)

            # Build insert rows matching collection schema
            rows = []
            for chunk, emb in zip(chunks, embeddings):
                rows.append({
                    "resume_id": doc.resume_id,
                    "embedding": emb,
                    "doc_type": chunk["doc_type"],
                    "section_name": chunk["section_name"],
                    "text": chunk["text"]
                })

            client.insert(collection_name=settings.milvus.collection, data=rows)
            logger.info(f"[Milvus] Inserted {len(rows)} vectors for {doc.resume_id}")
            return True
        except Exception as e:
            logger.error(f"[Milvus] Store failed: {e}")
            return False

    @classmethod
    async def _store_elasticsearch(cls, doc: ResumeDocument) -> bool:
        """Index resume in Elasticsearch for keyword search."""
        try:
            settings = get_settings()
            await ElasticsearchClient.create_index()
            client = ElasticsearchClient.get_client()

            # Highest degree for filtering
            degree = cls._highest_degree(doc)

            es_doc = {
                "resume_id": doc.resume_id,
                "name": doc.name or "",
                "full_text": doc.full_text,
                "skills": doc.skills,
                "degree": degree,
                "years_of_experience": int(doc.years_of_experience) if doc.years_of_experience else 0,
                "upload_time": doc.upload_time.isoformat()
            }

            await client.index(
                index=settings.elasticsearch.index,
                id=doc.resume_id,
                document=es_doc,
                refresh=True
            )
            logger.info(f"[ES] Indexed resume {doc.resume_id}")
            return True
        except Exception as e:
            logger.error(f"[ES] Store failed: {e}")
            return False

    @staticmethod
    def _highest_degree(doc: ResumeDocument) -> str:
        """Return the highest education degree from the resume."""
        hierarchy = ["大专", "本科", "硕士", "博士"]
        best = ""
        best_idx = -1
        for edu in doc.education:
            if edu.degree in hierarchy:
                idx = hierarchy.index(edu.degree)
                if idx > best_idx:
                    best_idx = idx
                    best = edu.degree
        return best
