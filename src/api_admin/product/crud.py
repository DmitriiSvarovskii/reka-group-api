from fastapi import Depends, HTTPException
from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List

from ..models import Product, Category
from .schemas import *
from src.database import get_async_session


async def crud_create_new_product(schema: str, data: ProductCreate, user_id: int, session: AsyncSession = Depends(get_async_session)):
    try:
        stmt = insert(Product).values(**data.dict(), created_by=user_id).execution_options(
            schema_translate_map={None: schema})
        await session.execute(stmt)
        await session.commit()
        return {"status": 201, 'date': data}
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


async def crud_update_product(schema: str, user_id: int, product_id: int, data: ProductUpdate, session: AsyncSession = Depends(get_async_session)) -> List[ProductUpdate]:
    stmt = update(Product).where(
        Product.id == product_id).values(**data.dict(), updated_by=user_id).execution_options(schema_translate_map={None: schema})
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_change_delete_flag_product(schema: str, user_id: int, product_id: int, session: AsyncSession = Depends(get_async_session)):
    stmt = update(Product).where(Product.id == product_id).values(
        deleted_flag=~Product.deleted_flag,
        deleted_at=datetime.now(),
        deleted_by=user_id).execution_options(schema_translate_map={None: schema})
    await session.execute(stmt)
    await session.commit()
    return {"message": f"Статус для deleted_flag изменен"}


async def crud_delete_product(schema: str, product_id: int, session: Session = Depends(get_async_session)):
    try:
        stmt = delete(Product).where(Product.id == product_id).execution_options(
            schema_translate_map={None: schema})
        await session.execute(stmt)
        await session.commit()
        return {"status": "success", "message": f"Категория, c id {product_id}, успешно удалена."}
    except IntegrityError as e:
        raise HTTPException(
            status_code=400, detail="Удаление этой категории невозможно, так как на нее ссылаются продукты.")
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


async def crud_update_product_field(schema: str, product_id: int, user_id: int, checkbox: str, session: AsyncSession = Depends(get_async_session)):
    field_to_update = getattr(Product, checkbox, None)
    if field_to_update is not None:
        field_name = field_to_update.key
        stmt = update(Product).where(Product.id == product_id).values(
            **{field_name: ~field_to_update},
            updated_at=datetime.now(),
            updated_by=user_id).execution_options(schema_translate_map={None: schema})
        await session.execute(stmt)
        await session.commit()
        return {"message": f"Статус для {checkbox} изменен"}
    else:
        raise ValueError(f"Недопустимое значение checkbox: {checkbox}")
