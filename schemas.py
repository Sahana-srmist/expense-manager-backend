from pydantic import BaseModel, field_serializer
from datetime import date as DateType
from typing import Any

class ExpenseIn(BaseModel):
    username: str
    reason: str
    amount: float
    date: str  # User inputs as DD-MM-YYYY

class ExpenseOut(BaseModel):
    sno: int
    username: str
    reason: str
    amount: float
    date: DateType  # Real `date` object

    
    @field_serializer("date", mode="plain")
    def serialize_date(value: DateType, info):
        return value.strftime("%d-%m-%Y")
