from __future__ import annotations
from pydantic import BaseModel
from typing import Optional

class PackingInfo(BaseModel):
    containers_of_pkgs: Optional[str] = None
    gross_weight: Optional[str] = None
    measurement: Optional[str] = None
    package_count: Optional[float] = None
    container_count: Optional[float] = None
    gross_weight_kg: Optional[float] = None
    measurement_cbm: Optional[float] = None

class BillOfLading(BaseModel):
    carrier: Optional[str] = None
    bl_no: Optional[str] = None
    bl_type: Optional[str] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    packing: Optional[PackingInfo] = None
    onboard_date: Optional[str] = None
    issue_date: Optional[str] = None
    shipment_date: Optional[str] = None