from __future__ import annotations

import os
import json
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

UPSTREAM_VECTOR_URL = os.getenv("UPSTREAM_VECTOR_URL")


class SearchRequest(BaseModel):
    query: str
    rows: Optional[int] = Field(default=10)
    dataset_id: Optional[str] = Field(default=None)
    use_dense: Optional[bool] = Field(default=True, alias="use-dense")
    use_sparse: Optional[bool] = Field(default=True, alias="use-sparse")
    use_rerank: Optional[bool] = Field(default=True, alias="use_rerank")
    rrf_alpha: Optional[float] = 0.5

    # Pydantic v2 config
    model_config = ConfigDict(populate_by_name=True)


app = FastAPI(title="Vector Search Proxy")


@app.post("/search")
def search(req: SearchRequest):
    if not UPSTREAM_VECTOR_URL:
        raise HTTPException(status_code=500, detail="UPSTREAM_VECTOR_URL is not configured")

    headers = {"Content-Type": "application/json"}
    payload = {
        "query": req.query,
        "rows": req.rows,
        "dataset_id": req.dataset_id,
        "use-dense": req.use_dense,
        "use-sparse": req.use_sparse,
        "use_rerank": req.use_rerank,
        "rrf_alpha": req.rrf_alpha,
    }
    try:
        r = requests.post(UPSTREAM_VECTOR_URL, headers=headers, data=json.dumps(payload), timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Upstream vector search timeout")
    except requests.HTTPError as e:
        detail = None
        try:
            detail = r.json()
        except Exception:
            detail = r.text if 'r' in locals() else str(e)
        raise HTTPException(status_code=r.status_code if 'r' in locals() else 502, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
