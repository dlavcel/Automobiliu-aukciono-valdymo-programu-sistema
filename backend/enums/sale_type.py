from enum import Enum

class SaleType(str, Enum):
    PURE_SALE = "pure_sale"
    RESERVE_PRICE = "reserve_price"
    ON_APPROVAL = "on_approval"