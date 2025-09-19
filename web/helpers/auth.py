from typing import Optional
from fastapi import Request, Response, HTTPException, status


SESSION_KEY = "user_id"

def login_user(response: Response, request: Request, user_id: str):
    """Store user id in session."""
    request.session[SESSION_KEY] = str(user_id)

def logout_user(response: Response, request: Request):
    """Clear user from session."""
    request.session.pop(SESSION_KEY, None)

def current_user_id(request: Request) -> Optional[str]:
    """Return current logged-in user id, or None."""
    return request.session.get(SESSION_KEY)

def require_user(request: Request) -> str:
    """Raise 401 if no user logged in, otherwise return user_id."""
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user_id
