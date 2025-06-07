from db import SessionLocal, LegislationNotice, EndedLegislationNotice
import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def crawl_proposal_detail(link_url: str):
    try:
        response = requests.get(link_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.find_all("div", class_="item"):
            h4 = item.find("h4")
            if h4 and "제안이유 및 주요내용" in h4.text:
                desc_div = item.find("div", class_="desc")
                if desc_div:
                    return re.sub(r'^[ \t]+', '', desc_div.get_text(separator="\n").strip(), flags=re.MULTILINE)
    except Exception as e:
        print(f"[에러] {link_url} 처리 중 오류: {e}")
    return None

def update_table_proposal_text(table_class, label: str):
    db = SessionLocal()
    try:
        targets = db.query(table_class).filter(
            (table_class.proposal_text == None) |
            (table_class.proposal_text == "")
        ).all()

        for bill in targets:
            if bill.link_url:
                print(f"[{label}] 📄 {bill.bill_name} - 크롤링 시도 중...")
                detail = crawl_proposal_detail(bill.link_url)
                if not detail:
                    print(f"[{label}] ❌ 1차 실패, 재시도 중...")
                    time.sleep(1)
                    detail = crawl_proposal_detail(bill.link_url)
                if detail:
                    bill.proposal_text = detail
                else:
                    print(f"[{label}] 🚫 크롤링 실패: {bill.link_url}")
                time.sleep(1)  # 요청 간 딜레이
        db.commit()
        print(f"[{label}] ✅ 제안이유 및 주요내용 DB 갱신 완료")
    finally:
        db.close()

if __name__ == "__main__":
    update_table_proposal_text(LegislationNotice, "진행중")
    update_table_proposal_text(EndedLegislationNotice, "종료")
