from datetime import date
from typing import Literal

from pydantic import BaseModel


class SalesOrder(BaseModel):
    id: str
    customer: str
    item: str
    quantity: int
    total_amount: float
    status: Literal["draft", "confirmed", "shipped", "delivered", "cancelled"]
    order_date: date


class PurchaseOrder(BaseModel):
    id: str
    supplier: str
    item: str
    quantity: int
    total_amount: float
    status: Literal["draft", "ordered", "received", "cancelled"]
    expected_date: date


class WorkOrder(BaseModel):
    id: str
    product: str
    quantity: int
    assigned_to: str
    status: Literal["planned", "in_progress", "completed", "on_hold"]
    due_date: date
