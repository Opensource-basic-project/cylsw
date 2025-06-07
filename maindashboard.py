from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("")
async def main_dashboard(request: Request):
    return templates.TemplateResponse("maindashboard.html", {"request": request})
