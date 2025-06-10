from fastapi import FastAPI, Request, Depends, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.wsgi import WSGIMiddleware

# 기능 파일 라우팅 
from plenary_bills_list import router as plenary_router   
from plenary_bills_detail import router as plenary_detail_router
from legislation_notice_ongoing_list import router as notice_list_router
from legislation_notice_ended_list import router as notice_list_ended_router
from legislation_notice_ongoing_detail import router as notice_detail_router
from legislation_notice_ended_detail import router as notice_detail_ended_router
from legislative_trends_list import router as trends_router
from legislative_trends_detail import router as trends_detail_router
from legislative_example_list import router as example_list_router
from legislative_example_detail import router as example_detail_router 
from legislation_notice import router as legislation_notice_router
from foreign_legislation import router as foreign_legislation_router
from maindashboard import router as main_dashboard_router

# Dash 앱
from dash_news_app import create_dash_app_news, create_dash_app_from_result, create_dash_app_from_result_in
from Cdash_app import create_Cdash_app
from dash_app import create_dash_app

# DB 관련
from db import init_db
from dbmanage import init_db
from dbmanage_CNT import init_CNTdb
from dbmanage_News import SessionLocal, BillNews
from dbmanage_NewsReact import NewsSentiment, NewsComment
from dbmanage_ranking import TrendingBill

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

# 뉴스 크롤링 및 분석
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from GetNewslink import search_news_unique
from GetNewsReact import load_comments, analyze_sentiment
from insert_NewsScript import get_article_body

# 메인 기능 블럭
from main_load import (
    get_latest_laws, 
    get_latest_news, 
    get_plenary_info_main,
    get_notice_info_main,
    get_foreign_info_main
    )

# 기타
from types import SimpleNamespace
from datetime import datetime
from pathlib import Path
import math
import os

init_db() # db 초기화

# db 경로 지정
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'bills.db'}"

# SQLAlchemy 기본 설정
engine = create_engine(DATABASE_URL, echo=False)
app = FastAPI()
templates = Jinja2Templates(directory="dash_news/html")         #뉴스 html 연결
templates_main = Jinja2Templates(directory="dash_main/html")    #메인 html 연결

dash = create_dash_app_from_result()  # 초기 bill_id 없이
# plotly 그래프들 mount
app.mount("/dash_news_view", WSGIMiddleware(dash.server))
app.mount("/dash_news_app_live", WSGIMiddleware(create_dash_app_from_result_in().server))
app.mount("/dash/", WSGIMiddleware(create_dash_app().server))
app.mount("/dash2/", WSGIMiddleware(create_Cdash_app().server))

# DB 연결 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 정적 파일 경로 mount (=> 병합후 경로수정 static => static_)
app.mount("/static_", StaticFiles(directory=os.path.join(BASE_DIR, "dash_news/html")), name="static_")


BASE_DIR = Path(__file__).resolve().parent
HTML_DIR = BASE_DIR / "dash_main" / "html"
app.mount("/dash_main/html", StaticFiles(directory=str(HTML_DIR)), name="html")

BASE_DIR_ = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR_ / "dash_main" / "assets"
app.mount("/dash_main/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")







def truncate(text, limit=10):
    return text[:limit] + "..." if len(text) > limit else text


