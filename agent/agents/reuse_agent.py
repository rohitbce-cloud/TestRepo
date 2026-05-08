from ..services.openai_service import OpenAIService
from ..services.vector_store import VectorStore
from ..config import Settings
from ..utils.logging import get_logger

logger = get_logger("agent.reuse")


class ReuseAgent:
    def __init__(self, openai_service: OpenAIService, vector_store: VectorStore, settings: Settings):
        self.openai = openai_service
        self.vector_store = vector_store
        self.settings = settings

    def find_similar_code(self, diff_text: str, payload: dict) -> dict:
        if not diff_text:
            logger.info("No diff_text available for reuse search.")
            return {"similar_code": [], "recommendation": "No diff available."}

        if self.vector_store.is_empty():
            indexed = self.vector_store.index_directory(
                self.openai,
                extensions=self.settings.vector_index_extensions,
                max_files=self.settings.vector_index_max_files,
                max_chunks=self.settings.vector_index_max_chunks,
                chunk_size=self.settings.vector_chunk_size,
                overlap=self.settings.vector_chunk_overlap,
            )
            logger.info("Indexed %s code chunks into the reuse vector store.", indexed)

        embedding = self.openai.create_embeddings([diff_text])[0]
        results = self.vector_store.similarity_search(embedding, k=3)
        if not results:
            return {
                "similar_code": [],
                "recommendation": "Build new code; no close reuse candidate found.",
            }

        score = results[0]["score"]
        if score < 0.6:
            recommendation = (
                "Strong match found. Reuse or adapt the existing implementation to save time and maintain consistency. "
                "Confirm that the candidate matches the new intent before applying."
            )
        else:
            recommendation = (
                "A similar implementation exists, but the match is moderate. "
                "Review suggested code for reuse or modification, otherwise build a new solution if the fit is weak."
            )

        return {"similar_code": results, "recommendation": recommendation}
