from fastapi import FastAPI

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

#static
from fastapi.staticfiles import StaticFiles

#DB
from db import init_db

app = FastAPI()

init_db()

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


app.mount("/static", StaticFiles(directory="static"), name="static")

#가상환경 권환 : Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
#가상환경 활성화 : .\venv\Scripts\Activate.ps1
#서버 실행 : uvicorn main:app --reload

