
import json

from fastapi import APIRouter

from app.models import CamelModel

from app.retrieval.vector_store import doc_chunk_counts, get_chunks


from app.config import EVAL_RESULT_PATH, GOLDEN_SET_PATH



# Like `const router = express.Router()` + every path in here is prefixed with /query
router = APIRouter(prefix="/eval_dashboard", tags=["eval_dashboard"])


class Metric(CamelModel):
    #model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    stage: str
    precision_at_k: float
    recall_at_k: float
    mrr: float
    citation_accuracy: float

class EvalRun(CamelModel): 
    #model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    run_at: str
    k: int
    goldenSetSize: int
    metrics: list[Metric]

@router.get("", response_model=EvalRun)
async def get_eval_dashboard():
    data = json.loads(EVAL_RESULT_PATH.read_text())
    golden_set = json.loads(GOLDEN_SET_PATH.read_text())

    type = ["vector", "hybrid", "hybrid_rerank"]
    metrics = [Metric(stage=t, 
                      precision_at_k=round(data[t]["means"]["mean_precision"], 2),
        recall_at_k=round(data[t]["means"]["mean_recall"], 2),
        mrr=round(data[t]["means"]["mean_rr"], 2),
        citation_accuracy=round(data[t]["means"]["mean_cc"], 2)
                      )  for t in type]
    


    return EvalRun(run_at=data["Date"], k=data["k"], goldenSetSize=len(golden_set), metrics=metrics)