from __future__ import annotations
import os
import json
import base64
import re
from typing import Dict, Any, List, Optional, Tuple
import fitz
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE_URL")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment (.env)")
    if base_url:
        return OpenAI(api_key = api_key, base_url=base_url)    
    return OpenAI(api_key=api_key)

def pdf_to_base64_png_images(pdf_path: str, zoom: float = 2.0, max_pages: Optional[int] = None) -> List[str]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    images: List[str] = []
    try:
        total_pages = doc.page_count
        page_count = min(total_pages, max_pages) if max_pages else total_pages
        for i in range(page_count):
            page = doc.load_page(i)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            png_bytes = pix.tobytes("png")
            images.append(base64.b64encode(png_bytes).decode("utf-8"))
    finally:
        doc.close()
    return images

def build_prompt(doc_type: str, schema: Dict[str, Any]) -> str:
    dt = (doc_type or "").lower()

    common = """
너는 무역/물류 문서(이미지/PDF)에서 필요한 필드를 정확히 추출하는 엔진이다.

공통 규칙:
- 출력은 JSON 객체 1개만. (설명/문장 금지)
- 아래 JSON Schema에 정확히 맞춰라. (스키마에 없는 키 생성 금지)
- 문서에 근거가 없으면 null.
- 절대 임의 추정/보완하지 말 것.
- 숫자 필드는 숫자로 출력(가능하면).
- 날짜는 가능하면 ISO-8601(YYYY-MM-DD)로 정규화한다.
""".strip()

    if "bill of lading" in dt or "b/l" in dt or dt.strip() == "bl":
        rules = """
[BL 전용 규칙 - 회사 룰 반영]

1) 운송사(carrier)
- DHL/FEDEX/UPS 등 로고 또는 상단 큰 글씨 회사명을 우선.

2) BL 번호(bl_no)
- 다음 표현을 우선 탐색:
  · "B/L No", "BL NO"
  · "Waybill", "WAYBILL NUMBER"
  · "Air Waybill", "AWB"
  · "Tracking Number"
- 바코드 근처(바로 위/아래)의 번호도 BL 번호 후보.
- "Invoice No"와 절대 혼동하지 말 것.
- bl_no는 숫자만 출력한다.
- "WAYBILL", "AWB", "AIR WAYBILL", "B/L", "BL", "NO" 등의 텍스트와 공백은 제거하고, 숫자만 이어붙여라.

3) 선적지/입항지(port_of_loading / port_of_discharge)  ★중요: Full 코드 그대로!
- 문서에 "SG-SIN-ASC", "KR-PUS-DGS" 같은 형태가 보이면 (국가2자리-도시3자리-기타코드)
  이를 선적/입항 코드로 간주한다.
- 이런 코드가 2개 이상 함께 보이면:
  · 첫 번째(보통 왼쪽/먼저 나오는 것) = port_of_loading
  · 두 번째(보통 오른쪽/다음에 나오는 것) = port_of_discharge
- 이 값은 절대 축약/정규화하지 말고, 문서에 인쇄된 원문 그대로 저장하라.
  예) "SG-SIN-ASC"는 "SGSIN"으로 바꾸지 말고 그대로 "SG-SIN-ASC"로 출력.

(라벨 기반 보조 규칙)
- "Port of Loading / Port of Discharge"
- "Place of Receipt / Place of Delivery"
- "Airport of Departure / Destination" 등이 명시되어 있으면 해당 값을 사용하되,
  Full 코드(예: SG-SIN-ASC)가 존재하면 Full 코드를 우선한다.

4) 출하일자(shipment_date)  ★회사 룰: Reproduction date = 출하일
- 상단에 "YYYY-MM-DD (Reproduction)" 형태가 있으면, 그 날짜를 shipment_date로 사용하라.
- "Data" 날짜가 함께 있더라도 회사 룰에 따라 shipment_date는 Reproduction 날짜를 우선한다.
- onboard_date, issue_date는 문서에 명시적으로 해당 라벨이 있을 때만 채우고, 애매하면 null.

5) PACKING 정보(packing)
- gross_weight: KG/KGS/LB/LBS 포함 중량
- package_count: Pieces/Packages/Pkgs 등의 수량(숫자)
- measurement: CBM/Measurement
- 숫자형으로 확실하면 gross_weight_kg / measurement_cbm도 채워라.
""".strip()
    else:
        rules = """
[Commercial Invoice / Tax Invoice 전용 규칙]

- 출력은 스키마 키만 사용.
- invoice_no: "INVOICE NO/Invoice number/INV NO" 우선. Waybill/BL/AWB와 혼동 금지.
- invoice_date: "INVOICE DATE/DATE" 우선. ISO-8601.

[items 추출 공통]
- items는 표(Item table) 기준으로 라인별 추출.

[material_code (중요, 강제)]
- material_code는 반드시 'Customer part number' 라벨에 해당하는 값만 사용.
- material_code는 숫자(digits)만 허용한다. (0-9 이외 문자가 하나라도 포함되면 material_code로 채택하지 말고 null 처리 후, Customer part number 영역에서 숫자값을 다시 찾아라.)
- 'TI part number', 'Order number', 'Delivery number' 칸의 값은 material_code가 아니다. 절대 사용 금지.
- 예: LM2930BDRQT 같은 영문/숫자 혼합 코드는 material_code가 아니라 TI part number이고, 이 코드에선 가져오지 말 것
- (중요) TI part number 문자열의 일부를 잘라 숫자만 추출하는 행위도 금지. (예: LM2930... -> 2930 금지)

- customer_po: "Customer P.O." / "PO" / "P.O." 우선
- quantity: "Quantity (EA)" / "Qty" 우선
- uom: EA/PCS 등
- hs_code, unit_price, amount도 가능한 만큼 채워라.
""".strip()

    return (
        common
        + "\n\n문서 종류: " + str(doc_type) + "\n\n"
        + rules
        + "\n\n아래 JSON Schema를 만족하는 JSON 객체 1개만 출력해라:\n"
        + json.dumps(schema, ensure_ascii=False)
    )

    
def extract_json_from_pdf(pdf_path: str, schema: Dict[str, Any], doc_type: str, model: Optional[str] = None, max_pages: Optional[int] = None) -> Dict[str, Any]:
    client = get_client()
    chosen_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    images_b64 = pdf_to_base64_png_images(pdf_path, max_pages=max_pages)
    if not images_b64:
        return {}

    prompt = build_prompt(doc_type=doc_type, schema=schema)
    content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    for b64 in images_b64:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
    
    resp = client.chat.completions.create(
        model=chosen_model,
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
        temperature=0
    )
    
    raw = resp.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_error": "JSONDecodeError", "_raw": raw}