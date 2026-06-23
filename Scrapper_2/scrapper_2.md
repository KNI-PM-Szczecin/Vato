# Wymagania Techniczne: Drugi Moduł Scrapera (Scrapper_2)

Dokument ten opisuje specyfikację techniczną drugiego modułu scrapperów w systemie **Vato**, odpowiedzialnego za weryfikację reputacji medialnej kontrahenta oraz detekcję potencjalnych oszustw phishingowych (homograficznych) w jego domenie internetowej.

---

## 1. Detekcja Phishingu w Domenie (Weryfikacja Alfabetu)

W celu ochrony przed atakami typu phishing, w których oszuści rejestrują domeny łudząco podobne do prawdziwych firm przy użyciu znaków spoza dozwolonego zestawu (np. cyrylica wyglądająca identycznie jak litery łacińskie - tzw. homoglify/IDN spoofing), system realizuje automatyczną analizę domen.

* **Technologia:** Dekodowanie IDNA (`codecs` / `.encode("ascii").decode("idna")`) oraz wyrażenia regularne (`re`).
* **Sposób działania:**
  1. Wyodrębnienie domeny głównej z adresu URL (np. `xn--kongsbrg-61a.pl` -> `kongsbrg.pl` z cyrylickim `е`).
  2. Jeżeli domena rozpoczyna się od prefiksu Punycode `xn--`, następuje jej zdekodowanie do postaci Unicode.
  3. Sprawdzenie, czy w zdekodowanej nazwie domeny występują znaki spoza podstawowego alfabetu łacińskiego, cyfr, myślników, kropek oraz oficjalnego zestawu polskich znaków diakrytycznych (`ąęćłńóśźż`).
  4. Jeśli wykryte zostaną znaki pochodzące z innych alfabetów (np. cyrylicy, greki itp.), domena zostaje oznaczona jako **podejrzana pod kątem phishingu**.
* **Wpływ na Scoring:** Wykrycie podejrzanej domeny skutkuje karą punktową w wysokości **-10 pkt** nakładaną na całkowity wynik wiarygodności kontrahenta.

---

## 2. Monitorowanie Wiadomości i Reputacji (Google News / Yahoo News RSS)

Moduł ten służy do oceny śladu medialnego firmy oraz wykrywania anomalii w postaci negatywnych doniesień prasowych. Działa asynchronicznie, pobierając najnowsze nagłówki prasowe i dopasowując je do profilu firmy.

* **Biblioteki:** `httpx` (asynchroniczny klient HTTP), `feedparser` (do obsługi kanałów RSS).
* **Sposób działania:**
  1. Oczyszczenie nazwy rejestrowej firmy z przyrostków prawnych (np. "Sp. z o.o.", "S.A.") w celu wyszukania samej marki handlowej.
  2. Wykonanie zapytania do agregatora wiadomości Google News RSS z parametrami regionalnymi dla Polski (`hl=pl&gl=PL&ceid=PL:pl`).
  3. Pobranie i sparsowanie **10 ostatnich wiadomości** dotyczących firmy.
  4. Analiza każdego nagłówka pod kątem słów kluczowych o charakterze negatywnym (np. *okradł*, *oszustwo*, *upadłość*, *areszt*, *likwidacja*, *wyrok*, *śledztwo*), z pominięciem polskich znaków przy dopasowaniu (dla zwiększenia niezawodności).
* **Wpływ na Scoring:**
  * **Znalezienie wzmianek medialnych (neutralnych/pozytywnych):** Traktowane jako dodatkowy atut wiarygodności cyfrowej firmy (**+2 pkt** bonusu).
  * **Brak wzmianek:** Ocena neutralna (**0 pkt**), brak kary punktowej.
  * **Wykrycie anomalii (negatywnych wiadomości powiązanych z firmą):** Wyświetlenie ostrzeżenia w raporcie wraz z linkami/tytułami oraz nałożenie kary punktowej w wysokości **-15 pkt** na całkowity wynik scoringu.

---

## 3. Integracja z Architekturą Vato

Moduł `Scrapper_2` jest zintegrowany bezpośrednio z warstwą usług (`services/news_verifier.py` i `services/web_verifier.py`), a pobierane dane zasilają model `ContractorData` w polach `news_found`, `news_anomalies` oraz `suspicious_domain`. 

Scoring jest automatycznie przeliczany przez `scoring/scorer.py`, a wyniki wraz ze szczegółowym uzasadnieniem trafiają do widoków GUI CustomTkinter oraz plików eksportowych Excel (`raport.xlsx`) oraz PDF (`raport.pdf`).
