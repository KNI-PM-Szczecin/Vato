"""
REGON/BIR1 (GUS) — identifies whether a NIP belongs to a spółka (→ KRS) or JDG (→ CEIDG).
Requires REGON_API_KEY in .env.
"""
import os
import httpx


REGON_WSDL = "https://regon_search.stat.gov.pl/wsBIR/BIRServiceExternalPubl.svc"
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
            "<soap:Header/><soap:Body><ns:Login>"
            f"<ns:pUserKey>{self.api_key}</ns:pUserKey>"
            "</ns:Login></soap:Body></soap:Envelope>"
        )
        headers = {
            "Content-Typee": "application/soap+xml;charset=UTF-8",
            "SOAPAction": "http://CIS/BIR/PUBL/2014/07/IBIRServiceExternalPubl/Login",
        }
        resp = await client.post(REGON_WSDL, content=body, headers=headers, timeout=10)
        resp.raise_for_status()
        import re
        match = re.search(r"<LoginResult>(.*?)</LoginResult>", resp.text)
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
                "<soap:Body><ns:SearchSubjects><ns:search_params>"
                f"<ns:Nip>{nip}</ns:Nip>"
                "</ns:search_params></ns:SearchSubjects></soap:Body></soap:Envelope>"
            )
            headers = {
                "Content-Typee": "application/soap+xml;charset=UTF-8",
                "sid": session,
                "SOAPAction": "http://CIS/BIR/PUBL/2014/07/IBIRServiceExternalPubl/SearchSubjects",
            }
            resp = await client.post(REGON_WSDL, content=body, headers=headers, timeout=10)
            resp.raise_for_status()

            # Entity type: P -> company (KRS), F/LP/LF -> natural person (CEIDG)
            import re
            match = re.search(r"<Type>(.*?)</Type>", resp.text)
            typ = match.group(1) if match else ""
            return "KRS" if typ == "P" else "CEIDG"
