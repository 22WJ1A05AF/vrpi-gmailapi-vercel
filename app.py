"""VR PI Group internship automation — Vercel + Gmail API.
Original offer-letter PDF layout and original email HTML/text template are retained.
"""
import os, json, base64, hashlib, logging
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate
from html import escape

import gspread
from fpdf import FPDF
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

COMPANY_NAME = os.getenv("COMPANY_NAME", "VR PI Group of Companies")
START_DATE = os.getenv("START_DATE", "10 November 2026")
DURATION = os.getenv("DURATION", "4 weeks")
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
GMAIL_USER = os.getenv("GMAIL_USER", "vrpigroupoftechnology@gmail.com")
GMAIL_CLIENT_ID = os.environ["GMAIL_CLIENT_ID"]
GMAIL_CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
GMAIL_REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vrpi")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_sheet():
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
    # Keep the same output columns used by the original spreadsheet automation.
    now_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    pdf_text = f"Delivered via Email ({pdf_filename})" if pdf_filename else ""
    ws.update_cell(row_index, 18, status)
    ws.update_cell(row_index, 19, pdf_text)
    ws.update_cell(row_index, 20, now_time)
    ws.update_cell(row_index, 21, note)


def clean_pdf_text(text):
    """Sanitizes text to ASCII to prevent font crashes on Helvetica."""
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
    pdf.set_text_color(255, 87, 34)  # Orange
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

    # 1. Subject that passes Google AI NLP filter (Zero promotional flags)
    msg["Subject"] = f"Internship Documentation: {domain} - {c['COMPANY_NAME']} [{aid}]"
    msg["From"] = f"VR PI Talent Acquisition <{c['FROM_EMAIL']}>"
    msg["To"] = to_email
    msg["Reply-To"] = c["FROM_EMAIL"]
    msg["Date"] = formatdate(localtime=True)

    # 2. Authentic Corporate Message (No bulk mail markers)
    body_text = (
        f"Dear {name},\n\n"
        f"Thank you for registering for the {domain} internship track at {c['COMPANY_NAME']}.\n\n"
        f"We have verified your application details:\n"
        f"• Candidate Name: {name}\n"
        f"• Reference ID: {aid}\n"
        f"• Assigned Track: {domain}\n"
        f"• Commencement Date: {c['START_DATE']}\n"
        f"• Duration: {c['DURATION']}\n\n"
        f"Your official Internship Offer Letter has been issued and is attached as a PDF to this email.\n\n"
        f"ACTION REQUIRED: Please reply directly to this email confirming 'I accept' to confirm your enrollment.\n\n"
        f"Warm regards,\n"
        f"HR & Talent Acquisition Team\n"
        f"{c['COMPANY_NAME']}\n"
        f"Website: https://thevrpigroup.com/about"
    )
    msg.set_content(body_text)

    # 3. Clean, Minimalist HTML (Bypasses SpamAssassin & Gmail Promo Filters)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; padding: 15px;">
      <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 25px;">
        
        <p style="font-size: 15px; margin-top: 0;">Dear <strong>{escape(name)}</strong>,</p>
        
        <p style="font-size: 14px; color: #334155;">
          Thank you for applying to <strong>{escape(c['COMPANY_NAME'])}</strong>. We have verified your registration for the <strong>{escape(domain)}</strong> internship track.
        </p>

        <div style="background-color: #f8fafc; border-left: 4px solid #ea580c; padding: 12px 16px; margin: 18px 0; font-size: 13.5px;">
          <p style="margin: 3px 0;"><strong>Reference ID:</strong> {aid}</p>
          <p style="margin: 3px 0;"><strong>Domain Track:</strong> {escape(domain)}</p>
          <p style="margin: 3px 0;"><strong>Start Date:</strong> {c['START_DATE']}</p>
          <p style="margin: 3px 0;"><strong>Duration:</strong> {c['DURATION']}</p>
        </div>

        <p style="font-size: 14px; color: #334155;">
          Your formal <strong>Internship Offer Letter</strong> is attached to this email as a PDF document. Please review the program specifications and terms.
        </p>

        <div style="background-color: #fff7ed; border: 1px solid #fed7aa; border-radius: 4px; padding: 10px 14px; margin: 18px 0; font-size: 13px; color: #9a3412;">
          <strong>Action Required:</strong> Please reply directly to this email with <em>"I accept"</em> to confirm your onboarding.
        </div>

        <p style="margin-top: 25px; font-size: 13px; color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 15px;">
          Warm regards,<br/>
          <strong>HR &amp; Talent Acquisition Team</strong><br/>
          {escape(c['COMPANY_NAME'])}<br/>
          <a href="https://thevrpigroup.com/about" style="color: #ea580c; text-decoration: none;">thevrpigroup.com</a>
        </p>
      </div>
    </body>
    </html>
    """
    msg.add_alternative(html_content, subtype="html")

    # 4. Attach PDF
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=f"Internship_Offer_{aid}.pdf")


    # Send using Gmail API (OAuth 2.0), authenticated as the old Gmail account.
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8").rstrip("=")
    service = get_gmail_service()
    result = service.users().messages().send(
        userId="me", body={"raw": raw_message}
    ).execute()
    return result.get("id", "")


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
            # Mark before sending so overlapping requests do not normally re-send the same row.
            update_sheet_cell(ws, row_index, "PROCESSING", "Preparing offer letter.", "")
            pdf_bytes = create_offer_pdf(aid, name, recipient, domain)
            message_id = send_offer_email(name, recipient, aid, domain, pdf_bytes)
            update_sheet_cell(
                ws, row_index, "SENT",
                f"Accepted by Gmail API; message ID: {message_id}. This does not confirm inbox placement.",
                f"Internship_Offer_{aid}.pdf"
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
