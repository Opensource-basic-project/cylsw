from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, ForeignLawTrend
import math
from sqlalchemy import or_, not_

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

STANDARD_NATIONS = ['미국', '일본', '독일', 'EU', '영국', '프랑스']
STANDARD_COMMITTEES = [
    '국회운영위원회', '법제사법위원회', '정무위원회', '기획재정위원회', '교육위원회',
    '과학기술정보방송통신위원회', '외교통일위원회', '국방위원회', '행정안전위원회', '문화체육관광위원회',
    '농림축산식품해양수산위원회', '산업통상자원중소벤처기업위원회', '보건복지위원회',
    '환경노동위원회', '국토교통위원회', '정보위원회', '여성가족위원회', '예산결산특별위원회'
]

@router.get("/legislative_trends")
def legislative_trends(
    request: Request,
    page: int = 1,
    size: int = 15,
    keyword: str = "",
    nation: str = "",
    committee: str = "",
    db: Session = Depends(get_db)
):
    query_obj = db.query(ForeignLawTrend)

    # 키워드 검색
    if keyword:
        like_keyword = f"%{keyword}%"
        query_obj = query_obj.filter(
            ForeignLawTrend.title.ilike(like_keyword) |
            ForeignLawTrend.asc_info.ilike(like_keyword)
        )
    
    # 국가 필터
    if nation == "기타":
        query_obj = query_obj.filter(~ForeignLawTrend.nation_name.in_(STANDARD_NATIONS))
    elif nation:
        query_obj = query_obj.filter(ForeignLawTrend.nation_name == nation)

    # 상임위원회 필터
    if committee == "기타":
        query_obj = query_obj.filter(
            or_(
                not_(ForeignLawTrend.asc_info.in_(STANDARD_COMMITTEES)),
                ForeignLawTrend.asc_info == None,
                ForeignLawTrend.asc_info == ""
            )
        )
    elif committee:
        query_obj = query_obj.filter(ForeignLawTrend.asc_info == committee)

    total_count = query_obj.count()
    rows = query_obj.order_by(ForeignLawTrend.procl_date.desc()) \
                    .offset((page - 1) * size) \
                    .limit(size).all()

    laws = [{
        "CN": r.cn,
        "TITLE": r.title,
        "NATION_NAME": r.nation_name,
        "PROCL_DATE": r.procl_date,
        "ASC_INFO": r.asc_info,
        "DETAIL_URL": r.detail_url
    } for r in rows]

    total_pages = math.ceil(total_count / size)
    max_buttons = 7
    start_page = max(1, page - max_buttons // 2)
    end_page = min(total_pages, start_page + max_buttons - 1)

    return templates.TemplateResponse("legislative_trends_list.html", {
        "request": request,
        "laws": laws,
        "page": page,
        "size": size,
        "keyword": keyword,
        "nation": nation,
        "committee": committee,
        "total_count": total_count,
        "start_page": start_page,
        "end_page": end_page,
        "total_pages": total_pages
    })
