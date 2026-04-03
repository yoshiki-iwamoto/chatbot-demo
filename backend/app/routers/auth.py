from fastapi import APIRouter, HTTPException, status

from app.auth.jwt_handler import create_access_token
from app.config import settings
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    if (
        request.username != settings.ADMIN_USERNAME
        or request.password != settings.ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    access_token = create_access_token(data={"sub": request.username})
    return TokenResponse(access_token=access_token, token_type="bearer")
