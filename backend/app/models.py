
from pydantic import BaseModel, ConfigDict

from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    
class Strategy(CamelModel):
    value : str
    label : str
    
    
ALL_STRATEGIES: list[Strategy] = [
    Strategy(value="naive", label="Naive (truncate + stuff)"),
    Strategy(value="map_reduce", label="Map-reduce"),
    Strategy(value="refine", label="Refine"),
    Strategy(value="vector", label="Vector"),
    Strategy(value="hybrid", label="Hybrid"),
    Strategy(value="hybrid_rerank", label="Rerank"),
]
LARGE_ONLY_VALUES = {"naive", "map_reduce", "refine"}