import os
from pathlib import Path

class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.agent_http_endpoint = os.getenv("AGENT_HTTP_ENDPOINT")
        self.github_event_path = os.getenv("GITHUB_EVENT_PATH")
        self.github_event_name = os.getenv("GITHUB_EVENT_NAME")
        self.github_workspace = Path(os.getenv("GITHUB_WORKSPACE", "."))
        self.data_root = Path(os.getenv("DATA_ROOT", "data"))
        self.vector_store_path = Path(os.getenv("VECTOR_STORE_PATH", str(self.data_root / "code_embeddings.faiss")))
        self.vector_metadata_path = Path(os.getenv("VECTOR_METADATA_PATH", str(self.data_root / "code_embeddings.json")))
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.max_diff_tokens = int(os.getenv("MAX_DIFF_TOKENS", "2500"))
        self.vector_index_extensions = os.getenv(
            "VECTOR_INDEX_EXTENSIONS",
            "py,js,ts,tsx,java,go,cs,rb,swift,kt,sql,md,sh,yml,yaml",
        ).split(",")
        self.vector_index_max_files = int(os.getenv("VECTOR_INDEX_MAX_FILES", "200"))
        self.vector_index_max_chunks = int(os.getenv("VECTOR_INDEX_MAX_CHUNKS", "500"))
        self.vector_chunk_size = int(os.getenv("VECTOR_CHUNK_SIZE", "800"))
        self.vector_chunk_overlap = int(os.getenv("VECTOR_CHUNK_OVERLAP", "80"))

    def ensure_data_root(self):
        self.data_root.mkdir(parents=True, exist_ok=True)


default_settings = Settings()
