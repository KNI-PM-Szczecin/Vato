# Dokumentacja API dla Systemu Oceny Kontrahentów (KYC)

Ten dokument opisuje wszystkie zewnętrzne interfejsy API, które są symulowane i planowane do docelowego wdrożenia w algorytmie zawartym w pliku `api_test.py`. Zestawienie obejmuje informacje o wymaganej autoryzacji oraz przeznaczeniu pobieranych danych dla każdej z kategorii punktacji.

## Główne API używane w kodzie (Mockowane w fetch_company_data)

### 1. Krajowy Rejestr Sądowy (KRS)
* **Typ dostępu:** Publiczne REST API (Brak wymaganego klucza / w pełni darmowe).
* **Zastosowanie w kodzie:**
  * **Kategoria 1 (Status Prawny):** Weryfikacja bieżącego statusu spółek kapitałowych (aktywna, zawieszona, w stanie upadłości, w likwidacji).
  * **Kategoria 4 (Stabilność):** Analiza danych historycznych (biuletyny dobowe), aby wykryć drastyczne i częste zmiany adresu siedziby czy nagłą, całkowitą wymianę członków zarządu i udziałowców.

### 2. Centralna Ewidencja i Informacja o Działalności Gospodarczej (CEIDG)
* **Typ dostępu:** Autoryzacja wymagana – darmowy klucz API (Token pobierany z `.env` jako `CEIDG_API_KEY`).
* **Zastosowanie w kodzie:**
  * **Kategoria 1 (Status Prawny):** Weryfikacja statusu Jednoosobowych Działalności Gospodarczych.
  * **Kategoria 2 (Doświadczenie):** Wyciąganie daty rozpoczęcia działalności w celu precyzyjnego określenia, jak długo firma istnieje na rynku. Identyfikacja zjawiska wielokrotnego otwierania i zamykania działalności przez tę samą osobę fizyczną.

### 3. Biała Lista Podatników VAT (KAS)
* **Typ dostępu:** Publiczne REST API (Brak wymaganego klucza / usługa publiczna).
* **Zastosowanie w kodzie:**
  * **Kategoria 3 (Bezpieczeństwo Podatkowe i Płatnicze):** Weryfikacja bieżącego statusu VAT podatnika (czynny, zwolniony, wykreślony). 
  * Weryfikacja zgłoszonego numeru konta bankowego. W systemie przyznajemy karne punkty (-10), jeżeli numer konta z faktury nie znajduje się w ogólnopolskim rejestrze (co chroni firmę przed odpowiedzialnością solidarną za cudze długi podatkowe).

### 4. Baza Internetowa REGON (BIR1 - GUS)
* **Typ dostępu:** Autoryzacja wymagana – darmowy klucz użytkownika (Token pobierany z `.env` jako `REGON_API_KEY`).
* **Zastosowanie w kodzie:**
  * System używa tego interfejsu jako "uniwersalnej wyszukiwarki". Pozwala on jednoznacznie zidentyfikować, czy dany podmiot po wpisanym NIPie należy odpytać w KRS (spółka) czy w CEIDG (działalność jednoosobowa), a także pozyskać m.in. kod PKD głównej działalności.

---

## Opcjonalne API rozszerzające weryfikację

Poniższe API nie są kluczowe w podstawowym wariancie, ale zostały uwzględnione jako propozycje do pełniejszego obrazu kontrahenta.

### 5. Przeglądarka Dokumentów Finansowych (eKRS MS)
* **Typ dostępu:** Publiczne REST API (Brak wymaganego klucza).
* **Zastosowanie:** Odpytanie systemu o fakt złożenia corocznego sprawozdania finansowego w formie XML. Ostrzega, jeśli spółka ukrywa swoje dane finansowe i celowo spóźnia się z dostarczeniem bilansów do sądu.

### 6. VIES API (Komisja Europejska)
* **Typ dostępu:** Publiczne REST / SOAP API (Brak wymaganego klucza).
* **Zastosowanie:** Zautomatyzowana weryfikacja aktywności numeru VAT-EU przed dokonaniem transakcji wewnątrzwspólnotowej (WDT/WNT) przy zerowej stawce VAT.

### 7. API Biur Informacji Gospodarczej (np. KRD, BIG InfoMonitor)
* **Typ dostępu:** Komercyjne, płatne REST API (Wymaga dedykowanych kluczy w `.env` m.in. `KRD_API_KEY`).
* **Zastosowanie:** Bezpośredni wgląd do giełdy i rejestru długów. Skrypt weryfikowałby faktyczne długi wymagalne na rzecz innych przedsiębiorstw – silny wskaźnik utraty płynności finansowej, dający mocne podstawy do wygenerowania alertu o odrzuceniu współpracy.
