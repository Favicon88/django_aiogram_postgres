from aiogram import Router


def get_handlers_router() -> Router:
    from . import payment_handlers
    from . import start
    from . import show_categories
    from . import cart_handlers
    from . import faq_handler

    router = Router()
    router.include_router(payment_handlers.router)
    router.include_router(start.router)
    router.include_router(show_categories.router)
    router.include_router(cart_handlers.router)
    router.include_router(faq_handler.router)

    return router
