import json
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False


class VectorStore:
    def __init__(self, settings):
        self.settings = settings
        self.index_path = Path(settings.vector_store_path)
        self.metadata_path = Path(settings.vector_metadata_path)
        self.root_path = Path(settings.github_workspace)
        self.embeddings: list[list[float]] = []
        self.metadata: list[dict[str, Any]] = []
        self.index = None
        self._load()

    def _load(self):
        if self.metadata_path.exists():
            with open(self.metadata_path, "r", encoding="utf-8") as fh:
                self.metadata = json.load(fh)
        if FAISS_AVAILABLE and self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))

    def _save_metadata(self):
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_path, "w", encoding="utf-8") as fh:
            json.dump(self.metadata, fh, indent=2)

    def is_empty(self) -> bool:
        return len(self.metadata) == 0

    def upsert(self, items: list[dict[str, Any]], vectors: list[list[float]]):
        self.metadata.extend(items)
        if FAISS_AVAILABLE:
            if self.index is None:
                dim = len(vectors[0])
                self.index = faiss.IndexFlatL2(dim)
            self.index.add(np.array(vectors, dtype="float32"))
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))
        else:
            self.embeddings.extend(vectors)
        self._save_metadata()

    def similarity_search(self, query_vector: list[float], k: int = 3) -> list[dict[str, Any]]:
        if FAISS_AVAILABLE and self.index is not None:
            distances, indices = self.index.search(np.array([query_vector], dtype="float32"), k)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.metadata):
                    results.append({"score": float(dist), **self.metadata[idx]})
            return results

        if not self.embeddings:
            return []
        matrix = np.array(self.embeddings, dtype="float32")
        query = np.array(query_vector, dtype="float32")
        scores = np.linalg.norm(matrix - query, axis=1)
        best = scores.argsort()[:k]
        return [
            {"score": float(scores[i]), **self.metadata[i]}
            for i in best
            if i < len(self.metadata)
        ]

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        text = text.strip()
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def index_directory(
        self,
        openai_service: Any,
        extensions: list[str] | None = None,
        max_files: int | None = None,
        max_chunks: int | None = None,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> int:
        extensions = extensions or self.settings.vector_index_extensions
        max_files = max_files or self.settings.vector_index_max_files
        max_chunks = max_chunks or self.settings.vector_index_max_chunks
        chunk_size = chunk_size or self.settings.vector_chunk_size
        overlap = overlap or self.settings.vector_chunk_overlap

        file_paths = [
            path
            for path in sorted(self.root_path.rglob("*"))
            if path.is_file()
            and path.suffix.lstrip(".") in extensions
            and ".git" not in str(path.parts)
            and "data" not in str(path.parts)
        ]

        selected_files = file_paths[:max_files]
        embeddings_inputs = []
        metadata_items = []

        for path in selected_files:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            chunks = self._chunk_text(text, chunk_size, overlap)
            for idx, chunk in enumerate(chunks):
                metadata_items.append(
                    {
                        "path": str(path.relative_to(self.root_path)),
                        "chunk_index": idx,
                        "content": chunk,
                    }
                )
                embeddings_inputs.append(chunk)
                if len(embeddings_inputs) >= max_chunks:
                    break
            if len(embeddings_inputs) >= max_chunks:
                break

        if not embeddings_inputs:
            return 0

        vectors = openai_service.create_embeddings(embeddings_inputs)
        self.upsert(metadata_items, vectors)
        return len(embeddings_inputs)
