from __future__ import annotations
import os
import json
import base64
from typing import Dict, Any, List, Optional
import fitz
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment (.env)")    
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
    return f"""
너는 무역/물류 문서에서 필드를 추출하는 엔진이다.
문서 종류 : {doc_type}
규칙:
- 문서에 명시되지 않은 값은 null
- 절대 추측하지 말 것
- number 타입은 숫자로(가능하면)
- 스키마에 없는 키는 만들지 말 것
- 최종 출력은 JSON 1개만
아래 JSON Schema를 만족하는 JSON을 출력해라:
{json.dumps(schema, ensure_ascii=False)}
""".strip()

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