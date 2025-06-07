from db import SessionLocal, ForeignLawTrend
import requests
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def crawl_foreign_description(link_url: str):
    try:
        response = requests.get(link_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and "content" in meta_tag.attrs:
            return meta_tag["content"].replace("<br/>", "<br>").strip()
    except Exception as e:
        print(f"[에러] {link_url} 크롤링 실패: {e}")
    return None

def update_foreign_law_descriptions():
    db = SessionLocal()
    try:
        targets = db.query(ForeignLawTrend).filter(
            (ForeignLawTrend.procl_date != None) &
            ((ForeignLawTrend.asc_info == None) | (ForeignLawTrend.asc_info == "")) |
            ((ForeignLawTrend.detail_url != None) & ((ForeignLawTrend.proposal_text == None) | (ForeignLawTrend.proposal_text == "")))
        ).all()

        for law in targets:
            if law.detail_url:
                print(f"[외국입법] 📄 {law.title} - 설명 크롤링 중...")
                detail = crawl_foreign_description(law.detail_url)
                if not detail:
                    print(f"[외국입법] ❌ 재시도...")
                    time.sleep(1)
                    detail = crawl_foreign_description(law.detail_url)
                if detail:
                    law.proposal_text = detail
                else:
                    print(f"[외국입법] 🚫 실패: {law.detail_url}")
                time.sleep(1)
        db.commit()
        print("[외국입법] ✅ 설명 갱신 완료")
    finally:
        db.close()

if __name__ == "__main__":
    update_foreign_law_descriptions()
