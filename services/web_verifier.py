import asyncio
import re
import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse, unquote
import httpx
import feedparser
import trafilatura
from bs4 import BeautifulSoup
from models.contractor import ContractorData

# Browser-like headers to avoid being blocked by search engines and basic firewalls
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pl,en-US;q=0.7,en;q=0.3"
}

# Extensive list of registries and aggregators to skip
IGNORED_DOMAINS = [
    "rejestr.io", "krs-online.com", "aplikuj.pl", "gowork.pl", 
    "panoramafirm.pl", "aleo.com", "mfind.pl", "oferteo.pl", 
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "youtube.com", "wikipedia.org", "wyszukiwarkaregon.stat.gov.pl",
    "money.pl", "biznes.gov.pl", "ceidg.gov.pl", "bizraport.pl",
    "infoveriti.pl", "krs360.pl", "owg.pl", "rejestr-krs.pl",
    "krs-pobierz.pl", "baza-krs.pl", "krajowyrejestrsadowy.pl",
    "kartoteka.pl", "firma.egospodarka.pl", "dnb.com", "teryt.pl",
    "krs-online.com.pl", "rejestr-danych.pl", "procedury.pl", "e-weksel.pl",
    "okredo.com", "okredo.pl", "rejestr-firm.pl", "szukaj-krs.pl", "imsig.pl"
]

def clean_company_name(name: str) -> str:
    """Removes formal Polish legal suffixes to focus on the company's core name/brand."""
    if not name or name == "---":
        return ""
    cleaned = name.upper()
    suffixes = [
        r"SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        r"SPÓŁKA AKCYJNA",
        r"SPÓŁKA JAWNA",
        r"SPÓŁKA KOMANDYTOWA",
        r"SPÓŁKA KOMANDYTOWO-AKCYJNA",
        r"SP\. Z O\.O\.",
        r"SP\.Z O\.O\.",
        r"SPÓŁKA Z O\.O\.",
        r"S\.A\.",
        r"SP\.J\.",
        r"SP\.K\.",
        r"SA$",
        r"S A$"
    ]
    for suffix in suffixes:
        cleaned = re.sub(suffix, "", cleaned)
    return " ".join(cleaned.split()).strip()

def extract_base_domain(url: str) -> str:
    """Extracts root domain from a full URL, supporting common SLDs like .com.pl."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    if domain.startswith("www."):
        domain = domain[4:]
    if ":" in domain:
        domain = domain.split(":")[0]
    parts = domain.split(".")
    if len(parts) > 2:
        # Support second-level domains
        if parts[-2] in ("com", "net", "org", "gov", "co", "edu", "mil", "ltd"):
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])
    return domain

def extract_yahoo_target(url: str) -> str:
    """Extracts the real destination URL from Yahoo tracking links."""
    try:
        match = re.search(r'/RU=([^/]+)', url)
        if match:
            return unquote(match.group(1))
    except Exception:
        pass
    return url

async def search_yahoo(query: str) -> str | None:
    """Searches Yahoo Search for a matching website domain."""
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=5) as client:
            res = await client.get("https://search.yahoo.com/search", params={"q": query})
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for div in soup.find_all("div", class_="compTitle"):
                    parent_classes = div.parent.attrs.get("class", [])
                    if any("algo" in c for c in parent_classes):
                        a = div.find("a", href=True)
                        if a:
                            target_url = extract_yahoo_target(a["href"])
                            if target_url.startswith("http") and "yahoo.com" not in target_url:
                                if not any(ignored in target_url.lower() for ignored in IGNORED_DOMAINS):
                                    return target_url
    except Exception as e:
        print(f"Błąd Yahoo Search dla '{query}': {e}")
    return None

async def search_ddg_lite(query: str) -> str | None:
    """Uses DuckDuckGo Lite as a fallback search engine."""
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=5) as client:
            res = await client.post("https://lite.duckduckgo.com/lite/", data={"q": query})
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("http") and "duckduckgo.com" not in href:
                        if not any(ignored in href.lower() for ignored in IGNORED_DOMAINS):
                            return href
    except Exception as e:
        print(f"Błąd DDG Lite dla '{query}': {e}")
    return None

def is_domain_similar(url: str, company_name: str) -> bool:
    """Checks if the found domain name is similar to the company's name to prevent matching random websites."""
    if not url or not company_name:
        return False
        
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc or parsed.path
        if netloc.startswith("www."):
            netloc = netloc[4:]
        domain_name = netloc.split('.')[0] if '.' in netloc else netloc
    except Exception:
        return False
        
    domain_clean = re.sub(r'[^a-z0-9]', '', domain_name.lower())
    
    def strip_pl(t: str) -> str:
        mapping = {
            'ą': 'a', 'Ą': 'A', 'ć': 'c', 'Ć': 'C', 'ę': 'e', 'Ę': 'E',
            'ł': 'l', 'Ł': 'L', 'ń': 'n', 'Ń': 'N', 'ó': 'o', 'Ó': 'O',
            'ś': 's', 'Ś': 'S', 'ź': 'z', 'Ź': 'Z', 'ż': 'z', 'Ż': 'Z'
        }
        for pol, eng in mapping.items():
            t = t.replace(pol, eng)
        return t
        
    cleaned_company = strip_pl(clean_company_name(company_name).lower())
    cleaned_company_clean = re.sub(r'[^a-z0-9\s]', '', cleaned_company)
    
    words = [w for w in cleaned_company_clean.split() if len(w) >= 3]
    if not words:
        return False
        
    # Check if first word of company name is in domain_clean
    first_word = words[0]
    if first_word in domain_clean or domain_clean in first_word:
        return True
        
    # Check if any other word of length >= 4 is in domain_clean
    for word in words:
        if len(word) >= 4 and (word in domain_clean or domain_clean in word):
            return True
            
    return False

