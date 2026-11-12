"""VR PI Group internship automation — Vercel + Gmail API.
Includes clean PDF offer-letter generation and anti-spam humanized email formatting.
"""
import os
import json
import base64
import hashlib
import logging
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from html import escape

import gspread
from fpdf import FPDF
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Environment Variables & Configuration
COMPANY_NAME = os.getenv("COMPANY_NAME", "VR PI Group of Companies")
START_DATE = os.getenv("START_DATE", "10 November 2026")
DURATION = os.getenv("DURATION", "4 weeks")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
GMAIL_USER = os.getenv("GMAIL_USER", "vrpigroupoftechnology@gmail.com")
GMAIL_CLIENT_ID = os.environ.get("GMAIL_CLIENT_ID", "")
GMAIL_CLIENT_SECRET = os.environ.get("GMAIL_CLIENT_SECRET", "")
GMAIL_REFRESH_TOKEN = os.environ.get("GMAIL_REFRESH_TOKEN", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vrpi")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_sheet():
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is missing.")
    info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
    gc = gspread.service_account_from_dict(info)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    return spreadsheet.get_worksheet(0)


def get_gmail_service():
    creds = Credentials(
        token=None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def update_sheet_cell(ws, row_index, status, note, pdf_filename):
    now_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    pdf_text = f"Delivered via Email ({pdf_filename})" if pdf_filename else ""
    ws.update_cell(row_index, 18, status)
    ws.update_cell(row_index, 19, pdf_text)
    ws.update_cell(row_index, 20, now_time)
    ws.update_cell(row_index, 21, note)


def clean_pdf_text(text):
    """Sanitizes text to ASCII/Latin-1 to prevent font crashes on Helvetica."""
    if not text:
        return ""
    replacements = {
        "•": "-", "—": "-", "–": "-", "’": "'", "‘": "'",
        "“": '"', "”": '"', "…": "...", "₹": "Rs.", "\xa0": " "
    }
    s = str(text)
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


class FormalOfferPDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_draw_color(226, 232, 240)
        self.line(14, 283, 196, 283)
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(148, 163, 184)
        self.cell(0, 8, "VR PI Group of Companies - Official Document | Candidate Confidential", align="C")


def create_offer_pdf(aid, name, to_email, domain):
    pdf = FormalOfferPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    c_name = clean_pdf_text(name)
    c_domain = clean_pdf_text(domain)
    c_email = clean_pdf_text(to_email)

    # 1. TOP LETTERHEAD
    pdf.set_xy(14, 12)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 54, 93)  # Corporate Navy
    pdf.cell(120, 8, clean_pdf_text(COMPANY_NAME.upper()))

    # Clickable Company Website Link
    pdf.set_xy(14, 20)
    pdf.set_font("Helvetica", "U", 8.5)
    pdf.set_text_color(37, 99, 235)  # Link Blue
    pdf.cell(120, 4, "https://thevrpigroup.com/about", link="https://thevrpigroup.com/about")

    # Date and Reference Block (Right Aligned)
    pdf.set_xy(135, 12)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(45, 55, 72)
    pdf.cell(61, 5, f"Date: {datetime.now().strftime('%d/%m/%Y')}", align="R")

    pdf.set_xy(135, 18)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(61, 5, f"Ref: {aid}", align="R")

    # Divider Line
    pdf.set_draw_color(255, 87, 34)  # Orange Accent Line
    pdf.set_line_width(0.8)
    pdf.line(14, 27, 196, 27)

    # 2. DOCUMENT TITLE
    pdf.set_xy(14, 32)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(182, 6, "INTERNSHIP OFFER LETTER", align="C")
    pdf.ln(8)

    # 3. RECIPIENT DETAILS & SALUTATION
    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(45, 55, 72)
    pdf.cell(182, 4.5, f"To: {c_name}")
    pdf.ln(4.5)

    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(182, 4, f"Email: {c_email}")
    pdf.ln(6)

    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(45, 55, 72)
    pdf.cell(182, 5, f"Dear {c_name},")
    pdf.ln(5.5)

    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 8.8)
    pdf.set_text_color(51, 65, 85)
    intro_text = (
        f"We are delighted to extend this formal offer of an internship with {COMPANY_NAME}. "
        f"Based on your profile and technical evaluation, you have been selected for the {c_domain} track. "
        f"We are confident that this opportunity will provide you with extensive hands-on industry exposure and mentorship."
    )
    pdf.multi_cell(182, 4.4, intro_text)

    # 4. OFFER PARTICULARS TABLE
    pdf.ln(3)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(182, 5, "OFFER DETAILS")
    pdf.ln(5.5)

    specs = [
        ("Candidate Name", c_name),
        ("Application ID", aid),
        ("Internship Domain Track", c_domain),
        ("Commencement Date", START_DATE),
        ("Program Duration", DURATION),
        ("Preferred Mode", "Virtual / Remote"),
        ("Supervising Division", "Technical Engineering & Mentorship Cell")
    ]

    for label, val in specs:
        pdf.set_x(14)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.set_text_color(71, 85, 105)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(50, 5.3, f"  {label}", border=1, fill=True)

        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B" if label == "Internship Domain Track" else "", 8)
        pdf.cell(127, 5.3, f"  {val}", border=1, fill=True)
        pdf.ln(5.3)

    # 5. TERMS & GUIDELINES
    pdf.ln(2.5)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(182, 5, "TERMS & CONDITIONS OF ENGAGEMENT")
    pdf.ln(5)

    terms = [
        "1. Project Deliverables: You are required to complete all assigned technical modules and submit project milestones on schedule.",
        "2. Confidentiality: You agree to uphold professional integrity and maintain strict confidentiality regarding all company workflows and source code.",
        "3. Verification & Certification: A verified Certificate of Internship will be awarded upon successful project evaluation and mentor approval.",
        "4. Onboarding: Technical setup and project allocation details will be delivered to your registered email before the commencement date."
    ]

    pdf.set_font("Helvetica", "", 7.8)
    pdf.set_text_color(71, 85, 105)
    for term in terms:
        pdf.set_x(14)
        pdf.multi_cell(182, 3.6, term)
        pdf.ln(0.6)

    # Acceptance Notice
    pdf.ln(1.5)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(26, 54, 93)
    pdf.multi_cell(182, 4, f"Please confirm your acceptance by signing below and returning a scanned copy of this letter on or before {START_DATE}.")

    # Formal Closing Statement
    pdf.ln(1)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(182, 4, "We congratulate you on this opportunity, look forward to having you as part of the team, and wish you a successful and rewarding learning experience.")

    # 6. DUAL SIGNATURE BLOCK
    curr_y = pdf.get_y() + 2.5
    pdf.set_draw_color(226, 232, 240)
    pdf.set_fill_color(248, 250, 252)

    # Left: Candidate Acceptance
    pdf.rect(14, curr_y, 88, 25, "DF")
    pdf.set_xy(17, curr_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(82, 4, "CANDIDATE ACCEPTANCE")
    pdf.set_xy(17, curr_y + 6.5)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(82, 4, "I accept the offer and agree to the terms.")
    pdf.set_xy(17, curr_y + 13.5)
    pdf.cell(82, 4, "Signature: __________________________")
    pdf.set_xy(17, curr_y + 18.5)
    pdf.cell(82, 4, f"Date: _____ / _____ / {datetime.now().year}")

    # Right: Company Signatory
    pdf.rect(108, curr_y, 88, 25, "DF")
    pdf.set_xy(111, curr_y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(82, 4, f"FOR {clean_pdf_text(COMPANY_NAME.upper())}")
    pdf.set_xy(111, curr_y + 6.5)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(82, 4, "[DIGITALLY VERIFIED & APPROVED]")
    pdf.set_xy(111, curr_y + 12.5)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(82, 4, "HR & Talent Acquisition Team")
    pdf.set_xy(111, curr_y + 17.5)
    pdf.cell(82, 4, f"Verification Code: {aid}")

    return bytes(pdf.output())


def send_offer_email(name, to_email, aid, domain, pdf_bytes):
    c = {"COMPANY_NAME": COMPANY_NAME, "START_DATE": START_DATE, "DURATION": DURATION, "FROM_EMAIL": GMAIL_USER}

    msg = EmailMessage()
    first_name = name.split()[0] if name else "Candidate"

    # 1. Human subject line (breaks spam hash filters)
    msg["Subject"] = f"Your internship offer with {c['COMPANY_NAME']} - {domain}"
    msg["From"] = f"VR PI Talent Acquisition <{c['FROM_EMAIL']}>"
    msg["To"] = to_email
    msg["Reply-To"] = c["FROM_EMAIL"]
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="gmail.com")

    # 2. Conversational plain text body
    body_text = (
        f"Hi {first_name},\n\n"
        f"Thank you for completing your application. We are pleased to offer you an internship position in our {domain} track.\n\n"
        f"Program Overview:\n"
        f"- Candidate: {name}\n"
        f"- Role: {domain} Intern\n"
        f"- Start Date: {c['START_DATE']}\n"
        f"- Duration: {c['DURATION']}\n"
        f"- Reference ID: {aid}\n\n"
        f"Your official offer letter is attached as a PDF. Please review it and reply directly to this email to confirm your acceptance.\n\n"
        f"If you have any questions before the start date, please feel free to reach out to us here.\n\n"
        f"Best regards,\n"
        f"Talent Acquisition Team\n"
        f"{c['COMPANY_NAME']}\n"
        f"vrpigroupoftechnology@gmail.com"
    )
    msg.set_content(body_text)

    # 3. Clean, lightweight HTML (looks authentic and avoids promo/spam blocks)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.6;">
      <p>Hi {escape(first_name)},</p>
      
      <p>Thank you for completing your application. We are pleased to offer you an internship position in our <strong>{escape(domain)}</strong> track.</p>
      
      <p><strong>Program Overview:</strong><br/>
      &bull; <strong>Candidate:</strong> {escape(name)}<br/>
      &bull; <strong>Role:</strong> {escape(domain)} Intern<br/>
      &bull; <strong>Start Date:</strong> {c['START_DATE']}<br/>
      &bull; <strong>Duration:</strong> {c['DURATION']}<br/>
      &bull; <strong>Reference ID:</strong> {aid}</p>

      <p>Your official offer letter is attached as a PDF. Please review it and reply directly to this email to confirm your acceptance.</p>

      <p>If you have any questions before the start date, please feel free to reach out to us here.</p>

      <p style="margin-top: 25px; color: #555555;">
        Best regards,<br/>
        <strong>Talent Acquisition Team</strong><br/>
        {escape(c['COMPANY_NAME'])}<br/>
        <span style="font-size: 12px; color: #777777;">vrpigroupoftechnology@gmail.com</span>
      </p>
    </body>
    </html>
    """
    msg.add_alternative(html_content, subtype="html")

    # 4. Attach PDF with clean, personalized filename
    pdf_filename = f"{first_name}_Internship_Offer.pdf"
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_filename
    )

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8").rstrip("=")
    service = get_gmail_service()
    result = service.users().messages().send(
        userId="me", body={"raw": raw_message}
    ).execute()
    return result.get("id", ""), pdf_filename


def process_pending_rows(max_rows=5):
    ws = get_sheet()
    rows = ws.get_all_values()
    if len(rows) < 2:
        return {"processed": 0, "message": "No candidate rows found."}

    headers = [h.strip().lower() for h in rows[0]]
    col_id = headers.index("application id") if "application id" in headers else 1
    col_name = headers.index("full name") if "full name" in headers else 2
    col_email = headers.index("email address") if "email address" in headers else 3
    col_domain = headers.index("internship domain track") if "internship domain track" in headers else 7
    col_sent = headers.index("letter sent") if "letter sent" in headers else 17

    processed = 0
    results = []
    for row_index, row in enumerate(rows[1:], start=2):
        if processed >= max_rows:
            break
        if len(row) <= max(col_id, col_name, col_email, col_domain, col_sent):
            continue
        status = row[col_sent].strip().upper()
        if status in {"SENT", "TEST SENT", "PROCESSED", "PROCESSING"}:
            continue

        name = row[col_name].strip()
        recipient = row[col_email].strip()
        aid = row[col_id].strip() or f"VRPI-INT-{hashlib.sha1((recipient + name).encode()).hexdigest()[:6].upper()}"
        domain = row[col_domain].strip() or "Internship Track"

        if not name or not recipient or "@" not in recipient:
            update_sheet_cell(ws, row_index, "FAILED", "Missing or invalid candidate name/email.", "")
            continue

        try:
            update_sheet_cell(ws, row_index, "PROCESSING", "Preparing offer letter.", "")
            pdf_bytes = create_offer_pdf(aid, name, recipient, domain)
            message_id, pdf_filename = send_offer_email(name, recipient, aid, domain, pdf_bytes)
            update_sheet_cell(
                ws, row_index, "SENT",
                f"Accepted by Gmail API; message ID: {message_id}.",
                pdf_filename
            )
            results.append({"row": row_index, "status": "SENT", "application_id": aid, "gmail_message_id": message_id})
            processed += 1
        except Exception as exc:
            log.exception("Failed processing sheet row %s", row_index)
            try:
                update_sheet_cell(ws, row_index, "FAILED", str(exc)[:500], "")
            except Exception:
                log.exception("Could not update failure status for row %s", row_index)
            results.append({"row": row_index, "status": "FAILED", "error": str(exc)[:300]})

    return {"processed": processed, "results": results}