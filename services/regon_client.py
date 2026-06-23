import os
import re
import httpx

REGON_WSDL = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
LOGIN_URL = f"{REGON_WSDL}/dan/Login"

class RegonClient:
    def __init__(self):
        self.api_key = os.getenv("REGON_API_KEY", "")
        self._session_key: str | None = None


    async def _login(self, client: httpx.AsyncClient) -> str:
        """Obtain a session key from BIR1."""

        body = (
            '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"'
            ' xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
            "<soap:Header/><soap:Body><ns:Zaloguj>"
            f"<ns:pKluczUzytkownika>{self.api_key}</ns:pKluczUzytkownika>"
            "</ns:Zaloguj></soap:Body></soap:Envelope>"
        )

        headers = {
            "Content-Type": "application/soap+xml;charset=UTF-8",
            "SOAPAction": "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Zaloguj",

        }

        resp = await client.post(REGON_WSDL, content=body, headers=headers, timeout=10)
        resp.raise_for_status()
        match = re.search(r"<ZalogujResult>(.*?)</ZalogujResult>", resp.text)
        
        return match.group(1) if match else ""


    async def identify(self, nip: str) -> str:

        """Return 'KRS' for spółki or 'CEIDG' for JDG/osoby fizyczne."""
        async with httpx.AsyncClient() as client:
            session = await self._login(client)
            if not session:
                return "UNKNOWN"

            body = (
                '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"'
                ' xmlns:ns="http://CIS/BIR/PUBL/2014/07">'
                f"<soap:Header><ns:UserSession>{session}</ns:UserSession></soap:Header>"
                "<soap:Body><ns:DaneSzukajPodmioty><ns:pParametryWyszukiwania>"
                f"<ns:Nip>{nip}</ns:Nip>"
                "</ns:pParametryWyszukiwania></ns:DaneSzukajPodmioty></soap:Body></soap:Envelope>"
            )

            headers = {

                "Content-Type": "application/soap+xml;charset=UTF-8",
                "sid": session,
                "SOAPAction": "http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukajPodmioty",

            }

            resp = await client.post(REGON_WSDL, content=body, headers=headers, timeout=10)
            resp.raise_for_status()

            # Typ podmiotu: P → spółka (KRS), F/LP/LF → osoba fizyczna (CEIDG)
            match = re.search(r"<Typ>(.*?)</Typ>", resp.text)
            typ = match.group(1) if match else ""
            
            return "KRS" if typ == "P" else "CEIDG" 