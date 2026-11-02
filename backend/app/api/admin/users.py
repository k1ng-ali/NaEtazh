from fastapi import APIRouter, Depends, status

from app.deps.auth import require_admin
from app.deps.services import get_user_service
from app.schemas.auth import CurrentUser
from app.schemas.user import UserAdminOut, UserCreateIn, UserPasswordIn, UserUpdateIn
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Admin • Users"])


@router.get("/", response_model=list[UserAdminOut], dependencies=[Depends(require_admin)])
async def list_users(service: UserService = Depends(get_user_service)):
    return await service.list_users()


@router.post(
    "/",
    response_model=UserAdminOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_user(data: UserCreateIn, service: UserService = Depends(get_user_service)):
    return await service.create_user(data=data)


@router.patch("/{user_id}", response_model=UserAdminOut)
async def update_user(
    user_id: int,
    data: UserUpdateIn,
    user: CurrentUser = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):
    return await service.update_user(user_id=user_id, data=data, current_user_id=user.id)


@router.put(
    "/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)]
)
async def set_password(user_id: int, data: UserPasswordIn, service: UserService = Depends(get_user_service)):
    await service.set_password(user_id=user_id, password=data.password)