async def search_website(company_name: str, nip: str) -> str | None:
    """Finds the company website domain using Yahoo Search with a DDG Lite fallback."""
    cleaned_name = clean_company_name(company_name)
    if not cleaned_name:
        return None

    def check_url(url: str | None) -> str | None:
        if url and is_domain_similar(url, company_name):
            return url
        return None

    # 1. Try with "strona oficjalna" first to avoid KRS directories which dominate NIP-based searches
    query_name = f"{cleaned_name} strona oficjalna"
    url = await search_yahoo(query_name)
    matched = check_url(url)
    if matched:
        return matched

    # 2. Try with NIP as fallback
    query_nip = f"{cleaned_name} NIP {nip}"
    url = await search_yahoo(query_nip)
    matched = check_url(url)
    if matched:
        return matched

    # 3. Try DDG Lite fallback
    url = await search_ddg_lite(query_name)
    matched = check_url(url)
    if matched:
        return matched
        
    url = await search_ddg_lite(query_nip)
    return check_url(url)

async def verify_ssl(url: str) -> bool:
    """Verifies if the website supports valid HTTPS/SSL connection."""
    try:
        test_url = url
        if url.startswith("http://"):
            test_url = "https://" + url[7:]
        elif not url.startswith("https://"):
            test_url = "https://" + url
            
        async with httpx.AsyncClient(verify=True, timeout=5, headers=HEADERS) as client:
            await client.get(test_url, follow_redirects=True)
            return True
    except Exception as e:
        print(f"Weryfikacja SSL/TLS nie powiodła się dla {url}: {e}")
        return False

async def check_domain_age(url: str) -> int | None:
    """Verifies domain age in days using the RDAP protocol."""
    try:
        domain = extract_base_domain(url)
        rdap_url = f"https://rdap.org/domain/{domain}"
        async with httpx.AsyncClient(timeout=5, headers=HEADERS) as client:
            response = await client.get(rdap_url, follow_redirects=True)
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", [])
                for event in events:
                    action = event.get("eventAction", "").lower()
                    if action in ("registration", "creation"):
                        reg_date_str = event.get("eventDate")
                        if reg_date_str:
                            date_part = reg_date_str.split("T")[0]
                            reg_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                            return (datetime.now().date() - reg_date).days
    except Exception as e:
        print(f"Błąd sprawdzania wieku domeny dla {url}: {e}")
    return None

async def check_rss_activity(url: str) -> int | None:
    """Checks recent posts on the website using RSS feeds."""
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme or 'https'}://{parsed.netloc}"
        
        feed_paths = ["/feed", "/rss", "/blog/feed", "/feed.xml", "/rss.xml"]
        async with httpx.AsyncClient(timeout=5, headers=HEADERS) as client:
            for path in feed_paths:
                try:
                    res = await client.get(base_url + path, follow_redirects=True)
                    if res.status_code == 200:
                        feed = await asyncio.to_thread(feedparser.parse, res.text)
                        if feed.entries:
                            latest = feed.entries[0]
                            date_parsed = latest.get("published_parsed") or latest.get("updated_parsed")
                            if date_parsed:
                                latest_date = datetime(*date_parsed[:6]).date()
                                return (datetime.now().date() - latest_date).days
                except Exception:
                    continue
    except Exception as e:
        print(f"Błąd sprawdzania RSS dla {url}: {e}")
    return None

async def check_trafilatura_activity(url: str) -> int | None:
    """Extracts date metadata from the main page using trafilatura."""
    try:
        async with httpx.AsyncClient(timeout=5, headers=HEADERS) as client:
            response = await client.get(url, follow_redirects=True)
            if response.status_code == 200:
                metadata = await asyncio.to_thread(trafilatura.extract_metadata, response.text)
                if metadata and metadata.date:
                    pub_date = datetime.strptime(metadata.date, "%Y-%m-%d").date()
                    return (datetime.now().date() - pub_date).days
    except Exception:
        pass
    return None

