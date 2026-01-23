from __future__ import annotations
from typing import Any, Dict
from src.models.bill_of_lading import BillOfLading
from src.models.import_invoice import ImportInvoice

def map_bl_to_sap_payload(bl: BillOfLading) -> Dict[str, Any]:
    return {
        "BL_NO": bl.bl_no,
        "CARRIER": bl.carrier,
        "POL": bl.port_of_loading,
        "POD": bl.port_of_discharge,
        "SHIPMENT_DATE": bl.shipment_date,
        "PACKING_CONTAINERS": bl.packing.containers_of_pkgs if bl.packing else None,
        "PACKING_GROSS_WEIGHT": bl.packing.gross_weight if bl.packing else None,
        "PACKING_MEASUREMENT": bl.packing.measurement if bl.packing else None
    }

def map_import_invoice_to_sap_payload(inv: ImportInvoice) -> Dict[str, Any]:
    return {
        "INVOICE_NO": inv.invoice_no,
        "INVOICE_DATE": inv.invoice_date,
        "SELLER_NAME": inv.seller_name,
        "BUYER_NAME": inv.buyer_name,
        "CURRENCY": inv.currency,
        "TOTAL_AMOUNT": inv.total_amount,
        "INCOTERMS": inv.incoterms,
        "PAYMENT_TERMS": inv.payment_terms,
        "COUNTRY_OF_ORIGIN": inv.country_of_origin,
        "ITEMS": [
            {
                "LINE_NO": it.line_no,
                "MATERIAL_CODE": it.material_code,
                "TI_PART_NUMBER": getattr(it, "ti_part_number", None),
                "CUSTOMER_PO": it.customer_po,
                "DESCRIPTION": it.description,
                "HS_CODE": it.hs_code,
                "QTY": it.quantity,
                "UOM": it.uom,
                "UNIT_PRICE": it.unit_price,
                "AMOUNT": it.amount
            }

            for it in (inv.items or [])
        ]
    }