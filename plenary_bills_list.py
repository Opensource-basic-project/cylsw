from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, PlenaryBill  # PlenaryBill 테이블 import
import math
from sqlalchemy import not_
from sqlalchemy import or_, and_

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/plenary")
def get_plenary_bills(
    request: Request,
    page: int = 1,
    size: int = 15,
    query: str = "",
    committee: str = "",
    result: str = "",
    db: Session = Depends(get_db)
):
    query_obj = db.query(PlenaryBill)

    if query:
        query_filter = f"%{query}%"
        query_obj = query_obj.filter(
            (PlenaryBill.bill_name.ilike(query_filter)) |
            (PlenaryBill.proposer.ilike(query_filter))
        )

    STANDARD_COMMITTEES = [
        '국회운영위원회', '법제사법위원회', '정무위원회', '기획재정위원회', '교육위원회',
        '과학기술정보방송통신위원회', '외교통일위원회', '국방위원회', '행정안전위원회', '문화체육관광위원회',
        '농림축산식품해양수산위원회', '산업통상자원중소벤처기업위원회', '보건복지위원회',
        '환경노동위원회', '국토교통위원회', '정보위원회', '여성가족위원회', '예산결산특별위원회'
    ]
    if committee == "기타":
        query_obj = query_obj.filter(
            or_(
                not_(PlenaryBill.committee_nm.in_(STANDARD_COMMITTEES)),
                PlenaryBill.committee_nm == None,
                PlenaryBill.committee_nm == ""
            )
        )
    elif committee:
        query_obj = query_obj.filter(PlenaryBill.committee_nm == committee)
        
    if result:
        if result == "원안가결":
            query_obj = query_obj.filter(PlenaryBill.proc_result_cd == "원안가결")
        elif result == "수정가결":
            query_obj = query_obj.filter(
                PlenaryBill.proc_result_cd.in_(["수정가결", "대안반영가결"])
            )
        elif result == "철회":
            query_obj = query_obj.filter(PlenaryBill.proc_result_cd == "철회")
        elif result == "부결":
            query_obj = query_obj.filter(
                PlenaryBill.proc_result_cd.in_(["부결"])
            )
        elif result == "기타":
            excluded = ["원안가결", "수정가결", "대안반영가결", "부결", "철회"]
            query_obj = query_obj.filter(~PlenaryBill.proc_result_cd.in_(excluded))

        
    
    total_count = query_obj.count()

    bills = query_obj.order_by(PlenaryBill.propose_dt.desc()) \
                 .offset((page - 1) * size) \
                 .limit(size) \
                 .all()

    bill_list = []
    for bill in bills:
        bill_list.append({
            "BILL_ID": bill.bill_id,
            "BILL_NM": bill.bill_name,
            "PROPOSER": bill.proposer,
            "PROC_RESULT_CD": bill.proc_result_cd,
            "COMMITTEE_NM": bill.committee_nm,
            "PROPOSE_DT": bill.propose_dt,
            "LINK_URL": bill.link_url
        })
        
    total_pages = math.ceil(total_count / size)
    max_buttons = 7
    half = max_buttons // 2

    start_page = max(1, page - half)
    end_page = start_page + max_buttons - 1
    if end_page > total_pages:
        end_page = total_pages
        start_page = max(1, end_page - max_buttons + 1)


    return templates.TemplateResponse("plenary_bills_list.html", {
        "request": request,
        "bills": bill_list,
        "page": page,
        "size": size,
        "query": query,
        "committee": committee,
        "total_count": total_count,
        "start_page": start_page,
        "end_page": end_page,
        "total_pages": total_pages, 
        "result": result,
    })
