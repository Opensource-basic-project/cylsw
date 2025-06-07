from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, PlenaryBill
import requests
from bs4 import BeautifulSoup
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")
API_KEY = "145bca1e52594533863a5b12ec70dbc9"

# 이미지 키워드 매핑 JSON 로딩
with open("keyword_image_map.json", "r", encoding="utf-8") as f:
    keyword_map = json.load(f)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_link_url_from_api(bill_id: str, age=22, max_pages=5):
    url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"
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
            if 'nwbpacrgavhjryiph' in data and isinstance(data['nwbpacrgavhjryiph'], list):
                bills_data = data['nwbpacrgavhjryiph'][1].get('row', [])
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
        summary_div = soup.find("div", id="summaryContentDiv")
        if summary_div:
            return summary_div.get_text(separator="\n").strip()
    except Exception as e:
        print(f"크롤링 에러: {e}")
    return "제안이유 및 주요내용을 불러올 수 없습니다."

def find_matched_images(bill_name: str):
    matched = []
    for topic, config in keyword_map.items():
        keywords = config.get("keywords", [])
        for keyword in keywords:
            if keyword in bill_name:
                matched.extend(config.get("images", []))
                break  # 같은 주제에서 하나라도 일치하면 중복 방지
    return matched


@router.get("/plenary/{bill_id}")
def plenary_bills_detail(request: Request, bill_id: str, db: Session = Depends(get_db)):
    bill = db.query(PlenaryBill).filter(PlenaryBill.bill_id == bill_id).first()

    if bill:
        matched_images = find_matched_images(bill.bill_name)
        return templates.TemplateResponse("plenary_bills_detail.html", {
            "request": request,
            "bill": {
                "BILL_ID": bill.bill_id,
                "BILL_NO": bill.bill_no,
                "BILL_NAME": bill.bill_name,
                "PROPOSER": bill.proposer,
                "PROPOSE_DT": bill.propose_dt,
                "PROC_RESULT_CD": bill.proc_result_cd,
                "COMMITTEE_NM": bill.committee_nm,
            },
            "proposal_text": bill.proposal_text or "제안이유 및 주요내용을 등록 중입니다.",
            "link_url": bill.link_url,
            "review_info": {
                "so_committee_date": bill.so_committee_date or "",
                "so_committee_result": bill.so_committee_result or "",
                "law_committee_date": bill.law_committee_date or "",
                "law_committee_result": bill.law_committee_result or "",
                "plenary_vote_date": bill.plenary_vote_date or "",
                "plenary_vote_result": bill.plenary_vote_result or "",
            },
            "matched_images": matched_images
        })

    # fallback: API + 크롤링
    link_url, bill_data = get_link_url_from_api(bill_id)
    if not link_url:
        raise HTTPException(status_code=404, detail="해당 법안을 찾을 수 없습니다.")

    proposal_text = crawl_proposal_detail(link_url)
    bill_name = bill_data.get("BILL_NAME", "")
    matched_images = find_matched_images(bill_name)

    return templates.TemplateResponse("plenary_bills_detail.html", {
        "request": request,
        "bill": {
            "BILL_ID": bill_data.get("BILL_ID", ""),
            "BILL_NO": bill_data.get("BILL_NO", ""),
            "BILL_NAME": bill_name,
            "PROPOSER": bill_data.get("PROPOSER", ""),
            "PROPOSE_DT": bill_data.get("PROPOSE_DT", ""),
            "PROC_RESULT_CD": bill_data.get("PROC_RESULT_CD", ""),
            "COMMITTEE_NM": bill_data.get("COMMITTEE_NM", "")
        },
        "proposal_text": proposal_text,
        "link_url": link_url,
        "review_info": {
            "so_committee_date": "",
            "so_committee_result": "",
            "law_committee_date": "",
            "law_committee_result": "",
            "plenary_vote_date": "",
            "plenary_vote_result": "",
        },
        "matched_images": matched_images
    })
