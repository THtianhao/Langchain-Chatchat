from dataclasses import dataclass
from typing import List

@dataclass
class Coupon:
    couponTitle: str
    jumpUrl: str
    type: str
    couponCode: str
    tier: int
    startDateGMT: str
    endDateGMT: str
    storeId: int
    storeName: str
    logoImg: str
    categories: List[str]

@dataclass
class CouponResponse:
    code: str
    msg: str
    pageNumber: int
    pageSize: int
    totalRecords: int
    totalPages: int
    results: List[Coupon]