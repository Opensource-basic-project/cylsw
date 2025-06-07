from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import SessionLocal, ForeignLawExample
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

STANDARD_COMMITTEES = [
    '국회운영위원회', '법제사법위원회', '정무위원회', '기획재정위원회', '교육위원회',
    '과학기술정보방송통신위원회', '외교통일위원회', '국방위원회', '행정안전위원회', '문화체육관광위원회',
    '농림축산식품해양수산위원회', '산업통상자원중소벤처기업위원회', '보건복지위원회',
    '환경노동위원회', '국토교통위원회', '정보위원회', '여성가족위원회', '예산결산특별위원회'
]

NATION_KEYWORDS = {
    "미국": ["USA", "U.S.", "미국"],
    "일본": ["일본", "Japan"],
    "영국": ["영국", "UK", "United Kingdom"],
    "독일": ["독일", "Germany"],
    "프랑스": ["프랑스", "France"],
    "유럽연합": ["EU", "유럽연합", "European Union"]
}

@router.get("/legislative_examples")
def legislative_examples(
    request: Request,
    page: int = 1,
    size: int = 15,
    keyword: str = "",
    nation: str = "",
    committee: str = "",
    db: Session = Depends(get_db)
):
    query_obj = db.query(ForeignLawExample)

    
    if keyword:
        like_keyword = f"%{keyword}%"
        query_obj = query_obj.filter(
            ForeignLawExample.title.ilike(like_keyword) |
            ForeignLawExample.rel_law.ilike(like_keyword)
        )

    if committee == "기타":
        query_obj = query_obj.filter(
            or_(
                not_(ForeignLawExample.asc_name.in_(STANDARD_COMMITTEES)),
                ForeignLawExample.asc_name == None,
                ForeignLawExample.asc_name == ""
            )
        )
    elif committee:
        query_obj = query_obj.filter(ForeignLawExample.asc_name == committee)
        
    if nation == "기타":
        exclude_conditions = [
            ForeignLawExample.title.ilike(f"%{kw}%")
            for kws in NATION_KEYWORDS.values() for kw in kws
        ]
        query_obj = query_obj.filter(~or_(*exclude_conditions))
    elif nation:
        keywords = NATION_KEYWORDS.get(nation, [])
        include_conditions = [ForeignLawExample.title.ilike(f"%{kw}%") for kw in keywords]
        query_obj = query_obj.filter(or_(*include_conditions))

    total_count = query_obj.count()
    rows = query_obj.order_by(ForeignLawExample.issue_date.desc()) \
                    .offset((page - 1) * size) \
                    .limit(size).all()

    examples = [{
        "CN": r.cn,
        "TITLE": r.title,
        "REL_LAW": r.rel_law,
        "ASC_NAME": r.asc_name,
        "ISSUE_DATE": r.issue_date,
        "DETAIL_URL": r.detail_url
    } for r in rows]

    total_pages = math.ceil(total_count / size)
    max_buttons = 7
    start_page = max(1, page - max_buttons // 2)
    end_page = min(total_pages, start_page + max_buttons - 1)

    return templates.TemplateResponse("legislative_example_list.html", {
        "request": request,
        "examples": examples,
        "page": page,
        "size": size,
        "keyword": keyword,
        "selected_nation": nation,
        "committee": committee, 
        "total_count": total_count,
        "start_page": start_page,
        "end_page": end_page,
        "total_pages": total_pages
    })
