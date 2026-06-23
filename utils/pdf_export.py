import os
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from urllib.parse import urlparse

def strip_polish_chars(text: str) -> str:
    """Replaces Polish characters with their ASCII equivalents to prevent rendering issues in ReportLab."""
    if not isinstance(text, str):
        return text
    mapping = {
        'ą': 'a', 'Ą': 'A',
        'ć': 'c', 'Ć': 'C',
        'ę': 'e', 'Ę': 'E',
        'ł': 'l', 'Ł': 'L',
        'ń': 'n', 'Ń': 'N',
        'ó': 'o', 'Ó': 'O',
        'ś': 's', 'Ś': 'S',
        'ź': 'z', 'Ź': 'Z',
        'ż': 'z', 'Ż': 'Z'
    }
    for pol, eng in mapping.items():
        text = text.replace(pol, eng)
    return text

def P(text: str, style: ParagraphStyle) -> Paragraph:
    """Wrapper to automatically strip Polish characters before rendering a Paragraph."""
    return Paragraph(strip_polish_chars(text), style)

def export_results_pdf(results, path: str) -> None:
    """Generates a professional, detailed PDF report of verified contractors, free of Polish characters."""
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom color palette (sleek dark blue theme)
    PRIMARY_COLOR = colors.HexColor("#1A365D")
    SECONDARY_COLOR = colors.HexColor("#2B6CB0")
    TEXT_COLOR = colors.HexColor("#2D3748")
    BG_LIGHT = colors.HexColor("#F7FAFC")
    BORDER_COLOR = colors.HexColor("#E2E8F0")
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=PRIMARY_COLOR,
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#718096"),
        spaceAfter=20
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBodyText',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    justification_style = ParagraphStyle(
        'JustificationText',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    story = []
    
    # Title & Metadata (Cleaned of Polish characters)
    story.append(P("Vato - Raport Weryfikacji Wiarygodnosci Kontrahentow", title_style))
    story.append(P(f"Wygenerowano dnia: {date.today().isoformat()} | Narzedzie audytorskie Vato", subtitle_style))
    story.append(Spacer(1, 10))
    
    for idx, contractor in enumerate(results):
        if idx > 0:
            story.append(Spacer(1, 20))
            
        has_scoring_dict = hasattr(contractor, 'scoring') and isinstance(contractor.scoring, dict)
        
        nip = getattr(contractor, 'nip', '---')
        name = getattr(contractor, 'legal_name', '---') if hasattr(contractor, 'legal_name') else '---'
        country = getattr(contractor, 'country_code', 'PL') if hasattr(contractor, 'country_code') else 'PL'
        
        # Section Heading
        story.append(P(f"Audyt podmiotu: {name} (NIP: {nip}, Kraj: {country})", h2_style))
        
        # 1. Gather Registry Data
        status_prawny = getattr(contractor, 'status_prawny', 'NIEZNANY')
        status_vat = getattr(contractor, 'status_vat', 'NIEZNANY')
        whitelist = "TAK" if getattr(contractor, 'rachunek_na_bialej_liscie', False) else "NIE"
        cap = getattr(contractor, 'share_capital', None)
        share_capital = f"{cap:,.2f} PLN" if cap is not None else "BRAK DANYCH"
        bailiff = "TAK" if getattr(contractor, 'has_bailiff_proceedings', False) else "NIE"
        if getattr(contractor, 'has_bailiff_proceedings', None) is None:
            bailiff = "BRAK DANYCH"
            
        # 2. Gather Digital Footprint (Scrapper_1)
        website = getattr(contractor, 'website_url', None) or "NIE ODNALEZIONO"
        ssl = "BEZPIECZNE (HTTPS)" if getattr(contractor, 'ssl_valid', False) else "BRAK SZYFROWANIA / BLAD SSL"
        
        age = getattr(contractor, 'domain_age_days', None)
        domain_age = f"{age} dni (~{round(age/365, 1)} lat)" if age is not None else "BRAK DANYCH"
        
        posts = getattr(contractor, 'days_since_last_post', None)
        activity = f"Ostatni wpis {posts} dni temu" if posts is not None else "BRAK AKTYWNOSCI / BRAK RSS"
        
        nip_match = "TAK (Potwierdzono)" if getattr(contractor, 'website_nip_matched', False) else "NIE (Brak zgodnosci)"
        
        # 3. Gather Scoring Data
        if has_scoring_dict:
            score = f"{contractor.scoring.get('total_score', 0)} / 100"
            risk = contractor.scoring.get('risk_level', 'NIEZNANE')
            justifications = contractor.scoring.get('justifications', [])
        elif hasattr(contractor, 'total'):
            score = f"{contractor.total} / 40"
            risk = getattr(contractor, 'risk_level', None)
            risk = risk.value if risk else 'NIEZNANE'
            justifications = getattr(contractor, 'details', [])
        else:
            score = "BRAK KONCOWEGO WYNIKU"
            risk = "NIEZNANE"
            justifications = []
            
        # Table of details
        data_table = [
            [
                P("<b>Dane rejestrowe (KRS/CEIDG)</b>", bold_body_style), "",
                P("<b>Wiarygodnosc Cyfrowa (WWW/SSL)</b>", bold_body_style), ""
            ],
            [
                P("Status prawny:", body_style), P(status_prawny, body_style),
                P("Strona internetowa:", body_style), P(website, body_style)
            ],
            [
                P("Status VAT:", body_style), P(status_vat, body_style),
                P("Szyfrowanie SSL/TLS:", body_style), P(ssl, body_style)
            ],
            [
                P("Biala Lista bankow:", body_style), P(whitelist, body_style),
                P("Wiek domeny:", body_style), P(domain_age, body_style)
            ],
            [
                P("Kapital zakladowy:", body_style), P(share_capital, body_style),
                P("Aktywnosc publikacji:", body_style), P(activity, body_style)
            ],
            [
                P("Postep. komornicze:", body_style), P(bailiff, body_style),
                P("Zgodnosc NIP na stronie:", body_style), P(nip_match, body_style)
            ],
            [
                P("<b>Wynik Scoringu:</b>", bold_body_style), P(f"<b>{score} pkt</b>", bold_body_style),
                P("<b>Rekomendacja ryzyka:</b>", bold_body_style), P(f"<b>{risk}</b>", bold_body_style)
            ]
        ]
        
        # Table styling
        t = Table(data_table, colWidths=[120, 140, 120, 140])
        t.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (3, 0), BG_LIGHT),
            ('BACKGROUND', (0, 6), (3, 6), BG_LIGHT),
            ('LINEBELOW', (0, 0), (3, 0), 1, SECONDARY_COLOR),
            ('LINEABOVE', (0, 6), (3, 6), 1, SECONDARY_COLOR),
            ('INNERGRID', (0, 0), (3, 6), 0.5, BORDER_COLOR),
            ('BOX', (0, 0), (3, 6), 1, PRIMARY_COLOR),
            ('TOPPADDING', (0, 0), (3, 6), 5),
            ('BOTTOMPADDING', (0, 0), (3, 6), 5),
            ('VALIGN', (0, 0), (3, 6), 'MIDDLE'),
        ]))
        
        story.append(t)
        story.append(Spacer(1, 10))
        
        # 4. Print Justifications
        if justifications:
            story.append(P("<b>Uzasadnienie wyniku (Analiza ryzyka):</b>", bold_body_style))
            story.append(Spacer(1, 4))
            for j in justifications:
                story.append(P(f"• {j}", justification_style))
                
        # Draw line separator between contractors
        story.append(Spacer(1, 10))
        line_table = Table([[""]], colWidths=[520])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0)
        ]))
        story.append(line_table)
        
    doc.build(story)
