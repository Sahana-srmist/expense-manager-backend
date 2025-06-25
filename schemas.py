from pydantic import BaseModel, field_serializer
from datetime import date as DateType
from typing import Any

class ExpenseIn(BaseModel):
    reason: str
    amount: float
    date: str  # Let it be 'YYYY-MM-DD'



class ExpenseOut(BaseModel):
    sno: int
    username: str
    reason: str
    amount: float
    date: DateType  # Real `date` object

    
    @field_serializer("date", mode="plain")
    def serialize_date(value: DateType, info):
        return value.strftime("%d-%m-%Y")
