from aiogram import Bot, Dispatcher
from typing import List, Dict, Tuple

from src.config import settings
from ..handlers import register_user_commands


dispatchers_by_webhook_url: Dict[str, Tuple[Bot, Dispatcher]] = {}
bots: List[Bot] = []


async def create_bot(token: str) -> Tuple[Bot, Dispatcher]:
    bot = Bot(token)
    dp = Dispatcher()
    register_user_commands(dp)

    dispatchers_by_webhook_url[
        f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}/{token}"
    ] = (bot, dp)
    await setup_webhook_for_bot(
        bot,
        f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}/{token}"
    )
    return bot, dp


async def add_new_bot(token: str):
    bot, dp = await create_bot(token)
    bots.append(bot)


async def init_multibots(tokens: List[Dict[str, str]]):
    for token_info in tokens:
        token = token_info["token_bot"]
        bot, dp = await create_bot(token)
        dispatchers_by_webhook_url[
            f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}/{token}"
        ] = (bot, dp)
        await setup_webhook_for_bot(
            bot,
            f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}/{token}"
        )


async def setup_webhook_for_bot(bot: Bot, webhook_url: str):
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != webhook_url:
        await bot.set_webhook(url=webhook_url)
