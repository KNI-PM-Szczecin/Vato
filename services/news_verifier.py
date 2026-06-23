import httpx
import feedparser
import urllib.parse
import re

# Negative Polish keywords indicating reputation risk/anomalies
NEGATIVE_KEYWORDS = [
    # Theft / Fraud
    "okradl", "okradla", "okradli", "oszustwo", "oszustwa", "oszukal", 
    "oszukala", "oszukali", "wyludzenie", "wyłudzenie", "kradziez", "kradzież",
    # Insolvency / Bankruptcy
    "bankructwo", "upadlosc", "upadłość", "likwidacja", "niewyplacalny", 
    "niewypłacalny", "niewyplacalnoscz", "niewypłacalność",
    # Scandals
    "afera", "skandal", "korupcja", "korupcji", "łapówka", "lapowka",
    # Prosecution / Arrest
    "prokuratura", "prokurator", "areszt", "aresztowanie", "zatrzymany", "zatrzymana",
    # Indebtedness
    "zadluzenie", "zadłużenie", "niewyplacone", "niewypłacone", "dlugi", "długi", "dlug", "dług",
    # Court / Legal disputes
    "proces sadowy", "proces sądowy", "sprawa w sadzie", "sprawa w sądzie", 
    "nakaz sadowy", "nakaz sądowy", "spor sadowy", "spór sądowy",
    "skazany", "skazana", "wyrok", "sedzia", "sędzia", "sprawa karna", 
    "śledztwo", "sledztwo", "zarzuty", "oskarżenie", "oskarzenie",
    "pozwany", "pozwana", "pozew", "sad", "sąd"
]

def clean_txt(text: str) -> str:
    """Helper to remove Polish diacritics for easier text matching."""
    mapping = {
        'ą': 'a', 'Ą': 'A', 'ć': 'c', 'Ć': 'C', 'ę': 'e', 'Ę': 'E',
        'ł': 'l', 'Ł': 'L', 'ń': 'n', 'Ń': 'N', 'ó': 'o', 'Ó': 'O',
        'ś': 's', 'Ś': 'S', 'ź': 'z', 'Ź': 'Z', 'ż': 'z', 'Ż': 'Z'
    }
    for pol, eng in mapping.items():
        text = text.replace(pol, eng)
    return text.lower()

def matches_negative_keyword(cleaned_title: str, keyword: str) -> bool:
    """
    Checks if a negative keyword matches the cleaned title.
    Uses regex with inflected forms and word boundaries for short/ambiguous words to avoid false positives.
    """
    cleaned_kw = clean_txt(keyword)
    
    # Custom regex patterns for short words that require precise inflection matching
    if cleaned_kw in ("sad", "sąd"):
        # Matches sąd, sądu, sądem, sądzie, sądy, sądów, sądom, sądami, sądach
        pattern = r'\bsad(u|em|zie|y|ow|om|ami|ach)?\b'
        return bool(re.search(pattern, cleaned_title))
        
    if cleaned_kw in ("dlug", "dlugi", "dług", "długi"):
        # Matches dług, długi, długu, długiem, długów, długom, długami, długach
        pattern = r'\bdlug(i|u|owi|iem|ow|om|ami|ach)?\b'
        return bool(re.search(pattern, cleaned_title))
        
    if cleaned_kw == "kara":
        # Matches kara, kary, karze, karę, karom, karami, karach, kar
        pattern = r'\bkar(a|y|ze|e|om|ami|ach)?\b'
        return bool(re.search(pattern, cleaned_title))
        
    # For general short keywords (< 5 chars), check exact word matching
    if len(cleaned_kw) < 5:
        pattern = r'\b' + re.escape(cleaned_kw) + r'\b'
        return bool(re.search(pattern, cleaned_title))
        
    # For longer keywords, substring match is safe and covers prefixes/suffixes
    return cleaned_kw in cleaned_title

async def fetch_company_news(company_name: str) -> dict:
    """
    Fetches the 10 latest news articles for the company from Google News RSS.
    Returns a dict with keys:
      - 'news_found': bool (True if any news found)
      - 'articles': list of dicts (title, link, date)
      - 'anomalies': list of dicts (articles indicating potential problems)
    """
    result = {
        "news_found": False,
        "articles": [],
        "anomalies": []
    }
    
    if not company_name or company_name == "---":
        return result
        
    from services.web_verifier import clean_company_name
    cleaned_name = clean_company_name(company_name)
    if not cleaned_name:
        return result
        
    encoded_query = urllib.parse.quote(cleaned_name)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pl&gl=PL&ceid=PL:pl"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=8, headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                entries = feed.entries[:10]
                if entries:
                    result["news_found"] = True
                    for entry in entries:
                        title = entry.get("title", "")
                        link = entry.get("link", "")
                        published = entry.get("published", "")
                        
                        article = {
                            "title": title,
                            "link": link,
                            "published": published
                        }
                        result["articles"].append(article)
                        
                        # Sentiment check
                        cleaned_title = clean_txt(title)
                        for kw in NEGATIVE_KEYWORDS:
                            if matches_negative_keyword(cleaned_title, kw):
                                result["anomalies"].append(article)
                                break
    except Exception as e:
        print(f"Error fetching Google News for {company_name}: {e}")
        
    return result
