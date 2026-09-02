from pydantic import BaseModel

class test(BaseModel):
    test_id: str
    section_id: int
    price: float