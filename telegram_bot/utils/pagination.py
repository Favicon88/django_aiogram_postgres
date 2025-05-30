import math
from typing import List, Literal, Optional

from constants import BUTTONS_PER_PAGE


class Pagination:
    """Класс реализует пагинацию."""

    def __init__(
        self,
        level: str,
        items: List,
        page: int = 1,
        per_page: int = BUTTONS_PER_PAGE,
    ):
        self.level = level
        self.items = items
        self.per_page = per_page
        self.page = page
        self.len = len(self.items)
        # math.ceil - округление в большую сторону до целого числа
        self.pages = math.ceil(self.len / self.per_page)

    def __get_slice(self):
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.items[start:stop]

    def get_page(self):
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        if self.page > 1:
            return self.page - 1
        return False
