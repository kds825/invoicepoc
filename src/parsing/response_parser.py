from __future__ import annotations
from typing import Any, Dict
from src.models.bill_of_lading import BillOfLading
from src.models.import_invoice import ImportInvoice

def parse_bl(data: Dict[str, Any]) -> BillOfLading:
    return BillOfLading(**data)

def parse_import_invoice(data: Dict[str, Any]) -> ImportInvoice:
    return ImportInvoice(**data)