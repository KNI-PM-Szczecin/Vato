from __future__ import annotations
from datetime import date
from enum import Enum
from pydantic import BaseModel


class RiskLevel(str, Enum):
    ACCEPT = "Akceptacja"
    VERIFY = "Wymagana weryfikacja"
    REJECT = "Odrzucenie"


class ContractorInput(BaseModel):
    nip: str
    bank_account: str | None = None


class ContractorData(BaseModel):
    nip: str
    bank_account: str | None = None
    status_prawny: str = "NIEZNANY"
    data_rozpoczecia: date | None = None
    status_vat: str = "NIEZNANY"
    rachunek_na_bialej_liscie: bool = False
    zmiany_adresu_ostatni_rok: int = 0
    wymiana_zarzadu_ostatnie_3msc: bool = False
    czeste_zmiany_formy: bool = False


class ScoreResult(BaseModel):
    nip: str
    status_prawny: int = 0
    doswiadczenie: int = 0
    podatki_vat: int = 0
    stabilnosc: int = 0
    total: int = 0
    szczegoly: list[str] = []
    risk_level: RiskLevel = RiskLevel.VERIFY

    @property
    def max_score(self) -> int:
        return 40
