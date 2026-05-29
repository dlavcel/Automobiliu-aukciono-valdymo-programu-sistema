from enum import Enum

class BidType(str, Enum):
    ENGLISH = "english"
    SEALED = "sealed"
    DUTCH_ACCEPT = "dutch_accept"