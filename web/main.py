from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signin", response_class=HTMLResponse)
async def signin(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/download", response_class=HTMLResponse)
async def download(request: Request):
    return templates.TemplateResponse("download.html", {"request": request})

@app.get("/meetings", response_class=HTMLResponse)
async def meetings(request: Request):
    return templates.TemplateResponse("meetings.html", {"request": request})

@app.get("/create-meeting", response_class=HTMLResponse)
async def create_meeting(request: Request):
    return templates.TemplateResponse("create-meeting.html", {"request": request})

@app.get("/meeting-report", response_class=HTMLResponse)
async def meeting_report(request: Request):
    return templates.TemplateResponse("meeting-report.html", {"request": request})

@app.get("/account-settings", response_class=HTMLResponse)
async def account(request: Request):
    return templates.TemplateResponse("account-settings.html", {"request": request})

@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
