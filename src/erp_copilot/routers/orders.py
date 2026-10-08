from fastapi import APIRouter, HTTPException

from erp_copilot.dummy_data import PURCHASE_ORDERS, SALES_ORDERS, WORK_ORDERS
from erp_copilot.schemas import PurchaseOrder, SalesOrder, WorkOrder

router = APIRouter(tags=["orders"])


def _filter_status[T](orders: list[T], status: str | None) -> list[T]:
    return [o for o in orders if o.status == status] if status else orders


def _get_or_404[T](orders: list[T], order_id: str) -> T:
    for order in orders:
        if order.id == order_id:
            return order
    raise HTTPException(status_code=404, detail=f"Order {order_id} not found")


@router.get("/sales-orders", response_model=list[SalesOrder])
async def list_sales_orders(status: str | None = None):
    return _filter_status(SALES_ORDERS, status)


@router.get("/sales-orders/{order_id}", response_model=SalesOrder)
async def get_sales_order(order_id: str):
    return _get_or_404(SALES_ORDERS, order_id)


@router.get("/purchase-orders", response_model=list[PurchaseOrder])
async def list_purchase_orders(status: str | None = None):
    return _filter_status(PURCHASE_ORDERS, status)


@router.get("/purchase-orders/{order_id}", response_model=PurchaseOrder)
async def get_purchase_order(order_id: str):
    return _get_or_404(PURCHASE_ORDERS, order_id)


@router.get("/work-orders", response_model=list[WorkOrder])
async def list_work_orders(status: str | None = None):
    return _filter_status(WORK_ORDERS, status)


@router.get("/work-orders/{order_id}", response_model=WorkOrder)
async def get_work_order(order_id: str):
    return _get_or_404(WORK_ORDERS, order_id)
