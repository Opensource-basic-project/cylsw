import requests
from db import SessionLocal, ForeignLawTrend
from sqlalchemy.orm import Session

API_KEY = "9f665ae0aeea4ed1bc2f23e1326456a2"
ENDPOINT = "http://lnp.nanet.go.kr/openapi/lawpreced"
KEYWORDS = ["법", "행정명령"]  # ✅ 다중 키워드 정의

def fetch_foreign_trends(page_no=1, display_lines=100, keyword="법"):
    params = {
        "KEY": API_KEY,
        "TYPE": "json",
        "PAGE_NO": page_no,
        "DISPLAY_LINES": display_lines,
        "SEARCH_KEYWORD": keyword,
    }
    response = requests.get(ENDPOINT, params=params)
    response.raise_for_status()
    return response.json()

def save_foreign_trends_to_db(db: Session, items: list):
    for item in items:
        cn = item.get("CN")
        if not cn:
            continue
        exists = db.query(ForeignLawTrend).filter(ForeignLawTrend.cn == cn).first()
        if exists:
            continue
        db.add(ForeignLawTrend(
            cn=cn,
            title=item.get("TITLE"),
            nation_name=item.get("NATION_NAME"),
            org_law_name=item.get("ORG_LAW_NAME"),
            procl_date=item.get("PROCL_DATE"),
            asc_info=item.get("ASC_INFO"),
            detail_url=item.get("DETAIL_URL")
        ))
    db.commit()

def update_legislative_trends_db():
    all_rows = []
    seen_cn = set()

    for keyword in KEYWORDS:
        print(f"🔍 키워드 '{keyword}' 수집 중...")
        for page_no in range(1, 21):
            try:
                data = fetch_foreign_trends(page_no=page_no, keyword=keyword)
                rows = data.get("RECORD", [])
                print(f"📄 {keyword} page {page_no} - {len(rows)}건")
                if data.get("RESULT_CODE") != "SUCCESS" or not rows:
                    break
                for row in rows:
                    cn = row.get("CN")
                    if cn and cn not in seen_cn:
                        seen_cn.add(cn)
                        all_rows.append(row)
            except Exception as e:
                print(f"[에러] {keyword} page {page_no} 요청 실패: {e}")
                continue

    # 최신순 정렬
    all_rows.sort(key=lambda x: x.get("PROCL_DATE", "00000000"), reverse=True)

    # 상위 500개만 저장 (주석 처리하면 전체 저장 가능)
    top_rows = all_rows[:500]

    db = SessionLocal()
    try:
        db.query(ForeignLawTrend).delete()
        db.commit()
        save_foreign_trends_to_db(db, top_rows)
        print(f"✅ 총 저장 건수: {len(top_rows)}")
    finally:
        db.close()

if __name__ == "__main__":
    update_legislative_trends_db()
