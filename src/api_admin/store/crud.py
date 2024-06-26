from typing import List, Optional
from datetime import datetime
from fastapi import Depends, HTTPException
from sqlalchemy import insert, select, delete, update
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.services import add_new_bot
from src.database import get_async_session
from .models import (
    Store, WorkingDay, StoreInfo,
    StoreOrderTypeAssociation, BotToken, DeliveryFix,
    DeliveryDistrict, DeliveryDistance, StoreSubscription,
    StorePayment, ServiceTextAndChat, LegalInformation,
    OrderType
)
from .schemas import (
    OneStore, StoreCreate, StoreUpdate,
    BotTokenCreate, UpdateStoreInfo,
    UpdateLegalInformation, PostDeliveryDistance,
    PostDeliveryDistrict, PostDeliveryFix, PostStoreInfo,
    UpdateDeliveryFix, UpdaneDayOfWeek, UpdateDeliveryDistance,
    UpdateDeliveryDistrict, UpdateServiceTextAndChat, UpdateStorePayment,
    CreateOrderType, ListOrderType, BaseStoreOrderTypeAssociation,
    GetStoreInfo
)


async def crud_get_all_stores(
    schema: str,
    session: AsyncSession = Depends(get_async_session)
):
    query = (
        select(Store).
        options(
            joinedload(Store.info),
            joinedload(Store.subscriptions)
        ).
        order_by(Store.id.desc()).
        execution_options(
            schema_translate_map={None: schema}
        )
    )
    result = await session.execute(query)
    stores = result.scalars().all()
    return stores


async def crud_get_one_stores(
    store_id: int,
    schema: str,
    session: AsyncSession = Depends(get_async_session)
) -> Optional[OneStore]:
    query = (
        select(Store).
        where(Store.id == store_id).
        options(
            joinedload(Store.info).
            options(joinedload(StoreInfo.types_delivery)),
            joinedload(Store.subscriptions),
            joinedload(Store.association).
            options(joinedload(StoreOrderTypeAssociation.order_type)),
            joinedload(Store.working_days).
            options(joinedload(WorkingDay.days_of_week)),
            joinedload(Store.payments),
            joinedload(Store.service_text_and_chats),
            joinedload(Store.legal_information)
        ).
        execution_options(schema_translate_map={None: schema})
    )
    result = await session.execute(query)
    store = result.scalar()
    type_delivery_id = store.info.type_delivery_id

    if type_delivery_id:
        delivery_info = await get_delyvery_type_info(
            type_delivery_id=type_delivery_id,
            store_id=store_id,
            schema=schema,
            session=session
        )
        store.delivery_info = delivery_info

    bot_token_query = select(BotToken).where(BotToken.store_id == store_id)
    bot_token_result = await session.execute(bot_token_query)
    bot_token = bot_token_result.scalar()

    store.bot_tokens = bot_token

    return store


async def get_delyvery_type_info(
    type_delivery_id: int,
    store_id: int,
    schema: str,
    session: AsyncSession = Depends(get_async_session)
):
    model_mapping = {
        1: DeliveryFix,
        2: DeliveryDistrict,
        3: DeliveryDistance
    }
    selected_model = model_mapping.get(type_delivery_id)
    if not selected_model:
        return None
    query = (
        select(selected_model).
        where(selected_model.store_id == store_id).
        execution_options(schema_translate_map={None: schema})
    )
    result = await session.execute(query)
    if type_delivery_id == 2:
        return result.scalars().all()
    else:
        return result.scalar()


async def crud_get_info_store_token(
    bot_token: str,
    session: AsyncSession = Depends(get_async_session)
):
    query = select(BotToken).where(BotToken.token_bot == bot_token)
    result = await session.execute(query)
    store = result.scalar()
    return store


async def crud_get_info_store_token_all(
    session: AsyncSession = Depends(get_async_session)
):
    query = select(BotToken)
    result = await session.execute(query)
    store = result.scalars().all()
    return store


async def read_test_many_to_many(
    session: AsyncSession = Depends(get_async_session)
):
    query = (
        select(StoreOrderTypeAssociation).
        where(StoreOrderTypeAssociation.store_id == 1).
        options(joinedload(StoreOrderTypeAssociation.order_type)).
        execution_options(schema_translate_map={None: "1"})
    )
    result = await session.execute(query)
    stores = result.scalars().all()
    return stores


