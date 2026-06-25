import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from services.i18n import t

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
LOGO_PATH = os.path.join(STATIC_DIR, "vato_black.png")

def _draw_logo(canvas, doc):
    """Draws the company logo in the top-right corner of the page with the correct aspect ratio."""
    if not os.path.exists(LOGO_PATH):
        return
    logo_w = 140
    # Keep the aspect ratio of the image (2048 x 1102) to prevent stretching and huge empty bounding box
    logo_h = int(logo_w * 1102 / 2048)  # ~75 pt
    x = doc.pagesize[0] - doc.rightMargin - logo_w
    y = doc.pagesize[1] - doc.topMargin - logo_h
    canvas.saveState()
    canvas.drawImage(LOGO_PATH, x, y, width=logo_w, height=logo_h, preserveAspectRatio=True, mask="auto")
    canvas.restoreState()

def strip_diacritics(text: str) -> str:
    """Replaces diacritic characters (Polish, German) with ASCII equivalents for ReportLab rendering."""
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
        'ż': 'z', 'Ż': 'Z',
        'ä': 'a', 'Ä': 'A',
        'ö': 'o', 'Ö': 'O',
        'ü': 'u', 'Ü': 'U',
        'ß': 'ss',
    }
    for char, replacement in mapping.items():
        text = text.replace(char, replacement)
    return text

strip_polish_chars = strip_diacritics

def _translate_legal_status(raw: str) -> str:
    upper = (raw or "").strip().upper()
    if upper in ("ACTIVE", "AKTYWNA", "AKTYWNY"):
        return t("pdf.status_active")
    if upper in ("SUSPENDED", "ZAWIESZONA", "ZAWIESZONY"):
        return t("pdf.status_suspended")
    if upper in ("CLOSED", "WYKREŚLONA", "WYKREŚLONY", "WYKRESLONA", "WYKRESLONY"):
        return t("pdf.status_closed")
    if upper == "LIQUIDATION" or "LIKWIDACJ" in upper:
        return t("pdf.status_liquidation")
    if upper == "BANKRUPTCY" or "UPADŁ" in upper or "UPADL" in upper:
        return t("pdf.status_bankruptcy")
    if upper in ("NIEZNANY", "UNKNOWN", ""):
        return t("pdf.unknown")
    return raw

def _translate_vat_status(raw: str) -> str:
    upper = (raw or "").strip().upper()
    if "CZYNNY" in upper or upper == "ACTIVE":
        return t("pdf.vat_active")
    if "ZWOLNIONY" in upper or upper == "EXEMPT":
        return t("pdf.vat_exempt")
    if "WYKREŚL" in upper or "WYKRESL" in upper or "REMOVED" in upper or "NIEZAREJESTR" in upper:
        return t("pdf.vat_removed")
    if upper in ("NIEZNANY", "UNKNOWN", ""):
        return t("pdf.unknown")
    return raw

def P(text: str, style: ParagraphStyle) -> Paragraph:
    """Wrapper to automatically strip diacritics before rendering a Paragraph."""
    return Paragraph(strip_diacritics(text), style)

