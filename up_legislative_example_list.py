import requests
from db import SessionLocal, ForeignLawExample
from sqlalchemy.orm import Session

API_KEY = "9f665ae0aeea4ed1bc2f23e1326456a2"
ENDPOINT = "http://lnp.nanet.go.kr/openapi/lawissue"

def fetch_foreign_examples(page_no=1, display_lines=100):
    params = {
        "KEY": API_KEY,
        "TYPE": "json",
        "PAGE_NO": page_no,
        "DISPLAY_LINES": display_lines,
    }
    response = requests.get(ENDPOINT, params=params)
    response.raise_for_status()
    return response.json()

def save_foreign_examples_to_db(db: Session, items: list):
    for item in items:
        cn = item.get("CN")
        if not cn:
            continue
        exists = db.query(ForeignLawExample).filter(ForeignLawExample.cn == cn).first()
        if exists:
            continue
        db.add(ForeignLawExample(
            cn=cn,
            title=item.get("TITLE"),
            rel_law=item.get("REL_LAW"),
            asc_name=item.get("ASC_NAME"),
            issue_date=item.get("ISSUE_DATE"),
            detail_url=item.get("DETAIL_URL")
        ))
    db.commit()

def update_legislative_examples_db():
    all_rows = []
    seen_cn = set()

    for page_no in range(1, 21):  # 최대 20페이지 수집
        try:
            data = fetch_foreign_examples(page_no=page_no)
            rows = data.get("RECORD", [])
            print(f"📄 page {page_no} - {len(rows)}건")
            if data.get("RESULT_CODE") != "SUCCESS" or not rows:
                break
            for row in rows:
                cn = row.get("CN")
                if cn and cn not in seen_cn:
                    seen_cn.add(cn)
                    all_rows.append(row)
        except Exception as e:
            print(f"[에러] page {page_no} 요청 실패: {e}")
            continue

    all_rows.sort(key=lambda x: x.get("ISSUE_DATE", "00000000"), reverse=True)
    top_rows = all_rows[:500]

    db = SessionLocal()
    try:
        db.query(ForeignLawExample).delete()
        db.commit()
        save_foreign_examples_to_db(db, top_rows)
        print(f"✅ 총 저장 건수: {len(top_rows)}")
    finally:
        db.close()

if __name__ == "__main__":
    update_legislative_examples_db()
