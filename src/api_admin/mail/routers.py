from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_async_session

from .crud import *
from .schemas import *
from ..user import User
from ..auth.routers import get_current_user_from_token


router = APIRouter(
    prefix="/api/v1/mail",
    tags=["Mail (admin)"])


@router.get("/", response_model=List[CategoryList], status_code=200)
async def get_all_category(store_id: int, current_user: User = Depends(get_current_user_from_token), session: AsyncSession = Depends(get_async_session)):
    try:
        categories = await crud_get_all_categories(schema=str(current_user.id), store_id=store_id, session=session)
        return categories
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


@router.post("/", status_code=201)
async def create_new_category(store_id: int, data: CategoryCreate,  current_user: User = Depends(get_current_user_from_token), session: AsyncSession = Depends(get_async_session)):
    try:
        new_category = await crud_create_new_category(schema=current_user.store_id, store_id=store_id,  data=data, user_id=current_user.id, session=session)
        return new_category
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


@router.put("/", status_code=200)
async def update_category(category_id: int, data: CategoryUpdate,  current_user: User = Depends(get_current_user_from_token), session: AsyncSession = Depends(get_async_session)):
    try:
        up_category = await crud_update_category(schema=str(current_user.id), category_id=category_id, data=data, user_id=current_user.id, session=session)
        return up_category
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


@router.put("/delete/")
async def change_delete_flag_category(category_id: int, current_user: User = Depends(get_current_user_from_token), session: AsyncSession = Depends(get_async_session)):
    try:
        change_category = await crud_change_delete_flag_category(schema=str(current_user.id), user_id=current_user.id, category_id=category_id, session=session)
        return change_category
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


@router.put("/checkbox/",)
async def update_category_field(category_id: int, checkbox: str, current_user: User = Depends(get_current_user_from_token), session: AsyncSession = Depends(get_async_session)):
    """
    Параметры:

    - `category_id`: идентификатор категории.
    - `checkbox`: имя поля, которое требуется изменить. Для категории доступно только: `availability`.
   """
    try:
        change_category = await crud_update_category_field(schema=str(current_user.id), user_id=current_user.id, category_id=category_id, checkbox=checkbox, session=session)
        return change_category
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


@router.delete("/")
async def delete_category(category_id: int, current_user: User = Depends(get_current_user_from_token), session: AsyncSession = Depends(get_async_session)):
    try:
        change_category = await crud_delete_category(schema=str(current_user.id), category_id=category_id, session=session)
        return change_category
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")
