import os
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from models.db import get_session, Client, SignupIn, SigninIn, APIResponse, APIError
from helpers.security import hash_password, verify_password, new_csrf_token, validate_csrf, CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from helpers.auth import login_user, logout_user, current_user_id, require_user


app = FastAPI()
# Secret key for signing sessions
SESSION_SECRET = os.getenv("SESSION_SECRET", "-=1qaz2wsedcCDE#SW@ZAQ!=-")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,   # set True in production
    session_cookie="session",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---- CSRF validation ------------------------------------------------
def ensure_csrf(request: Request):
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if not validate_csrf(cookie_token, header_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

# ---- Pages ----------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    uid = current_user_id(request)
    return templates.TemplateResponse(
        "index.html", {
            "request": request, 
            "user_id": uid,
        }
    )

@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    token = new_csrf_token()
    resp = templates.TemplateResponse("signup.html", {"request": request, "csrf_token": token})
    resp.set_cookie(CSRF_COOKIE_NAME, token, samesite="Lax", secure=False, httponly=False, max_age=3600)
    return resp

@app.get("/signin", response_class=HTMLResponse)
async def signin(request: Request):
    token = new_csrf_token()
    resp = templates.TemplateResponse("signin.html", {"request": request, "csrf_token": token})
    resp.set_cookie(CSRF_COOKIE_NAME, token, samesite="Lax", secure=False, httponly=False, max_age=3600)
    return resp

@app.get("/signout")
async def signout(request: Request):
    resp = RedirectResponse(url="/", status_code=302)
    logout_user(resp, request)
    resp.delete_cookie(CSRF_COOKIE_NAME)
    return resp

@app.post("/api/signup", response_model=APIResponse)
async def api_signup(payload: SignupIn, request: Request, db: Session = Depends(get_session)):
    ensure_csrf(request)

    errors: list[APIError] = []
    existing = db.scalar(select(Client).where(Client.email == payload.email.lower()))
    if existing:
        errors.append(APIError(field="email", message="This email is already registered."))
        return JSONResponse(APIResponse(ok=False, errors=errors).model_dump())

    user = Client(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # TODO: catch errors in another way
        return JSONResponse(APIResponse(ok=False, errors=[APIError(field="email", message="This email is already registered.")]).model_dump())

    db.refresh(user)
    resp = JSONResponse(APIResponse(ok=True, redirect="/signin").model_dump())
    login_user(resp, request, str(user.id))
    new_token = new_csrf_token()
    resp.set_cookie(CSRF_COOKIE_NAME, new_token, samesite="Lax", secure=False, httponly=False, max_age=3600)
    return resp

@app.post("/api/signin", response_model=APIResponse)
async def api_signin(payload: SigninIn, request: Request, db: Session = Depends(get_session)):
    ensure_csrf(request)

    user = db.scalar(select(Client).where(Client.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        return JSONResponse(APIResponse(ok=False, errors=[APIError(field="form", message="Invalid email or password.")]).model_dump())

    resp = JSONResponse(APIResponse(ok=True, redirect="/meetings").model_dump())
    login_user(resp, request, str(user.id))
    new_token = new_csrf_token()
    resp.set_cookie(CSRF_COOKIE_NAME, new_token, samesite="Lax", secure=False, httponly=False, max_age=3600)
    return resp

@app.get("/download", response_class=HTMLResponse)
async def download(request: Request):
    return templates.TemplateResponse("download.html", {"request": request})

@app.get("/meetings", response_class=HTMLResponse)
async def meetings(request: Request, user_id: str = Depends(require_user), db: Session = Depends(get_session)):
    user = db.query(Client).filter(Client.id == user_id).first()
    if not user:
        return RedirectResponse(url="/signin")

    return templates.TemplateResponse(
        "meetings.html", 
        {
            "request": request, 
            "user_id": user_id,
            "user": user,
            "show_top_menu": True,
        }
    )

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
