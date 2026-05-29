from enum import Enum

class AuctionType(str, Enum):
    ENGLISH = "english"
    SEALED_FIRST_PRICE = "sealed_first_price"