import requests
from db import SessionLocal, ForeignLawExample
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def crawl_example_description(link_url: str):
    try:
        response = requests.get(link_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.select_one("#de_cont")
        if content_div:
            text = content_div.get_text("\n", strip=True)
            return text
    except Exception as e:
        print(f"[에러] {link_url} 크롤링 실패: {e}")
    return None

def update_foreign_example_descriptions():
    db = SessionLocal()
    try:
        targets = db.query(ForeignLawExample).filter(
            (ForeignLawExample.issue_date != None) &
            ((ForeignLawExample.asc_name == None) | (ForeignLawExample.asc_name == "")) |
            ((ForeignLawExample.detail_url != None) & ((ForeignLawExample.proposal_text == None) | (ForeignLawExample.proposal_text == "")))
        ).all()

        for law in targets:
            if law.detail_url:
                print(f"[입법례] 📄 {law.title} - 설명 크롤링 중...")
                detail = crawl_example_description(law.detail_url)
                if not detail:
                    print(f"[입법례] ❌ 재시도...")
                    time.sleep(1)
                    detail = crawl_example_description(law.detail_url)
                if detail:
                    law.proposal_text = detail
                else:
                    print(f"[입법례] 🚫 실패: {law.detail_url}")
                time.sleep(1)
        db.commit()
        print("[입법례] ✅ 설명 갱신 완료")
    finally:
        db.close()

if __name__ == "__main__":
    update_foreign_example_descriptions()
