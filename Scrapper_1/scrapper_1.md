# Wymagania Techniczne: Moduł Weryfikacji Cyfrowej (Scrapper_1)

Dokument ten opisuje specyfikację modułu weryfikacji cyfrowej kontrahenta na podstawie analizy jego obecności w sieci, zabezpieczeń witryny oraz aktywności.

---

## 1. Wyszukiwanie witryny (DuckDuckGo Search)
Jeżeli w bazach rejestrowych (KRS/CEIDG) brakuje oficjalnej witryny kontrahenta, system skorzysta z wyszukiwarki DuckDuckGo do odnalezienia potencjalnej domeny.

* **Biblioteka:** `duckduckgo-search` (w wersji asynchronicznej).
* **Sposób działania:**
  1. Budowa zapytania wyszukiwania na podstawie pełnej nazwy firmy oraz opcjonalnie numeru NIP (np. `"Nazwa Firmy Sp. z o.o. NIP 1234567890"` lub `"Nazwa Firmy oficjalna strona"`).
  2. Pobranie pierwszych 3-5 wyników wyszukiwania.
  3. Przefiltrowanie wyników pod kątem wykluczenia agregatorów danych (np. rejestr.io, krs-online.com, aplikuj.pl) w celu znalezienia właściwej domeny firmowej.

---

## 2. Bezpieczeństwo Połączenia (Szyfrowanie SSL / TLS)
System zweryfikuje, czy witryna stosuje bezpieczne protokoły komunikacji oraz czy certyfikat SSL/TLS jest w pełni poprawny i zaufany.

* **Technologia:** Moduły `ssl` oraz `socket` (Python Standard Library) zintegrowane z asynchronicznym klientem `httpx`.
* **Sposób działania:**
  1. Próba nawiązania połączenia przez `https://`.
  2. Pobranie parametrów sesji TLS (wersja protokołu, np. TLSv1.3).
  3. Odczytanie właściwości certyfikatu:
     * Status zaufania (czy wystawca jest zaufanym urzędem certyfikacji).
     * Okres ważności certyfikatu (data rozpoczęcia i zakończenia ważności).
     * Sprawdzenie, czy certyfikat nie wygasł lub nie wygaśnie w najbliższych dniach.

---

## 3. Wiek Domeny (RDAP - Registration Data Access Protocol)
Weryfikacja wieku domeny w celu odrzucenia ryzyka transakcji z niedawno zarejestrowanymi domenami (tzw. "firmami jednosezonowymi" lub domenami wyłudzającymi dane).

* **Technologia:** Bezpośrednie zapytania HTTP do rejestrów RDAP (np. za pośrednictwem serwera przekierowań `https://rdap.org/domain/{domena}`) za pomocą `httpx`.
* **Sposób działania:**
  1. Wyciągnięcie nazwy domeny głównej z adresu URL (np. `firma.pl` z `https://www.firma.pl/kontakt`).
  2. Pobranie JSON z serwera RDAP.
  3. Wyodrębnienie z sekcji `events` znacznika czasu dla akcji `registration` (data utworzenia domeny).
  4. Obliczenie wieku domeny w dniach/latach. Jeśli domena ma mniej niż 90 dni, przyznawany jest ujemny scoring punktowy.

---

## 4. Aktywność publikacyjna (Mierzenie aktualności za pomocą RSS)
Weryfikacja czy firma aktywnie prowadzi działalność operacyjną i marketingową w sieci.

* **Biblioteka:** `feedparser`
* **Sposób działania:**
  1. System wysyła zapytania do standardowych ścieżek RSS (np. `/feed`, `/rss`, `/news/feed`) w celu detekcji aktywnych kanałów dystrybucji treści.
  2. W przypadku znalezienia kanału RSS, parsuje ostatnie wpisy i sprawdza datę ich publikacji.
  3. Oblicza czas, jaki upłynął od ostatniego wpisu (np. aktywność w ciągu ostatnich 90 dni to dodatkowe punkty w ocenie wiarygodności).

---

## 5. Dodatkowe pomysły do implementacji (Rekomendacje)

W celu znacznego zwiększenia wiarygodności i skuteczności oceny cyfrowej, proponuję wdrożyć następujące mechanizmy:

### A. Dopasowanie NIP na stronie (NIP-Matching) [GORĄCO POLECAM]
* **Idea:** Automatyczne pobranie treści strony głównej / zakładki kontaktowej i wyszukanie na niej ciągu znaków odpowiadającego weryfikowanemu numerowi NIP firmy.
* **Uzasadnienie:** Jest to najpewniejsza metoda potwierdzenia, że znaleziona przez wyszukiwarkę domena faktycznie należy do badanej firmy (i nie jest to zbieżność nazw). Brak zgodności NIP-u powinien blokować przyznanie punktów za domenę.

### B. Wykrywanie Nagłówków Bezpieczeństwa (Security Headers Check)
* **Idea:** Odczytanie nagłówków HTTP odpowiedzi serwera w celu weryfikacji obecności podstawowych zabezpieczeń:
  * `Content-Security-Policy` (CSP)
  * `X-Frame-Options` (zabezpieczenie przed Clickjackingiem)
  * `Strict-Transport-Security` (HSTS - wymuszenie HTTPS)
* **Uzasadnienie:** Obecność tych nagłówków świadczy o wysokim profesjonalizmie i dbałości firmy o bezpieczeństwo użytkowników oraz danych.

### C. Weryfikacja formularza kontaktowego i linków do Social Media
* **Idea:** Ekstrakcja linków do profili społecznościowych (LinkedIn, Facebook) oraz sprawdzenie obecności adresu e-mail w domenie firmowej (np. `kontakt@firma.pl` zamiast `firma123@gmail.com`).
* **Uzasadnienie:** Posiadanie poczty we własnej domenie oraz aktywnych profili na LinkedIn/Facebooku znacząco uwiarygadnia działalność biznesową.

### D. Analiza pliku `robots.txt` i mapy witryny (`sitemap.xml`)
* **Idea:** Odpytanie `/robots.txt` w celu weryfikacji poprawności konfiguracji dla robotów sieciowych oraz odnalezienie sitemapy do wyciągnięcia dat modyfikacji podstron bez konieczności parsowania całego kodu HTML.
* **Uzasadnienie:** Pozwala to na nieinwazyjne pobranie informacji o dacie ostatniej aktualizacji dowolnej podstrony w witrynie.
