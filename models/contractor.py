from __future__ import annotations
from datetime import date
from enum import Enum
from typing import Any
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
    country_code: str = "PL"
    legal_name: str = "---"
    bank_account: str | None = None
    status_prawny: str = "NIEZNANY"
    data_rozpoczecia: date | None = None
    status_vat: str = "NIEZNANY"
    rachunek_na_bialej_liscie: bool = False
    zmiany_adresu_ostatni_rok: int = 0
    wymiana_zarzadu_ostatnie_3msc: bool = False
    czeste_zmiany_formy: bool = False
    share_capital: float = None
    has_bailiff_proceedings: bool = None
    website_url: str | None = None
    ssl_valid: bool | None = None
    domain_age_days: int | None = None
    days_since_last_post: int | None = None
    website_nip_matched: bool | None = None
    scoring: Any = None 


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
