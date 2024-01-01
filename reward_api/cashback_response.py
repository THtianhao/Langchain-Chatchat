from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CashbackDetail:
    cashback: str
    category: str

@dataclass
class Store:
    storeId: str
    cashbackLink: str
    storeName: str
    logoImg: str
    domain: str
    maxCashBack: str
    country: str
    cashbackDetail: List[CashbackDetail]
    categories: List[str]
    upto: Optional[bool]

@dataclass
class CashBackResponse:
    pageNumber: int
    pageSize: int
    records: int
    nextPage: bool
    stores: List[Store]