async def crud_create_new_store(
    schema: str,
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        insert(Store).
        values(
            user_id=user_id,
            created_by=user_id
        ).
        execution_options(schema_translate_map={None: schema}).
        returning(Store.id)
    )
    result = await session.execute(stmt)
    new_store_id = result.scalar()
    await session.commit()

    return {"status": 201, "id": new_store_id, }


async def crud_create_new_store_and_bot(
    schema: str,
    data: StoreCreate,
    token_bot: BotTokenCreate,
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    store_result = await crud_create_new_store(
        schema=schema,
        user_id=user_id,
        session=session
    )
    store_id = store_result.get("id")
    await add_new_bot(token_bot.token_bot)
    await session.execute(
        insert(BotToken).
        values(
            **token_bot.model_dump(),
            user_id=user_id,
            store_id=store_id
        )
    )
    await session.execute(
        insert(StoreInfo).
        values(
            **data.model_dump(),
            store_id=store_id
        ).
        execution_options(schema_translate_map={None: schema}))
    await session.execute(
        insert(StoreSubscription).
        values(store_id=store_id).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(
        insert(StorePayment).
        values(store_id=store_id).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(
        insert(ServiceTextAndChat).
        values(store_id=store_id).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(
        insert(LegalInformation).
        values(store_id=store_id).
        execution_options(schema_translate_map={None: schema})
    )
    order_type_values = [{'store_id': store_id, 'order_type_id': order_type_id,
                          'is_active': False} for order_type_id in range(1, 4)]
    working_day_values = [
        {
            'store_id': store_id,
            'day_of_week_id': day_of_week_id,
            'is_working': False
        } for day_of_week_id in range(1, 8)
    ]

    await session.execute(
        insert(StoreOrderTypeAssociation).
        values(order_type_values).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(
        insert(WorkingDay).
        values(working_day_values).
        execution_options(schema_translate_map={None: schema})
    )
    await session.commit()
    return {"status": 201}


async def crud_update_store(
    schema: str,
    user_id: int,
    store_id: int,
    data: StoreUpdate,
    session: AsyncSession = Depends(get_async_session)
) -> List[StoreUpdate]:
    stmt = (
        update(StoreInfo).
        where(StoreInfo.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_get_legal_informations(
    store_id: int,
    schema: str,
    session: AsyncSession = Depends(get_async_session)
):
    query = (
        select(LegalInformation).
        where(LegalInformation.store_id == store_id).
        execution_options(schema_translate_map={None: schema})
    )
    result = await session.execute(query)
    store = result.scalar()
    return store


async def crud_update_store_info(
    schema: str,
    user_id: int,
    store_id: int,
    data: UpdateStoreInfo,
    session: AsyncSession = Depends(get_async_session)
) -> List[UpdateStoreInfo]:
    stmt = (
        update(StoreInfo).
        where(StoreInfo.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_update_store_legal_informations(
    schema: str,
    user_id: int,
    store_id: int,
    data: UpdateLegalInformation,
    session: AsyncSession = Depends(get_async_session)
) -> List[UpdateLegalInformation]:
    stmt = (
        update(LegalInformation).
        where(LegalInformation.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_create_store_delivery_distance(
    schema: str,
    user_id: int,
    data: PostDeliveryDistance,
    session: AsyncSession = Depends(get_async_session)
) -> List[PostDeliveryDistance]:
    stmt = (
        insert(DeliveryDistance).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_update_store_delivery_distance(
    schema: str,
    user_id: int,
    store_id: int,
    data: UpdateDeliveryDistance,
    session: AsyncSession = Depends(get_async_session)
) -> List[UpdateDeliveryDistance]:
    stmt = (
        update(DeliveryDistance).
        where(DeliveryDistance.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_create_store_delivery_fix(
    schema: str,
    user_id: int,
    data: PostDeliveryFix,
    session: AsyncSession = Depends(get_async_session)
) -> List[PostDeliveryFix]:
    stmt = (
        insert(DeliveryFix).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_update_store_delivery_fix(
    schema: str,
    user_id: int,
    store_id: int,
    data: UpdateDeliveryFix,
    session: AsyncSession = Depends(get_async_session)
) -> List[UpdateDeliveryFix]:
    stmt = (
        update(DeliveryFix).
        where(DeliveryFix.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_create_store_delivery_district(
    schema: str,
    user_id: int,
    data: PostDeliveryDistrict,
    session: AsyncSession = Depends(get_async_session)
) -> List[PostDeliveryDistrict]:
    stmt = (
        insert(DeliveryDistrict).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_update_store_delivery_district(
    schema: str,
    user_id: int,
    store_id: int,
    delivery_id: int,
    data: UpdateDeliveryDistrict,
    session: AsyncSession = Depends(get_async_session)
) -> List[UpdateDeliveryDistrict]:
    stmt = (
        update(DeliveryDistrict).
        where(DeliveryDistrict.id == delivery_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_get_service_text_and_chats(
    store_id: int,
    schema: str,
    session: AsyncSession = Depends(get_async_session)
):
    query = (
        select(ServiceTextAndChat).
        where(ServiceTextAndChat.store_id == store_id).
        execution_options(schema_translate_map={None: schema})
    )
    result = await session.execute(query)
    store = result.scalar()
    return store


async def crud_update_service_text_and_chats(
    schema: str,
    user_id: int,
    store_id: int,
    data: UpdateServiceTextAndChat,
    session: AsyncSession = Depends(get_async_session)
) -> List[UpdateServiceTextAndChat]:
    stmt = (
        update(ServiceTextAndChat).
        where(ServiceTextAndChat.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_get_store_payments(
    store_id: int,
    schema: str,
    session: AsyncSession = Depends(get_async_session)
):
    query = (
        select(StorePayment).
        where(StorePayment.store_id == store_id).
        execution_options(schema_translate_map={None: schema})
    )
    result = await session.execute(query)
    store = result.scalar()
    return store


async def crud_update_store_payments(
    schema: str,
    user_id: int,
    store_id: int,
    data: UpdateStorePayment,
    session: AsyncSession = Depends(get_async_session)
) -> List[UpdateStorePayment]:
    stmt = (
        update(StorePayment).
        where(StorePayment.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success", 'date': data}


async def crud_change_delete_flag_store(
    schema: str,
    user_id: int,
    store_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        update(Store).
        where(Store.id == store_id).
        values(
            deleted_flag=~Store.deleted_flag,
            deleted_at=datetime.now(),
            deleted_by=user_id).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"message": "Статус для deleted_flag изменен"}


async def crud_delete_store(
    schema: str,
    store_id: int,
    session: Session = Depends(get_async_session)
):
    try:
        stmt = delete(Store).where(Store.id == store_id).execution_options(
            schema_translate_map={None: schema}
        )
        await session.execute(stmt)
        await session.commit()
        return {
            "status": "success",
            "message": f"Магазин, c id {store_id}, успешно удалена."
        }
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Удаление этого магазина невозможно, "
                "так как на нее ссылаются продукты."
            )
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


async def crud_delete_delivery_district(
    schema: str,
    store_id: int,
    delivery_id: int,
    session: Session = Depends(get_async_session)
):
    try:
        stmt = (
            delete(DeliveryDistrict).
            where(
                DeliveryDistrict.store_id == store_id,
                DeliveryDistrict.id == delivery_id
            ).
            execution_options(schema_translate_map={None: schema})
        )
        await session.execute(stmt)
        await session.commit()
        return {
            "status": "success",
            "message": f"Район доставки, c id {store_id}, успешно удален."
        }
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Удаление этого района доставки невозможно, "
                "так как на него ссылаются отчёты."
            )
        )
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


async def crud_update_store_activity(
    schema: str,
    store_id: int,
    session: Session = Depends(get_async_session)
):
    stmt = (
        update(StoreSubscription).
        where(StoreSubscription.store_id == store_id).
        values(is_active=~StoreSubscription.is_active).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"message": "Изменён статус активности"}


async def crud_update_order_type(
    schema: str,
    store_id: int,
    order_type_id: int,
    session: Session = Depends(get_async_session)
):
    stmt = (
        update(StoreOrderTypeAssociation).
        where(
            StoreOrderTypeAssociation.store_id == store_id,
            StoreOrderTypeAssociation.order_type_id == order_type_id
        ).
        values(is_active=~StoreOrderTypeAssociation.is_active).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"message": "Изменён статус активности"}


async def crud_create_new_order_type(
    data: CreateOrderType,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = insert(OrderType).values(**data.model_dump())
    await session.execute(stmt)
    await session.commit()

    return {"status": 201, "data": data}


async def crud_get_all_order_types(
    session: AsyncSession = Depends(get_async_session)
) -> List[ListOrderType]:
    query = select(OrderType).order_by(OrderType.id.desc())
    result = await session.execute(query)
    stores = result.scalars().all()
    return stores


async def crud_update_day_of_week(
    schema: str,
    store_id: int,
    day_of_week_id: int,
    session: Session = Depends(get_async_session)
):
    stmt = (
        update(WorkingDay).
        where(
            WorkingDay.store_id == store_id,
            WorkingDay.day_of_week_id == day_of_week_id
        ).
        values(is_active=~WorkingDay.is_working).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()
    return {"message": "Изменён статус активности"}


async def crud_update_checkbox_payments(
    schema: str,
    store_id: int,
    checkbox: str,
    session: Session = Depends(get_async_session)
):
    field_to_update = getattr(StorePayment, checkbox, None)
    if field_to_update is not None:
        field_name = field_to_update.key
        stmt = (
            update(StorePayment).
            where(StorePayment.store_id == store_id).
            values(**{field_name: ~field_to_update}).
            execution_options(schema_translate_map={None: schema})
        )
        await session.execute(stmt)
        await session.commit()
        return {"message": f"Статус для {checkbox} изменен"}
    else:
        raise ValueError(f"Недопустимое значение checkbox: {checkbox}")


async def crud_update_checkbox_store_info(
    schema: str,
    store_id: int,
    checkbox: str,
    session: Session = Depends(get_async_session)
):
    checkboxes = ["format_unified", "format_24_7", "format_custom"]
    if checkbox not in checkboxes:
        raise ValueError(f"Недопустимое значение checkbox: {checkbox}")

    field_to_update = getattr(StoreInfo, checkbox, None)
    if field_to_update is not None:
        values_to_update = {field: False for field in checkboxes}
        values_to_update[checkbox] = True

        stmt = (
            update(StoreInfo).
            where(StoreInfo.store_id == store_id).
            values(**values_to_update).
            execution_options(schema_translate_map={None: schema})
        )
        await session.execute(stmt)
        await session.commit()
        return {"message": f"Статус для {checkbox} изменен"}
    else:
        raise ValueError(f"Недопустимое значение checkbox: {checkbox}")


async def crud_create_new_store_order_types_association(
    schema: str,
    data: BaseStoreOrderTypeAssociation,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        insert(StoreOrderTypeAssociation).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()

    return {"status": 201, "data": data}


async def crud_update_new_day_of_week(
    schema: str,
    user_id: int,
    store_id: str,
    day_of_week_id: int,
    data: UpdaneDayOfWeek,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        update(WorkingDay).
        where(
            WorkingDay.store_id == store_id,
            WorkingDay.day_of_week_id == day_of_week_id
        ).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()

    return {"status": 201, "data": data}


async def crud_get_store_info(
    session: AsyncSession = Depends(get_async_session)
):
    query = (
        select(StoreInfo).
        order_by(StoreInfo.id.desc()).
        execution_options(schema_translate_map={None: '1'})
    )
    result = await session.execute(query)
    store_info = result.scalars().all()
    return store_info


async def crud_create_new_test(
    schema: str,
    store_id: int,
    data: PostStoreInfo,
    session: AsyncSession = Depends(get_async_session)
):
    stmt = (
        update(StoreInfo).
        where(StoreInfo.store_id == store_id).
        values(**data.model_dump()).
        execution_options(schema_translate_map={None: schema})
    )
    await session.execute(stmt)
    await session.commit()

    return {"status": 201, }


async def crud_test_get_one_stores(
    store_id: int,
    schema: str,
    session: AsyncSession = Depends(get_async_session)
) -> Optional[GetStoreInfo]:
    query = (
        select(StoreInfo).
        where(StoreInfo.store_id == store_id).
        execution_options(schema_translate_map={None: schema})
    )
    result = await session.execute(query)
    store = result.scalar()
    return store


async def crud_test_many_to_many(
    store_id: int,
    schema: str,
    session: AsyncSession = Depends(get_async_session)
) -> Optional[GetStoreInfo]:
    query = (
        select(StoreInfo).
        where(StoreInfo.store_id == store_id).
        execution_options(schema_translate_map={None: schema})
    )
    result = await session.execute(query)
    store = result.scalar()
    return store
