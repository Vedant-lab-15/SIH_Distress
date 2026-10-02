from __future__ import annotations

from typing import Sequence
import numpy as np


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class HFTextEmbedder:
    """Optional Hugging Face text embedding adapter.

    The core demo does not depend on downloading an external model. Instantiate
    this adapter only when sentence-transformers is installed and the model is
    available locally or network access is explicitly permitted.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Optional dependency 'sentence-transformers' is not installed. "
                "Use the structured/dynamic pipeline for the offline demo."
            ) from exc
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        return np.asarray(self.model.encode(list(texts), normalize_embeddings=True))
