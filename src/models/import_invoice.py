from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional

class ImportInvoiceItem(BaseModel):
    line_no: Optional[int] = None
    description: Optional[str] = None
    material_code: Optional[str] = None
    customer_po: Optional[str] = None
    hs_code: Optional[str] = None
    quantity: Optional[float] = None
    uom: Optional[str] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None

class ImportInvoice(BaseModel):
    invoice_no: Optional[str] = None
    invoice_date: Optional[str] = None
    seller_name: Optional[str] = None
    buyer_name: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    incoterms: Optional[str] = None
    payment_terms: Optional[str] = None
    country_of_origin: Optional[str] = None
    items: List[ImportInvoiceItem] = []