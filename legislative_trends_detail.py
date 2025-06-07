from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, ForeignLawTrend
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

def crawl_meta_description(link_url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        res = requests.get(link_url, headers=headers, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        tag = soup.find("meta", attrs={"name": "description"})
        if tag and tag.get("content"):
            # ✅ 줄마다 공백 제거 후 줄바꿈 정리
            raw = tag["content"].replace("<br/>", "\n").replace("<br>", "\n")
            cleaned_lines = [line.strip() for line in raw.splitlines() if line.strip()]
            return "\n".join(cleaned_lines)
        return None
    except Exception as e:
        print(f"[크롤링 오류] {link_url}: {e}")
        return "상세 설명을 불러올 수 없습니다."

@router.get("/legislative-trends/{cn}")
def foreign_law_detail(request: Request, cn: str, db: Session = Depends(get_db)):
    law = db.query(ForeignLawTrend).filter(ForeignLawTrend.cn == cn).first()
    if not law:
        raise HTTPException(status_code=404, detail="해당 입법 정보를 찾을 수 없습니다.")
    
    description = law.proposal_text
    if not description and law.detail_url:
        description = crawl_meta_description(law.detail_url)

    return templates.TemplateResponse("legislative_trends_detail.html", {
        "request": request,
        "law": law,
        "description": description or "상세 설명이 등록되지 않았습니다.",
    })
