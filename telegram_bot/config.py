import logging
import os
from logging.handlers import RotatingFileHandler

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from constants import DATETIME_FORMAT
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")
# id и url канала для проверки подписки (например: -1001234567890), можно вывести в бд
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_URL = os.getenv("CHANNEL_URL")
# id и url группы для проверки подписки, можно вывести в бд
GROUP_ID = int(os.getenv("GROUP_ID"))
GROUP_URL = os.getenv("GROUP_URL")
YOO_TOKEN = os.getenv("YOO_TOKEN")  # токен YooKassa
LOG_FILE_PATH = os.getenv("LOG_FILE", "logs/telegram_bot.log")
EXCEL_FILE = "orders_data/orders.xlsx"

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
    encoding="utf-8",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            LOG_FILE_PATH,
            mode="a",
            maxBytes=10 * 1024 * 1024,  # до 10 мегабайт
            backupCount=5,  # Количество архивных файлов
            encoding="utf-8",
        ),
    ],
)
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt=DATETIME_FORMAT, utc=True),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.contextvars.merge_contextvars,
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(ensure_ascii=False),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger(__name__)

dp = Dispatcher()
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
