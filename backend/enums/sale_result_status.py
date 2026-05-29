from enum import Enum

class SaleResultStatus(str, Enum):
    PENDING = "pending"
    SOLD = "sold"
    RESERVE_NOT_MET = "reserve_not_met"
    AWAITING_SELLER_APPROVAL = "awaiting_seller_approval"
    REJECTED_BY_SELLER = "rejected_by_seller"