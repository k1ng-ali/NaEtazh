from fastapi import APIRouter, Cookie, Depends, Response, status

from app.core.config import settings
from app.deps.auth import get_current_user
from app.deps.services import get_auth_service
from app.schemas.auth import CurrentUser, LoginIn, TokenOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

REFRESH_COOKIE = "refresh_token"
# Cookie уходит только в запросы входа, а не во весь API
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=settings.REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, response: Response, service: AuthService = Depends(get_auth_service)):
    token, refresh_token = await service.login(login=data.login, password=data.password)
    _set_refresh_cookie(response, refresh_token)
    return token


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(None),
    service: AuthService = Depends(get_auth_service),
):
    token, new_refresh_token = await service.refresh(refresh_token=refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )


@router.get("/me", response_model=UserOut)
async def me(
    user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return await service.get_me(user_id=user.id)
