from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Simple demo catalog. Replace with your own catalog loader or DB.
CATALOG: List[Dict[str, Any]] = [
    {
        "id": "p1",
        "title": "Wireless Bluetooth Earbuds",
        "description": "Compact true wireless earbuds with noise reduction and 24h case battery.",
        "price": 49.99,
        "image_url": "https://example.com/images/earbuds.jpg",
    },
    {
        "id": "p2",
        "title": "Gaming Mechanical Keyboard",
        "description": "RGB mechanical keyboard with hot-swappable switches and compact layout.",
        "price": 89.0,
        "image_url": "https://example.com/images/keyboard.jpg",
    },
    {
        "id": "p3",
        "title": "Stainless Steel Water Bottle",
        "description": "Insulated bottle keeps drinks cold 24h and hot 12h. BPA-free.",
        "price": 19.5,
        "image_url": "https://example.com/images/bottle.jpg",
    },
    {
        "id": "p4",
        "title": "Dancing Image Mug",
        "description": "Heat-sensitive mug reveals dancing figures when hot liquid is poured.",
        "price": 14.99,
        "image_url": "https://example.com/images/mug.jpg",
    },
    {
        "id": "p5",
        "title": "Portable Bluetooth Speaker",
        "description": "Waterproof speaker with deep bass and 12-hour playtime.",
        "price": 39.99,
        "image_url": "https://example.com/images/speaker.jpg",
    },
]

# Build a sparse TF-IDF index for the catalog.
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception as e:  # pragma: no cover - environment without sklearn
    TfidfVectorizer = None
    cosine_similarity = None

try:
    # Optional dense encoder (if installed). Falls back gracefully if missing.
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _dense_model: Optional[SentenceTransformer] = None
except Exception:  # pragma: no cover
    SentenceTransformer = None
    np = None
    _dense_model = None

_sparse_vectorizer: Optional[TfidfVectorizer] = None
_sparse_matrix = None


def _catalog_texts() -> List[str]:
    return [f"{p['title']}\n{p['description']}" for p in CATALOG]


def _ensure_sparse_index():
    global _sparse_vectorizer, _sparse_matrix
    if TfidfVectorizer is None:
        return
    if _sparse_vectorizer is None:
        _sparse_vectorizer = TfidfVectorizer(max_features=20000)
        _sparse_matrix = _sparse_vectorizer.fit_transform(_catalog_texts())


def _ensure_dense_model():
    global _dense_model
    if SentenceTransformer is None:
        return
    if _dense_model is None:
        # Light, widely used model
        _dense_model = SentenceTransformer("all-MiniLM-L6-v2")


class SearchRequest(BaseModel):
    query: str
    rows: Optional[int] = Field(default=10)
    dataset_id: Optional[str] = Field(default=None)
    use_dense: Optional[bool] = Field(default=True, alias="use-dense")
    use_sparse: Optional[bool] = Field(default=True, alias="use-sparse")
    use_rerank: Optional[bool] = Field(default=True, alias="use_rerank")
    rrf_alpha: Optional[float] = 0.5

    class Config:
        allow_population_by_field_name = True


app = FastAPI(title="Vector Search Backend (Demo)")


def _sparse_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    if TfidfVectorizer is None or cosine_similarity is None:
        return []
    _ensure_sparse_index()
    if _sparse_vectorizer is None:
        return []
    q_vec = _sparse_vectorizer.transform([query])
    sims = cosine_similarity(q_vec, _sparse_matrix)[0]
    idxs = sims.argsort()[::-1][:top_k]
    results = []
    for rank, i in enumerate(idxs, start=1):
        results.append({
            "rank": rank,
            "score": float(sims[i]),
            "item": CATALOG[i],
        })
    return results


def _dense_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    if SentenceTransformer is None or np is None:
        return []
    _ensure_dense_model()
    if _dense_model is None:
        return []
    texts = _catalog_texts()
    q_emb = _dense_model.encode([query], normalize_embeddings=True)
    c_embs = _dense_model.encode(texts, normalize_embeddings=True)
    sims = (q_emb @ c_embs.T).ravel()
    idxs = sims.argsort()[::-1][:top_k]
    results = []
    for rank, i in enumerate(idxs, start=1):
        results.append({
            "rank": rank,
            "score": float(sims[i]),
            "item": CATALOG[i],
        })
    return results


def _rrf_combine(sparse: List[Dict[str, Any]], dense: List[Dict[str, Any]], alpha: float, top_k: int) -> List[Dict[str, Any]]:
    # Reciprocal Rank Fusion over item ids
    def to_rank_map(lst):
        return {d["item"]["id"]: i for i, d in enumerate(lst)}

    s_map = to_rank_map(sparse)
    d_map = to_rank_map(dense)
    ids = {**{k: True for k in s_map}, **{k: True for k in d_map}}
    fused = []
    for pid in ids.keys():
        s_rank = s_map.get(pid)
        d_rank = d_map.get(pid)
        score = 0.0
        if s_rank is not None:
            score += 1.0 / (alpha + (s_rank + 1))
        if d_rank is not None:
            score += 1.0 / (alpha + (d_rank + 1))
        # Retrieve the product object from either list
        prod = None
        for src in (sparse, dense):
            for e in src:
                if e["item"]["id"] == pid:
                    prod = e["item"]
                    break
            if prod:
                break
        fused.append({"id": pid, "score": score, "item": prod})
    fused.sort(key=lambda x: x["score"], reverse=True)
    # Reassign rank
    return [
        {"rank": i + 1, "score": float(e["score"]), "item": e["item"]}
        for i, e in enumerate(fused[:top_k])
    ]


@app.post("/search")
def search(req: SearchRequest):
    top_k = req.rows or 10
    sparse = _sparse_search(req.query, top_k) if req.use_sparse else []
    dense = _dense_search(req.query, top_k) if req.use_dense else []

    if req.use_rerank and sparse and dense:
        combined = _rrf_combine(sparse, dense, alpha=req.rrf_alpha or 0.5, top_k=top_k)
        results = combined
    elif dense:
        results = dense
    else:
        results = sparse

    # Shape a compact response
    return {
        "query": req.query,
        "count": len(results),
        "results": [
            {
                "rank": r["rank"],
                "score": r["score"],
                **r["item"],
            }
            for r in results
        ],
    }
