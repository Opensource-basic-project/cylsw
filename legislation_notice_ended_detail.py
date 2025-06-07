from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, EndedLegislationNotice
import requests
from bs4 import BeautifulSoup
import re

router = APIRouter()
templates = Jinja2Templates(directory="templates")
API_KEY = "145bca1e52594533863a5b12ec70dbc9"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# fallback용 API 조회
def get_link_url_from_api(bill_id: str, age=22, max_pages=5):
    url = "https://open.assembly.go.kr/portal/openapi/nohgwtzsamojdozky"
    for pIndex in range(1, max_pages + 1):
        params = {
            'KEY': API_KEY,
            'Type': 'json',
            'AGE': age,
            'pSize': 100,
            'pIndex': pIndex,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if 'nohgwtzsamojdozky' in data and isinstance(data['nohgwtzsamojdozky'], list):
                bills_data = data['nohgwtzsamojdozky'][1].get('row', [])
                for bill in bills_data:
                    if str(bill.get('BILL_ID')).strip() == str(bill_id).strip():
                        return bill.get('LINK_URL'), bill
        except Exception as e:
            print(f"API 호출 에러: {e}")
            break
    return None, None

def crawl_proposal_detail(link_url: str):
    try:
        response = requests.get(link_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all("div", class_="item"):
            h4 = item.find("h4")
            if h4 and "제안이유 및 주요내용" in h4.text:
                desc_div = item.find("div", class_="desc")
                if desc_div:
                    return re.sub(r'^[ \t]+', '', desc_div.get_text(separator="\n").strip(), flags=re.MULTILINE)
    except Exception as e:
        print(f"크롤링 에러: {e}")
    return "제안이유 및 주요내용을 불러올 수 없습니다."

@router.get("/legislation_ended/{bill_id}")
def legislation_ended_detail(request: Request, bill_id: str, db: Session = Depends(get_db)):
    bill = db.query(EndedLegislationNotice).filter(EndedLegislationNotice.bill_id == bill_id).first()

    if bill:
        return templates.TemplateResponse("legislation_notice_ended_detail.html", {
            "request": request,
            "bill": {
                "BILL_ID": bill.bill_id,
                "BILL_NAME": bill.bill_name,
                "PROPOSER": bill.proposer,
                "CURR_COMMITTEE": bill.curr_committee,
                "ANNOUNCE_DT": bill.announce_dt,
            },
            "proposal_text": bill.proposal_text or "제안이유 및 주요내용을 등록 중입니다.",
            "link_url": bill.link_url
        })

    # fallback
    link_url, bill_data = get_link_url_from_api(bill_id)
    if not link_url:
        raise HTTPException(status_code=404, detail="해당 법안을 찾을 수 없습니다.")

    proposal_text = crawl_proposal_detail(link_url)
    return templates.TemplateResponse("legislation_notice_ended_detail.html", {
        "request": request,
        "bill": bill_data,
        "proposal_text": proposal_text,
        "link_url": link_url
    })

"""from fastapi import APIRouter, Request, HTTPException 
from fastapi.templating import Jinja2Templates
from fastapi import Depends
from sqlalchemy.orm import Session
from db import SessionLocal, EndedLegislationNotice

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/legislation_ended/{bill_id}")
def legislation_ended_detail(request: Request, bill_id: str, db: Session = Depends(get_db)):
    bill = db.query(EndedLegislationNotice).filter(EndedLegislationNotice.bill_id == bill_id).first()

    if not bill:
        raise HTTPException(status_code=404, detail="해당 bill_id에 대한 데이터를 찾을 수 없습니다.")

    return templates.TemplateResponse("legislation_notice_ended_detail.html", {
        "request": request,
        "bill": {
            "BILL_NAME": bill.bill_name,
            "PROPOSER": bill.proposer,
            "BILL_ID": bill.bill_id,
            "NOTI_ED_DT": bill.noti_ed_dt,
            "LINK_URL": bill.link_url,
            "CURR_COMMITTEE": bill.curr_committee,
            "ANNOUNCE_DT": bill.announce_dt,
        },
        "proposal_text": bill.proposal_text,
        "link_url": bill.link_url,
    })"""
