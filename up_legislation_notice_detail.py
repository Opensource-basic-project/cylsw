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

        # 제안이유 및 주요내용
        proposal_text = None
        for item in soup.find_all("div", class_="item"):
            h4 = item.find("h4")
            if h4 and "제안이유 및 주요내용" in h4.text:
                desc_div = item.find("div", class_="desc")
                if desc_div:
                    proposal_text = re.sub(r'^[ \t]+', '', desc_div.get_text(separator="\n").strip(), flags=re.MULTILINE)
                    break

        notice_period = None
        tbody = soup.find("tbody")
        rows = tbody.find_all("tr") if tbody else []

        if rows:
            tds = rows[0].find_all("td")
            if len(tds) >= 6:
                notice_period = tds[5].get_text(strip=True)  # ❌ 7번째 (index 6)를 사용

        return proposal_text, notice_period

    except Exception as e:
        print(f"[에러] {link_url} 처리 중 오류: {e}")
    return None, None

def update_table_proposal_text(table_class, label: str):
    db = SessionLocal()
    try:
        targets = db.query(table_class).filter(table_class.link_url != None).all()

        for bill in targets:
            print(f"[{label}] 📄 {bill.bill_name} - 크롤링 시도 중...")
            detail, notice_period = crawl_proposal_detail(bill.link_url)

            if not detail and not notice_period:
                print(f"[{label}] 🚫 크롤링 실패: {bill.link_url}")
                continue

            changed = False

            if detail and bill.proposal_text != detail:
                bill.proposal_text = detail
                changed = True

            if notice_period and getattr(bill, "notice_period", None) != notice_period:
                bill.notice_period = notice_period
                changed = True

            if changed:
                print(f"[업데이트] ✏️ {bill.bill_name} - 변경 사항 반영됨")
            else:
                print(f"[유지] ⏩ {bill.bill_name} - 내용 동일, 덮어쓰기 생략")

            time.sleep(1)

        db.commit()
        print(f"[{label}] ✅ DB 갱신 완료")

    finally:
        db.close()

if __name__ == "__main__":
    update_table_proposal_text(LegislationNotice, "진행중")
    update_table_proposal_text(EndedLegislationNotice, "종료")
