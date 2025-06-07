from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, ForeignLawTrend, ForeignLawExample
import math

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/foreign_legislation")
def foreign_legislation_combined(
    request: Request,
    page_trend: int = 1,
    page_example: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    # 외국입법동향
    trend_query = db.query(ForeignLawTrend)
    total_trend = trend_query.count()
    trend_rows = trend_query.order_by(ForeignLawTrend.procl_date.desc()) \
                            .offset((page_trend - 1) * size) \
                            .limit(size).all()

    # 외국입법례
    example_query = db.query(ForeignLawExample)
    total_example = example_query.count()
    example_rows = example_query.order_by(ForeignLawExample.issue_date.desc()) \
                                .offset((page_example - 1) * size) \
                                .limit(size).all()

    # 데이터 정제
    trends = [{
        "CN": r.cn,
        "TITLE": r.title,
        "NATION_NAME": r.nation_name,
        "PROCL_DATE": r.procl_date,
        "ASC_INFO": r.asc_info,
        "DETAIL_URL": r.detail_url
    } for r in trend_rows]

    examples = [{
        "CN": r.cn,
        "TITLE": r.title,
        "REL_LAW": r.rel_law,
        "ASC_NAME": r.asc_name,
        "ISSUE_DATE": r.issue_date,
        "DETAIL_URL": r.detail_url
    } for r in example_rows]

    # 페이지네이션 계산
    total_pages_trend = math.ceil(total_trend / size)
    total_pages_example = math.ceil(total_example / size)
    max_buttons = 5

    def calc_pages(current, total):
        half = max_buttons // 2
        start = max(1, current - half)
        end = min(total, start + max_buttons - 1)
        if end - start < max_buttons:
            start = max(1, end - max_buttons + 1)
        return start, end

    start_trend, end_trend = calc_pages(page_trend, total_pages_trend)
    start_example, end_example = calc_pages(page_example, total_pages_example)

    return templates.TemplateResponse("foreign_legislation.html", {
        "request": request,
        "trends": trends,
        "examples": examples,
        "page_trend": page_trend,
        "page_example": page_example,
        "total_count_trend": total_trend,
        "total_count_example": total_example,
        "total_pages_trend": total_pages_trend,
        "total_pages_example": total_pages_example,
        "start_trend": start_trend,
        "end_trend": end_trend,
        "start_example": start_example,
        "end_example": end_example,
        "size": size
    })
