import json
import os
from typing import List, Tuple
import faiss
import numpy as np
from ..config import settings

class FaissIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.meta: List[dict] = []

    def add(self, vectors: np.ndarray, metas: List[dict]) -> None:
        assert vectors.shape[0] == len(metas)
        if vectors.size == 0: return
        self.index.add(vectors.astype("float32"))
        self.meta.extend(metas)

    def search(self, vectors: np.ndarray, top_k: int) -> Tuple[np.ndarray, List[List[dict]]]:
        if self.index.ntotal == 0:
            empty_D = np.zeros((vectors.shape[0], 0), dtype="float32")
            return empty_D, [[] for _ in range(vectors.shape[0])]
        D, I = self.index.search(vectors.astype("float32"), top_k)
        metas: List[List[dict]] = []
        for row in I:
            row_metas: List[dict] = []
            for i in row:
                if i < 0 or i >= len(self.meta):
                    continue
                row_metas.append(self.meta[i])
            metas.append(row_metas)
        return D, metas

    def save(self) -> None:
        faiss.write_index(self.index, settings.FAISS_INDEX_PATH)
        with open(settings.FAISS_META_PATH, "w", encoding="utf-8") as f:
            for m in self.meta:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, dim: int) -> "FaissIndex":
        if os.path.exists(settings.FAISS_INDEX_PATH):
            idx = cls(dim)
            idx.index = faiss.read_index(settings.FAISS_INDEX_PATH)
            if os.path.exists(settings.FAISS_META_PATH):
                with open(settings.FAISS_META_PATH, "r", encoding="utf-8") as f:
                    idx.meta = [json.loads(l) for l in f]
            return idx
        return cls(dim)