# 여론분석
def get_top_5_bills(db_path="sqlite:///bills.db"):
    engine = create_engine(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    top_5 = session.query(TrendingBill).order_by(TrendingBill.rank.asc()).limit(5).all()
    return top_5


@app.get("/dashboard", response_class=HTMLResponse)
async def read_index(request: Request):
    law_list = get_latest_laws(n=3)
    latest_news = get_latest_news()
    top_5_bills = get_top_5_bills()
    plenary_main = get_plenary_info_main()
    noticelaw = get_notice_info_main()
    examples, trends = get_foreign_info_main()
    

    return templates_main.TemplateResponse("index.html", {
        "request": request,
        "laws": law_list,
        "latest_news": latest_news,
        "top_5_bills": top_5_bills,
        "plenary_mlist": plenary_main,
        "noticelaw": noticelaw,
        "examples" : examples,
        "trends": trends,
    })



app.include_router(plenary_router)
app.include_router(plenary_detail_router)
app.include_router(notice_list_router)
app.include_router(notice_list_ended_router)
app.include_router(notice_detail_router)
app.include_router(notice_detail_ended_router)
app.include_router(trends_router)
app.include_router(trends_detail_router)
app.include_router(example_list_router)
app.include_router(example_detail_router) 
app.include_router(legislation_notice_router)
app.include_router(foreign_legislation_router)
app.include_router(main_dashboard_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def redirect_to_dashboard():
    return RedirectResponse(url="/dashboard")
#가상환경 권환 : Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
#가상환경 활성화 : .\venv\Scripts\Activate.ps1
#서버 실행 : uvicorn main:app --reload




# 여론분석 뉴스 검색어 처리 => 기능 비활성화 (selenium 접근 방지)
@app.post("/analyze_news")
def analyze_news(request: Request, title: str = Form(...), db: Session = Depends(get_db)):
    title = title.strip()

    num = 1

    if num:
        return templates.TemplateResponse("index_news.html", {
            "request": request,
            "error": "",
            "title": "",
            "article_title": "배포 사이트에서는 지원되지 않는 기능입니다.",
            "article_url": "",
            "article_html": "배포 사이트에서는 지원되지 않는 기능입니다.",
            "total_comments": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "total": 0,
            "comments": [],
            "query": title,
            "dash_url": "",
            "has_prev": False,
            "has_next": False,
            "current_page": 1,
            "total_pages": 1,
            "start_page": 1,
            "end_page": 1,
            "size": 1,
            "result": "",
        })
    

    

# db  기반 기본 페이지
@app.get("/public_opinion")
def get_index_news(request: Request, page: int = 1, db: Session = Depends(get_db)):
    per_page = 1
    total_bills = db.query(NewsSentiment).count()
    total_pages = math.ceil(total_bills / per_page)

    if page < 1 or page > total_pages:
        page = 1

    offset = (page - 1) * per_page

    news_sentiment = (
        db.query(NewsSentiment)
        .order_by(NewsSentiment.id)
        .offset(offset)
        .limit(per_page)
        .first()
    )

    if not news_sentiment:
        return templates.TemplateResponse("index_news.html", {
            "request": request,
            "error": "데이터를 찾을 수 없습니다.",
            "title": "",
            "article_title": "데이터가 없습니다.",
            "article_url": "",
            "article_html": "데이터베이스에 일치하는 검색 결과가 없습니다. 검색 기능을 이용하세요.",
            "total_comments": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "total": 0,
            "comments": [],
            "query": "",
            "dash_url": "",
            "has_prev": False,
            "has_next": False,
            "current_page": 1,
            "total_pages": 1,
            "start_page": 1,
            "end_page": 1,
            "size": 1,
            "result": "",
        })

    dash_app = create_dash_app_news()
    app.mount("/dash_news_app", WSGIMiddleware(dash_app.server))

    bill_news = (
        db.query(BillNews)
        .filter(
            BillNews.bill_id == news_sentiment.bill_id,
            BillNews.news_url == news_sentiment.news_url
        )
        .first()
    )

    comments = (
        db.query(NewsComment)
        .filter(
            NewsComment.bill_id == news_sentiment.bill_id,
            NewsComment.news_url == news_sentiment.news_url
        )
        .order_by(NewsComment.id.asc())
        .all()
    )

    # iframe용 Dash URL 생성
    dash_url_news = f"/dash_news_app/?page={page}"

    PAGE_DISPLAY_COUNT = 5
    start_page = max(1, page - PAGE_DISPLAY_COUNT // 2)
    end_page = min(total_pages, start_page + PAGE_DISPLAY_COUNT - 1)
    if (end_page - start_page) < (PAGE_DISPLAY_COUNT - 1):
        start_page = max(1, end_page - PAGE_DISPLAY_COUNT + 1)

    return templates.TemplateResponse("index_news.html", {
        "request": request,
        "title": news_sentiment.title,
        "article_title": bill_news.news_title if bill_news else "",
        "article_url": bill_news.news_url if bill_news else "",
        "article_html": bill_news.body if bill_news else "",
        "total_comments": bill_news.comment_count if bill_news else 0,
        "positive_count": news_sentiment.positive_count,
        "negative_count": news_sentiment.negative_count,
        "neutral_count": news_sentiment.neutral_count,
        "total": news_sentiment.positive_count + news_sentiment.negative_count + news_sentiment.neutral_count,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "current_page": page,
        "total_pages": total_pages,
        "start_page": start_page,
        "end_page": end_page,
        "size": per_page,
        "query": "",
        "committee": "",
        "result": "",
        "comments": comments,
        "dash_url_live": "",
        "dash_url_news": dash_url_news
    })

