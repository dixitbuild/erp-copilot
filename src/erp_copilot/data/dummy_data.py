from datetime import date

from erp_copilot.data.schemas import PurchaseOrder, SalesOrder, WorkOrder

SALES_ORDERS = [
    SalesOrder(id="SO-1001", customer="Acme Corp", item="Steel Bracket", quantity=200,
               total_amount=4800.00, status="confirmed", order_date=date(2026, 9, 1)),
    SalesOrder(id="SO-1002", customer="Globex Ltd", item="Hydraulic Pump", quantity=15,
               total_amount=12750.50, status="shipped", order_date=date(2026, 9, 5)),
    SalesOrder(id="SO-1003", customer="Initech", item="Control Panel", quantity=40,
               total_amount=9200.00, status="draft", order_date=date(2026, 9, 12)),
    SalesOrder(id="SO-1004", customer="Umbrella Inc", item="Steel Bracket", quantity=500,
               total_amount=12000.00, status="delivered", order_date=date(2026, 8, 20)),
]

PURCHASE_ORDERS = [
    PurchaseOrder(id="PO-2001", supplier="MetalWorks Co", item="Steel Sheet", quantity=1000,
                  total_amount=15000.00, status="ordered", expected_date=date(2026, 10, 15)),
    PurchaseOrder(id="PO-2002", supplier="PumpTech", item="Pump Motor", quantity=30,
                  total_amount=8400.00, status="received", expected_date=date(2026, 9, 28)),
    PurchaseOrder(id="PO-2003", supplier="CircuitHub", item="PCB Board", quantity=250,
                  total_amount=6250.00, status="draft", expected_date=date(2026, 10, 30)),
]

WORK_ORDERS = [
    WorkOrder(id="WO-3001", product="Steel Bracket", quantity=200, assigned_to="Line A",
              status="in_progress", due_date=date(2026, 10, 10)),
    WorkOrder(id="WO-3002", product="Hydraulic Pump", quantity=15, assigned_to="Line B",
              status="completed", due_date=date(2026, 9, 25)),
    WorkOrder(id="WO-3003", product="Control Panel", quantity=40, assigned_to="Line C",
              status="planned", due_date=date(2026, 10, 20)),
]
