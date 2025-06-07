from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, LegislationNotice
from sqlalchemy import not_
import math

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/legislation_notice_ongoing")
def legislation_notice_ongoing(
    request: Request,
    page: int = 1,
    size: int = 15,
    query: str = "",
    committee: str = "",
    db: Session = Depends(get_db)
):
    query_obj = db.query(LegislationNotice)

    # 검색어 필터
    if query:
        query_filter = f"%{query}%"
        query_obj = query_obj.filter(
            (LegislationNotice.bill_name.ilike(query_filter)) |
            (LegislationNotice.proposer.ilike(query_filter))
        )

    # 상임위 필터
    STANDARD_COMMITTEES = [
        '국회운영위원회', '법제사법위원회', '정무위원회', '기획재정위원회', '교육위원회',
        '과학기술정보방송통신위원회', '외교통일위원회', '국방위원회', '행정안전위원회', '문화체육관광위원회',
        '농림축산식품해양수산위원회', '산업통상자원중소벤처기업위원회', '보건복지위원회',
        '환경노동위원회', '국토교통위원회', '정보위원회', '여성가족위원회', '예산결산특별위원회'
    ]
    if committee == "기타":
        query_obj = query_obj.filter(
            not_(LegislationNotice.curr_committee.in_(STANDARD_COMMITTEES))
        )
    elif committee:
        query_obj = query_obj.filter(LegislationNotice.curr_committee == committee)

    # 페이징
    total_count = query_obj.count()
    notices = query_obj.order_by(LegislationNotice.announce_dt.desc()) \
                       .offset((page - 1) * size) \
                       .limit(size) \
                       .all()

    # 출력 데이터 구성
    notices_list = []
    for n in notices:
        notices_list.append({
            "BILL_NAME": n.bill_name,
            "PROPOSER": n.proposer,
            "BILL_ID": n.bill_id,
            "NOTI_ED_DT": n.noti_ed_dt,
            "LINK_URL": n.link_url,
            "CURR_COMMITTEE": n.curr_committee,
            "ANNOUNCE_DT": n.announce_dt,
        })

    # 페이지 버튼 계산
    total_pages = math.ceil(total_count / size)
    max_buttons = 7
    half = max_buttons // 2
    start_page = max(1, page - half)
    end_page = start_page + max_buttons - 1
    if end_page > total_pages:
        end_page = total_pages
        start_page = max(1, end_page - max_buttons + 1)

    return templates.TemplateResponse("legislation_notice_ongoing_list.html", {
        "request": request,
        "ongoing_notices": notices_list,
        "page": page,
        "size": size,
        "query": query,
        "committee": committee,
        "total_count": total_count,
        "start_page": start_page,
        "end_page": end_page,
        "total_pages": total_pages,  
    })
