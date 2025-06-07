from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, ForeignLawExample
import requests
from bs4 import BeautifulSoup

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def crawl_example_description(link_url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(link_url, headers=headers, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        content_div = soup.select_one("#de_cont")
        return content_div.get_text("\n", strip=True) if content_div else None
    except Exception as e:
        print(f"[크롤링 오류] {link_url}: {e}")
        return "상세 설명을 불러올 수 없습니다."

@router.get("/legislative-example/{cn}")
def foreign_law_example_detail(request: Request, cn: str, db: Session = Depends(get_db)):
    law = db.query(ForeignLawExample).filter(ForeignLawExample.cn == cn).first()
    if not law:
        raise HTTPException(status_code=404, detail="해당 입법례 정보를 찾을 수 없습니다.")

    description = law.proposal_text
    if not description and law.detail_url:
        description = crawl_example_description(law.detail_url)

    return templates.TemplateResponse("legislative_example_detail.html", {
        "request": request,
        "law": law,
        "description": description or "상세 설명이 등록되지 않았습니다.",
    })