def export_results_pdf(results, path: str) -> None:
    """Generates a professional, detailed PDF report of verified contractors."""
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    PRIMARY_COLOR = colors.HexColor("#1A365D")
    SECONDARY_COLOR = colors.HexColor("#2B6CB0")
    TEXT_COLOR = colors.HexColor("#2D3748")
    BG_LIGHT = colors.HexColor("#F7FAFC")
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=PRIMARY_COLOR,
        spaceAfter=5,
        rightIndent=160  # Protects the logo area from horizontal overlap
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#718096"),
        spaceAfter=12,
        rightIndent=160  # Protects the logo area from horizontal overlap
    )

    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceBefore=8,
        spaceAfter=6,
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

    story = []

    story.append(P(t("pdf.title"), title_style))
    story.append(P(t("pdf.subtitle", date=date.today().isoformat()), subtitle_style))
    story.append(Spacer(1, 40))  # Increased spacing to create a vertical protection zone below the logo

    for idx, contractor in enumerate(results):
        if idx > 0:
            story.append(Spacer(1, 20))

        has_scoring_dict = hasattr(contractor, 'scoring') and isinstance(contractor.scoring, dict)

        nip = getattr(contractor, 'nip', '---')
        name = getattr(contractor, 'legal_name', '---') if hasattr(contractor, 'legal_name') else '---'
        country = getattr(contractor, 'country_code', 'PL') if hasattr(contractor, 'country_code') else 'PL'

        story.append(P(t("pdf.entity_audit", name=name, nip=nip, country=country), h2_style))

        status_prawny = _translate_legal_status(getattr(contractor, 'status_prawny', ''))
        status_vat = _translate_vat_status(getattr(contractor, 'status_vat', ''))
        whitelist = t("pdf.yes") if getattr(contractor, 'rachunek_na_bialej_liscie', False) else t("pdf.no")
        cap = getattr(contractor, 'share_capital', None)
        share_capital = f"{cap:,.2f} PLN" if cap is not None else t("pdf.no_data")
        bailiff = t("pdf.yes") if getattr(contractor, 'has_bailiff_proceedings', False) else t("pdf.no")
        if getattr(contractor, 'has_bailiff_proceedings', None) is None:
            bailiff = t("pdf.no_data")

        website = getattr(contractor, 'website_url', None) or t("pdf.not_found")
        ssl = t("pdf.ssl_ok") if getattr(contractor, 'ssl_valid', False) else t("pdf.ssl_bad")

        age = getattr(contractor, 'domain_age_days', None)
        domain_age = t("pdf.domain_age_fmt", days=age, years=round(age / 365, 1)) if age is not None else t("pdf.no_data")

        posts = getattr(contractor, 'days_since_last_post', None)
        activity = t("pdf.last_post", days=posts) if posts is not None else t("pdf.no_activity")

        nip_match = t("pdf.nip_match_yes") if getattr(contractor, 'website_nip_matched', False) else t("pdf.nip_match_no")

        if has_scoring_dict:
            total_score_val = contractor.scoring.get('total_score', 0)
            score = f"{total_score_val} / 100"
            risk = contractor.scoring.get('risk_level', t("pdf.unknown"))
            color_code = contractor.scoring.get('color_code', 'yellow')
            justifications = contractor.scoring.get('justifications', [])
        elif hasattr(contractor, 'total'):
            total_score_val = contractor.total
            score = f"{total_score_val} / 40"
            risk = getattr(contractor, 'risk_level', None)
            risk = risk.value if risk else t("pdf.unknown")
            color_code = 'yellow'
            justifications = getattr(contractor, 'details', [])
        else:
            total_score_val = 0
            score = t("pdf.no_score")
            risk = t("pdf.unknown")
            color_code = 'yellow'
            justifications = []

        if color_code == 'green':
            score_bg = colors.HexColor("#E6F4EA")
            score_fg = colors.HexColor("#1E7E34")
        elif color_code == 'red':
            score_bg = colors.HexColor("#FDECEA")
            score_fg = colors.HexColor("#C62828")
        else:
            score_bg = colors.HexColor("#FFF3E0")
            score_fg = colors.HexColor("#E65100")

        score_style = ParagraphStyle('ScoreCell', parent=bold_body_style, textColor=score_fg, fontSize=10)
        header_cell_style = ParagraphStyle('HeaderCell', parent=bold_body_style, textColor=colors.white, fontSize=9)

        data_table = [
            [
                P(f"<b>{t('pdf.registry_header')}</b>", header_cell_style), "",
                P(f"<b>{t('pdf.digital_header')}</b>", header_cell_style), ""
            ],
            [
                P(t("pdf.legal_status"), body_style), P(status_prawny, body_style),
                P(t("pdf.website"), body_style), P(website, body_style)
            ],
            [
                P(t("pdf.vat_status"), body_style), P(status_vat, body_style),
                P(t("pdf.ssl"), body_style), P(ssl, body_style)
            ],
            [
                P(t("pdf.whitelist"), body_style), P(whitelist, body_style),
                P(t("pdf.domain_age"), body_style), P(domain_age, body_style)
            ],
            [
                P(t("pdf.share_capital"), body_style), P(share_capital, body_style),
                P(t("pdf.activity"), body_style), P(activity, body_style)
            ],
            [
                P(t("pdf.bailiff"), body_style), P(bailiff, body_style),
                P(t("pdf.nip_match"), body_style), P(nip_match, body_style)
            ],
            [
                P(f"<b>{t('pdf.score')}</b>", score_style), P(f"<b>{score}</b>", score_style),
                P(f"<b>{t('pdf.risk')}</b>", score_style), P(f"<b>{risk}</b>", score_style)
            ]
        ]

        tbl = Table(data_table, colWidths=[130, 130, 130, 125])
        tbl.setStyle(TableStyle([
            ('SPAN', (0, 0), (1, 0)),
            ('SPAN', (2, 0), (3, 0)),
            ('BACKGROUND', (0, 0), (3, 0), PRIMARY_COLOR),
            ('BACKGROUND', (0, 6), (3, 6), score_bg),
            ('LINEBELOW', (0, 0), (3, 0), 1, SECONDARY_COLOR),
            ('LINEABOVE', (0, 6), (3, 6), 2, score_fg),
            ('ROWBACKGROUNDS', (0, 1), (3, 5), [colors.white, BG_LIGHT]),
            ('INNERGRID', (0, 0), (3, 6), 0.5, BORDER_COLOR),
            ('BOX', (0, 0), (3, 6), 1, PRIMARY_COLOR),
            ('TOPPADDING', (0, 0), (3, 6), 4),
            ('BOTTOMPADDING', (0, 0), (3, 6), 4),
            ('LEFTPADDING', (0, 0), (3, 6), 8),
            ('VALIGN', (0, 0), (3, 6), 'MIDDLE'),
        ]))

        story.append(tbl)
        story.append(Spacer(1, 6))

        if justifications:
            just_header_style = ParagraphStyle(
                'JustHeader',
                parent=bold_body_style,
                textColor=colors.white,
                fontSize=11,
                leading=16,
            )
            just_item_style = ParagraphStyle(
                'JustItem',
                parent=body_style,
                leftIndent=12,
                firstLineIndent=-12,
                spaceAfter=2,
                fontSize=9,
                leading=13,
                textColor=TEXT_COLOR,
            )
            box_rows = [[P(f"<b>{t('email.analysis_title')}</b>", just_header_style)]]
            for j in justifications:
                box_rows.append([P(f"• {j}", just_item_style)])

            box_table = Table(box_rows, colWidths=[520])
            box_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
                ('LINEBELOW', (0, 0), (-1, 0), 2, SECONDARY_COLOR),
                ('LINEBEFORE', (0, 0), (0, -1), 4, SECONDARY_COLOR),
                ('BOX', (0, 0), (-1, -1), 1, PRIMARY_COLOR),
                ('INNERGRID', (0, 1), (-1, -1), 0.5, BORDER_COLOR),
                ('TOPPADDING', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 14),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
            ]))
            story.append(box_table)

        story.append(Spacer(1, 10))
        line_table = Table([[""]], colWidths=[520])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0)
        ]))
        story.append(line_table)

    doc.build(story, onFirstPage=_draw_logo, onLaterPages=lambda canvas, doc: None)
