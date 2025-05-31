from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram import Bot

# Можно добавить другие языки в команды, помимо русского.
users_commands: dict[str, dict[str, str]] = {
    "ru": {
        "start": "Запуск бота",
    },
}


async def set_default_commands(bot: Bot):

    for language_code, commands in users_commands.items():
        await bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in commands.items()
            ],
            scope=BotCommandScopeDefault(),
            language_code=language_code,
        )
