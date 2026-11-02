from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.enums.role import UserRoleEnum
from app.schemas.auth import CurrentUser

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> CurrentUser:
    payload = decode_token(credentials.credentials, "access") if credentials else None
    if payload is None or payload.get("role") not in UserRoleEnum._value2member_map_:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(id=int(payload["sub"]), role=payload["role"])


def require_role(*roles: UserRoleEnum):
    async def checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough rights")
        return user

    return checker


require_admin = require_role(UserRoleEnum.admin)
# Менеджер и администратор
require_staff = require_role(UserRoleEnum.admin, UserRoleEnum.manager)
