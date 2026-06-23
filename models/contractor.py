from __future__ import annotations
from datetime import date
from enum import Enum
from pydantic import BaseModel


class RiskLevel(str, Enum):
    ACCEPT = "Accepted"
    VERIFY = "Verification Required"
    REJECT = "Rejected"


class ContractorInput(BaseModel):
    nip: str
    bank_account: str | None = None


class ContractorData(BaseModel):
    nip: str
    bank_account: str | None = None
    legal_status: str = "UNKNOWN"
    start_date: date | None = None
    vat_status: str = "UNKNOWN"
    account_on_whitelist: bool = False
    address_changes_last_year: int = 0
    board_changes_last_3_months: bool = False
    frequent_legal_form_changes: bool = False


class ScoreResult(BaseModel):
    nip: str
    legal_status: int = 0
    experience: int = 0
    vat_taxes: int = 0
    stability: int = 0
    total: int = 0
    details: list[str] = []
    risk_level: RiskLevel = RiskLevel.VERIFY

    @property
    def max_score(self) -> int:
        return 40