async def check_website_activity(url: str) -> int | None:
    """Tries RSS first, falls back to trafilatura metadata analysis."""
    rss_days = await check_rss_activity(url)
    if rss_days is not None:
        return rss_days
    
    traf_days = await check_trafilatura_activity(url)
    return traf_days

async def match_nip_on_website(url: str, nip: str) -> bool:
    """Verifies if the NIP number is printed on the website, scanning homepage and contact links."""
    try:
        clean_nip = "".join(filter(str.isdigit, nip))
        if not clean_nip:
            return False
            
        async with httpx.AsyncClient(timeout=5, headers=HEADERS) as client:
            # 1. Check homepage
            response = await client.get(url, follow_redirects=True)
            if response.status_code == 200:
                if verify_nip_in_text(response.text, clean_nip):
                    return True
                
                # 2. Dynamic discovery of contact/legal subpages from homepage
                candidate_links = []
                try:
                    soup = BeautifulSoup(response.text, "html.parser")
                    keywords = ["kontakt", "contact", "firma", "about", "regulamin", "privacy", "polityka", "legal", "dane"]
                    parsed = urlparse(url)
                    base_url = f"{parsed.scheme or 'https'}://{parsed.netloc}"
                    
                    for a in soup.find_all("a", href=True):
                        href = a["href"].strip()
                        text = a.text.strip().lower()
                        
                        if any(kw in text or kw in href.lower() for kw in keywords):
                            if href.startswith("/"):
                                full_url = base_url + href
                            elif href.startswith("http"):
                                full_url = href
                            else:
                                full_url = base_url + "/" + href
                            
                            parsed_link = urlparse(full_url)
                            if parsed_link.netloc == parsed.netloc:
                                if full_url not in candidate_links:
                                    candidate_links.append(full_url)
                except Exception as e:
                    print(f"Błąd dynamicznego skanowania linków dla {url}: {e}")

                # Scan dynamically discovered candidate links (limit to top 6 to prevent slow runs)
                for link in candidate_links[:6]:
                    try:
                        res = await client.get(link, follow_redirects=True)
                        if res.status_code == 200 and verify_nip_in_text(res.text, clean_nip):
                            return True
                    except Exception:
                        continue

            # 3. Fallback to standard hardcoded paths if homepage failed or returned no dynamic links
            subpaths = ["/kontakt", "/contact", "/polityka-prywatnosci", "/privacy-policy"]
            parsed = urlparse(url)
            base_url = f"{parsed.scheme or 'https'}://{parsed.netloc}"
            
            for path in subpaths:
                try:
                    res = await client.get(base_url + path, follow_redirects=True)
                    if res.status_code == 200 and verify_nip_in_text(res.text, clean_nip):
                        return True
                except Exception:
                    continue
                    
    except Exception as e:
        print(f"Błąd dopasowywania NIP na stronie {url}: {e}")
    return False


def verify_nip_in_text(text: str, clean_nip: str) -> bool:
    """Searches text for clean NIP digits or NIP digits separated by spaces/dashes."""
    patterns = [
        clean_nip,
        f"{clean_nip[:3]}-{clean_nip[3:6]}-{clean_nip[6:8]}-{clean_nip[8:]}",
        f"{clean_nip[:3]}-{clean_nip[3:5]}-{clean_nip[5:7]}-{clean_nip[7:]}"
    ]
    for pattern in patterns:
        if pattern in text:
            return True
            
    regex_pattern = r"[\s-]*".join(clean_nip)
    if re.search(regex_pattern, text):
        return True
    return False

async def enrich_with_web_data(contractor: ContractorData) -> ContractorData:
    """Enriches the contractor model with digital footprint verification."""
    company_name = contractor.legal_name
    nip = contractor.nip
    
    # 1. Search for website
    website_url = await search_website(company_name, nip)
    if not website_url:
        print(f"Nie odnaleziono oficjalnej strony WWW dla firmy: {company_name}")
        return contractor.model_copy(update={
            "website_url": None,
            "ssl_valid": False,
            "domain_age_days": None,
            "days_since_last_post": None,
            "website_nip_matched": False
        })
        
    # Standardize URL to base domain root
    base_domain = extract_base_domain(website_url)
    standardized_url = f"https://{base_domain}"
    
    print(f"Weryfikacja strony WWW dla {company_name}: {standardized_url}")
    
    # 2. Parallel tasks for SSL, Age, Activity and NIP matching
    ssl_task = verify_ssl(standardized_url)
    age_task = check_domain_age(standardized_url)
    activity_task = check_website_activity(standardized_url)
    nip_task = match_nip_on_website(standardized_url, nip)
    
    ssl_valid, domain_age_days, days_since_last_post, website_nip_matched = await asyncio.gather(
        ssl_task, age_task, activity_task, nip_task
    )
    
    return contractor.model_copy(update={
        "website_url": standardized_url,
        "ssl_valid": ssl_valid,
        "domain_age_days": domain_age_days,
        "days_since_last_post": days_since_last_post,
        "website_nip_matched": website_nip_matched
    })
