import requests
from db import SessionLocal, PlenaryBill
from sqlalchemy.orm import Session

API_KEY = "145bca1e52594533863a5b12ec70dbc9"

def fetch_plenary_bills(age: int, pIndex: int = 1, pSize: int = 100):
    url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"  # 본회의 처리된 법안 API (예시)
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "AGE": age,
        "pIndex": pIndex,
        "pSize": pSize
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def save_plenary_bills_to_db(db: Session, bills: list):
    for bill in bills:
        bill_id = bill.get("BILL_ID")
        if not bill_id:
            continue
        exists = db.query(PlenaryBill).filter(PlenaryBill.bill_id == bill_id).first()
        if exists:
            continue

        new_bill = PlenaryBill(
            bill_id=bill_id,
            bill_no=bill.get("BILL_NO"),
            bill_name=bill.get("BILL_NM"),
            proposer=bill.get("PROPOSER"),
            proc_result_cd=bill.get("PROC_RESULT_CD"),
            committee_nm=bill.get("COMMITTEE_NM"),
            propose_dt=bill.get("PROPOSE_DT"),
            link_url=bill.get("LINK_URL"),
        )
        db.add(new_bill)
    db.commit()

def update_plenary_bills_db():
    age = 22
    all_rows = []
    for pIndex in range(1, 6):
        data = fetch_plenary_bills(age, pIndex=pIndex, pSize=100)
        bills_data = data.get("nwbpacrgavhjryiph", []) 
        if not bills_data:
            break
        for item in bills_data:
            rows = item.get("row", [])
            all_rows.extend(rows)

    db = SessionLocal()
    try:
        db.query(PlenaryBill).delete()
        db.commit()
        save_plenary_bills_to_db(db, all_rows)
        print("본회의 법안 목록 DB 갱신 완료")
    finally:
        db.close()

if __name__ == "__main__":
    update_plenary_bills_db()
