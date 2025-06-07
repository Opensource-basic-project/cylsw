from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, LegislationNotice, EndedLegislationNotice
import math

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/legislation_notice")
def legislation_notice_combined(
    request: Request,
    page_ongoing: int = 1,
    page_ended: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    # 진행 중 입법예고
    ongoing_query = db.query(LegislationNotice)
    total_ongoing = ongoing_query.count()
    ongoing_notices = ongoing_query.order_by(LegislationNotice.announce_dt.desc()) \
                                   .offset((page_ongoing - 1) * size) \
                                   .limit(size).all()

    # 종료된 입법예고
    ended_query = db.query(EndedLegislationNotice)
    total_ended = ended_query.count()
    ended_notices = ended_query.order_by(EndedLegislationNotice.announce_dt.desc()) \
                                 .offset((page_ended - 1) * size) \
                                 .limit(size).all()

    # 리스트 변환
    ongoing_list = [
        {
            "BILL_NAME": n.bill_name,
            "PROPOSER": n.proposer,
            "BILL_ID": n.bill_id,
            "NOTI_ED_DT": n.noti_ed_dt,
            "LINK_URL": n.link_url,
            "CURR_COMMITTEE": n.curr_committee,
            "ANNOUNCE_DT": n.announce_dt,
        } for n in ongoing_notices
    ]

    ended_list = [
        {
            "BILL_NAME": n.bill_name,
            "PROPOSER": n.proposer,
            "BILL_ID": n.bill_id,
            "NOTI_ED_DT": n.noti_ed_dt,
            "LINK_URL": n.link_url,
            "CURR_COMMITTEE": n.curr_committee,
            "ANNOUNCE_DT": n.announce_dt,
        } for n in ended_notices
    ]

    # 페이지네이션 계산
    total_pages_ongoing = math.ceil(total_ongoing / size)
    total_pages_ended = math.ceil(total_ended / size)
    max_buttons = 5

    def calc_pages(current, total):
        half = max_buttons // 2
        start = max(1, current - half)
        end = min(total, start + max_buttons - 1)
        if end - start < max_buttons:
            start = max(1, end - max_buttons + 1)
        return start, end

    start_ongoing, end_ongoing = calc_pages(page_ongoing, total_pages_ongoing)
    start_ended, end_ended = calc_pages(page_ended, total_pages_ended)

    return templates.TemplateResponse("legislation_notice.html", {
        "request": request,
        "ongoing_notices": ongoing_list,
        "ended_notices": ended_list,
        "page_ongoing": page_ongoing,
        "page_ended": page_ended,
        "total_count_ongoing": total_ongoing,
        "total_count_ended": total_ended,
        "total_pages_ongoing": total_pages_ongoing,
        "total_pages_ended": total_pages_ended,
        "start_ongoing": start_ongoing,
        "end_ongoing": end_ongoing,
        "start_ended": start_ended,
        "end_ended": end_ended,
        "size": size
    })
