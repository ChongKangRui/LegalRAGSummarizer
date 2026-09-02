from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

# Like `const router = express.Router()` + every path in here is prefixed with /query
router = APIRouter(prefix="/query", tags=["query"])


# ---- Request / response bodies. FastAPI validates + documents these for you ----
class QueryRequest(BaseModel):
    question: str
    top_k: int = 3


class QueryResponse(BaseModel):
    question: str
    answer: str
    top_k: int


# ---- A dependency: this is FastAPI's "per-route middleware".

async def require_api_key(x_api_key: str = Header(default=None)):
    if x_api_key != "secret-123":
        raise HTTPException(status_code=401, detail="bad or missing X-API-Key")
    return x_api_key  # whatever you return gets injected into the handler if it wants it


# Attach the dependency in the decorator when the handler doesn't need its return value.
# (Alternative: `async def run_query(body, key: str = Depends(require_api_key))` to use it.)
@router.post("/", response_model=QueryResponse, dependencies=[Depends(require_api_key)])
async def run_query(body: QueryRequest):
    # `body` is already parsed + validated against QueryRequest.
    return QueryResponse(
        question=body.question,
        answer=f"stub answer for: {body.question!r}",
        top_k=body.top_k,
    )

@router.get("/")
def hi():
    return "Hi there, this is a query"