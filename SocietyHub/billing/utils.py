import io
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

def number_to_words_inr(number):
    """Converter for Indian Currency amounts into words."""
    try:
        n = int(round(float(number)))
        def num999(n):
            ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
                    "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
            tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
            s = ""
            if n >= 100:
                s += ones[n // 100] + " Hundred "
                n %= 100
            if n >= 20:
                s += tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")
            elif n > 0:
                s += ones[n]
            return s.strip()

        if n == 0:
            return "Zero Rupees Only"
        
        crore = n // 10000000
        n %= 10000000
        lakh = n // 100000
        n %= 100000
        thousand = n // 1000
        n %= 1000
        remainder = n

        res = []
        if crore > 0:
            res.append(num999(crore) + " Crore")
        if lakh > 0:
            res.append(num999(lakh) + " Lakh")
        if thousand > 0:
            res.append(num999(thousand) + " Thousand")
        if remainder > 0:
            res.append(num999(remainder))
        
        return "Rupees " + " ".join(res).strip() + " Only"
    except Exception:
        return f"Rupees {number} Only"


from reportlab.pdfgen import canvas as pdf_canvas

def draw_society_watermark(canvas, doc=None, society_name="Housing Society"):
    """
    Renders an authentic, translucent Maharashtra CHS circular watermark emblem
    in the background of the page BEFORE tables and text are drawn.
    Guarantees that the watermark is translucent (alpha=0.08) and never obscures text.
    """
    if not society_name and isinstance(doc, str):
        society_name = doc
    canvas.saveState()
    cx = A4[0] / 2.0
    cy = A4[1] / 2.0

    # Gentle slate color - clearly visible through transparent tables without obscuring text
    wm_color = colors.HexColor('#64748B')
    canvas.setFillColor(wm_color)
    canvas.setStrokeColor(wm_color)

    # CRITICAL: setFillAlpha and setStrokeAlpha MUST be applied AFTER setFillColor/setStrokeColor
    # because setFillColor/setStrokeColor in ReportLab resets the graphics state alpha to 1.0.
    if hasattr(canvas, 'setFillAlpha'):
        canvas.setFillAlpha(0.08)
    if hasattr(canvas, 'setStrokeAlpha'):
        canvas.setStrokeAlpha(0.08)

    canvas.setLineWidth(1.2)
    canvas.translate(cx, cy)
    canvas.rotate(35)

    # Draw decorative double circular emblem
    canvas.circle(0, 0, 185)
    canvas.circle(0, 0, 177)
    canvas.setLineWidth(0.8)
    canvas.circle(0, 0, 140)

    # Arch text
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawCentredString(0, 155, "★ CO-OPERATIVE HOUSING SOCIETY LTD ★")
    canvas.drawCentredString(0, -165, "★ OFFICIAL MAINTENANCE RECORD ★")

    # Society Name dynamically sized
    raw_name = (society_name or "SOCIETY").upper()
    clean_name = raw_name
    for suffix in [" CO-OPERATIVE HOUSING SOCIETY LTD", " CO-OP HOUSING SOCIETY LTD", " CHS LTD", " CHS"]:
        if clean_name.endswith(suffix):
            clean_name = clean_name[:-len(suffix)].strip()
            break

    if len(clean_name) > 24:
        fsize = 20
    elif len(clean_name) > 16:
        fsize = 24
    else:
        fsize = 30

    canvas.setFont('Helvetica-Bold', fsize)
    canvas.drawCentredString(0, 8, clean_name)

    canvas.setFont('Helvetica-Bold', 9.5)
    canvas.drawCentredString(0, -18, "CO-OP HOUSING SOCIETY")
    canvas.setFont('Helvetica-Oblique', 8)
    canvas.drawCentredString(0, -32, "AUTHENTICATED DOCUMENT")

    canvas.restoreState()


class WatermarkedCanvas(pdf_canvas.Canvas):
    """
    Custom Canvas that ensures page backgrounds and watermarks render cleanly.
    """
    def __init__(self, *args, society_name="Housing Society", **kwargs):
        self.society_watermark_name = society_name
        super().__init__(*args, **kwargs)

    def showPage(self):
        super().showPage()


def get_watermark_canvas_maker(society_name):
    class CanvasMaker(WatermarkedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, society_name=society_name, **kwargs)
    return CanvasMaker


def create_watermark_callback(society_name):
    """Page callback that draws a crisp translucent watermark in the background of each page."""
    def draw_watermark(canvas, doc):
        draw_society_watermark(canvas, doc, society_name=society_name)
    return draw_watermark


def generate_bill_pdf(transaction):
    """
    Generates an authentic Maharashtra Cooperative Housing Society (CHS) 
    Maintenance Bill PDF with complete rate breakdown and Society Watermark.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()

    header_title_style = ParagraphStyle(
        'BillHeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#111827')
    )

    sub_header_style = ParagraphStyle(
        'BillSubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#374151')
    )

    bill_title_style = ParagraphStyle(
        'BillTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#111827')
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#111827')
    )

    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1F2937')
    )

    cell_right_bold = ParagraphStyle(
        'CellRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#111827')
    )

    cell_right = ParagraphStyle(
        'CellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#1F2937')
    )

    society = transaction.society
    society_display = society.display_name if society else "SocietyHub Co-operative Housing Society Ltd"
    society_reg = society.registration_display if society else "MUM-2/WL/HSG/TC/11026/2018-19"
    society_address = society.address_display if society else "LBS Marg, Church Road, Mumbai - 400070"

    profile = getattr(transaction.user, 'profile', None)
    flat_no = f"{profile.wing or 'A'}-{profile.flat_number or '101'}" if profile else "101"
    area_sqft = f"{int(profile.area_sqft)}" if profile and profile.area_sqft else "850"
    user_name = (transaction.user.get_full_name() or transaction.user.username).upper()
    if not user_name.startswith("MR.") and not user_name.startswith("MS.") and not user_name.startswith("MRS."):
        user_name = f"MR. {user_name}"

    bill_no = transaction.bill_number or str(transaction.id + 28)
    bill_date_str = (transaction.bill_date or transaction.created_at.date()).strftime("%d/%m/%Y")
    due_date_str = (transaction.due_date or (transaction.created_at.date() + datetime.timedelta(days=30))).strftime("%d/%m/%Y")
    billing_period = transaction.billing_period or "Monthly Maintenance"

    # Header
    story.append(Paragraph(society_display, header_title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"REG NO: {society_reg}", sub_header_style))
    story.append(Paragraph(society_address, sub_header_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceBefore=2, spaceAfter=8))
    story.append(Paragraph(f"Maintenance Bill for {billing_period}", bill_title_style))
    story.append(Spacer(1, 8))

    # Meta Info Top Table (Left: Flat & Name, Right: Bill No, Bill Date, Due Date)
    meta_data = [
        [
            Paragraph(f"<b>Flat No. {flat_no} (AREA : {area_sqft} SQFT)</b>", cell_bold),
            Paragraph(f"<b>Bill No : {bill_no}</b>", cell_right_bold)
        ],
        [
            Paragraph(f"<b>Name : {user_name}</b>", cell_bold),
            Paragraph(f"<b>Bill Date : {bill_date_str}</b>", cell_right_bold)
        ],
        [
            Paragraph(f"<b>Designation : {profile.flat_name or 'Residential Unit'}</b>" if profile else "", cell_normal),
            Paragraph(f"<b>Due Date : {due_date_str}</b>", cell_right_bold)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[310, 215])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Particulars Table: Exactly formatted with itemized Particulars & Amount columns
    breakdown = transaction.get_breakdown()
    
    # 2-column particulars split or list table
    items_rows = []
    items_rows.append([
        Paragraph("<b>Particulars</b>", cell_bold),
        Paragraph("<b>Amount</b>", cell_right_bold),
        Paragraph("<b>Particulars</b>", cell_bold),
        Paragraph("<b>Amount</b>", cell_right_bold),
    ])

    subtotal = float(transaction.subtotal_amount) if transaction.subtotal_amount else 0.0
    if not subtotal:
        subtotal = sum(float(item.get('amount', 0)) for item in breakdown)
    if not subtotal:
        subtotal = float(transaction.amount)

    # Distribute into 2 pairs per row
    for i in range(0, len(breakdown), 2):
        item1 = breakdown[i]
        p1 = item1.get('particular', '').upper()
        a1 = f"{float(item1.get('amount', 0)):,.2f}"
        
        if i + 1 < len(breakdown):
            item2 = breakdown[i + 1]
            p2 = item2.get('particular', '').upper()
            a2 = f"{float(item2.get('amount', 0)):,.2f}"
        else:
            p2 = ""
            a2 = ""

        items_rows.append([
            Paragraph(p1, cell_normal),
            Paragraph(a1, cell_right),
            Paragraph(p2, cell_normal),
            Paragraph(a2, cell_right)
        ])

    particulars_table = Table(items_rows, colWidths=[185, 75, 185, 80])
    particulars_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(particulars_table)

    # Summary Table: TOTAL, Advance Credit, Arrears, Interest, GRAND TOTAL
    arrears = float(transaction.arrears_amount or 0)
    advance = float(transaction.advance_amount or 0)
    interest = float(transaction.interest_amount or 0)
    grand_total = float(transaction.amount)

    summary_rows = [
        [Paragraph("<b>TOTAL :</b>", cell_right_bold), Paragraph(f"<b>{subtotal:,.2f}</b>", cell_right_bold)],
    ]
    if advance > 0:
        summary_rows.append([
            Paragraph("<b>Less: Advance / Pre-paid Credit :</b>", cell_right_bold), 
            Paragraph(f"-{advance:,.2f}", cell_right)
        ])
    summary_rows.extend([
        [Paragraph("<b>Arrears Amount :</b>", cell_right_bold), Paragraph(f"{arrears:,.2f}", cell_right)],
        [Paragraph("<b>Pending Interest Amount :</b>", cell_right_bold), Paragraph("0.00", cell_right)],
        [Paragraph("<b>Current Interest 21% p.a. on Arrears :</b>", cell_right_bold), Paragraph(f"{interest:,.2f}", cell_right)],
        [Paragraph("<b>GRAND TOTAL PAYABLE :</b>", cell_right_bold), Paragraph(f"<b>Rs. {grand_total:,.2f}</b>", cell_right_bold)],
    ])
    summary_table = Table(summary_rows, colWidths=[420, 105])
    summary_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 6))

    # Amount in Words Box
    words = number_to_words_inr(grand_total)
    words_data = [[Paragraph(f"({words})", cell_bold)]]
    words_table = Table(words_data, colWidths=[525])
    words_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(words_table)
    story.append(Spacer(1, 10))

    # Notes & Committee Footer Section
    bank_notes = society.bank_info_display if society else "Bank: Citizencredit Co-op Bank Ltd, Kurla(W), A/c No: 2090062000018288, IFSC: CCBL0209006"
    notes_text = (
        "<b>NOTES :</b><br/>"
        "1) Please Pay the Bill on or Before Due Date.<br/>"
        "2) Delayed Payment will be Charged Interest @ 21% p.a.<br/>"
        "3) Mention your Flat No. and Mobile No. on Reverse of Cheque / Transaction Reference.<br/>"
        f"4) Payment should be drawn in favour of <b>{society_display}</b>.<br/>"
        f"5) For NEFT/Online Payment: {bank_notes}.<br/>"
        "6) Errors and Omissions are exempted."
    )
    
    footer_data = [
        [
            Paragraph(notes_text, ParagraphStyle('Notes', parent=cell_normal, fontSize=7.5, leading=10.5)),
            Paragraph(f"<b>For {society_display}</b><br/><br/><br/><br/>___________________________<br/><b>Chairman / Secretary / Treasurer</b>", ParagraphStyle('SignBlock', parent=cell_normal, fontSize=8, leading=11, alignment=TA_RIGHT))
        ]
    ]
    footer_table = Table(footer_data, colWidths=[340, 185])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(KeepTogether([footer_table]))

    # Build with background translucent society watermark on every page
    society_raw_name = society.name if society else "SocietyHub"
    def wm_callback(c, d):
        draw_society_watermark(c, d, society_name=society_raw_name)

    canvas_maker = get_watermark_canvas_maker(society_raw_name)
    doc.build(story, canvasmaker=canvas_maker, onFirstPage=wm_callback, onLaterPages=wm_callback)
    buffer.seek(0)
    return buffer


def generate_receipt_pdf(transaction):
    """
    Generates an official Maharashtra Model Bye-Law No. 65 compliant 
    Society Maintenance Receipt in PDF format with Society Watermark.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()

    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1E293B')
    )

    sub_header_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4F6D7A')
    )

    statutory_note_style = ParagraphStyle(
        'StatutoryNote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#64748B')
    )

    meta_label = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )

    meta_value = ParagraphStyle(
        'MetaValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )

    society = transaction.society
    society_display = society.display_name if society else "SocietyHub Co-operative Housing Society Ltd"
    society_reg = society.registration_display if society else "MUM-2/WL/HSG/TC/11026/2018-19"
    society_address = society.address_display if society else "LBS Marg, Church Road, Mumbai - 400070"

    profile = getattr(transaction.user, 'profile', None)
    wing_flat = f"Wing {profile.wing or 'A'}, Flat {profile.flat_number or '101'}" if profile else "N/A"
    area_sqft = f"{int(profile.area_sqft)} sq.ft" if profile and profile.area_sqft else "850 sq.ft"
    resident_role = f"Resident ({profile.get_resident_type_display()})" if profile and hasattr(profile, 'get_resident_type_display') else "Resident"

    # Header section
    story.append(Paragraph(society_display.upper(), header_title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"REG NO: {society_reg} • {society_address.upper()}", sub_header_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("OFFICIAL E-RECEIPT OF MAINTENANCE PAYMENT", statutory_note_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4F6D7A'), spaceBefore=1, spaceAfter=10))

    # Meta Information Table
    receipt_date_str = transaction.updated_at.strftime("%d-%b-%Y, %I:%M %p")
    receipt_no = transaction.receipt_number or f"SH-REC-{transaction.id:04d}"
    tx_id = transaction.razorpay_payment_id or f"TXN-ONLINE-{transaction.id}"

    meta_data = [
        [
            Paragraph("<b>Receipt Number:</b>", meta_label), Paragraph(receipt_no, meta_value),
            Paragraph("<b>Payment Date:</b>", meta_label), Paragraph(receipt_date_str, meta_value)
        ],
        [
            Paragraph("<b>Received From:</b>", meta_label), Paragraph(transaction.user.get_full_name() or transaction.user.username, meta_value),
            Paragraph("<b>Payment Channel:</b>", meta_label), Paragraph("Razorpay Gateway (Verified)", meta_value)
        ],
        [
            Paragraph("<b>Unit / Flat:</b>", meta_label), Paragraph(f"{wing_flat} ({area_sqft})", meta_value),
            Paragraph("<b>Transaction ID:</b>", meta_label), Paragraph(tx_id, meta_value)
        ],
        [
            Paragraph("<b>Billing Period:</b>", meta_label), Paragraph(transaction.billing_period or "Monthly Maintenance", meta_value),
            Paragraph("<b>Payment Status:</b>", meta_label), Paragraph("<font color='#059669'><b>PAID & RECONCILED</b></font>", meta_value)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[95, 165, 100, 165])
    meta_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # Particulars Table Header
    story.append(Paragraph("<b>BREAKDOWN OF RECEIVED MAINTENANCE CHARGES</b>", meta_label))
    story.append(Spacer(1, 5))

    breakdown = transaction.get_breakdown()
    items_data = [
        [
            Paragraph("<b>Sr.</b>", table_header),
            Paragraph("<b>Maintenance Particular & Description</b>", table_header),
            Paragraph("<b>Category</b>", table_header),
            Paragraph("<b>Amount (INR)</b>", table_header),
        ]
    ]

    for idx, item in enumerate(breakdown, 1):
        p_name = item.get('particular', '').upper()
        p_amt = float(item.get('amount', 0))
        items_data.append([
            Paragraph(str(idx), table_cell),
            Paragraph(f"<b>{p_name}</b>", table_cell),
            Paragraph("Maintenance", table_cell),
            Paragraph(f"Rs. {p_amt:,.2f}", table_cell_bold),
        ])

    has_arrears = bool(transaction.arrears_amount and transaction.arrears_amount > 0)
    has_interest = bool(transaction.interest_amount and transaction.interest_amount > 0)

    if has_arrears or has_interest:
        subtotal = float(transaction.subtotal_amount) if transaction.subtotal_amount else sum(float(item.get('amount', 0)) for item in breakdown)
        items_data.append([
            Paragraph("", table_cell),
            Paragraph("<b>Current Assessment Charges Subtotal</b>", table_cell_bold),
            Paragraph("Subtotal", table_cell),
            Paragraph(f"Rs. {subtotal:,.2f}", table_cell_bold),
        ])

    if has_arrears:
        items_data.append([
            Paragraph("+", table_cell_bold),
            Paragraph("<b>PREVIOUS UNPAID ARREARS</b>", table_cell_bold),
            Paragraph("Arrears Dues", table_cell),
            Paragraph(f"Rs. {float(transaction.arrears_amount):,.2f}", table_cell_bold),
        ])

    if has_interest:
        items_data.append([
            Paragraph("+", table_cell_bold),
            Paragraph("<b>INTEREST ON ARREARS (21% P.A.)</b>", table_cell_bold),
            Paragraph("Statutory Interest", table_cell),
            Paragraph(f"Rs. {float(transaction.interest_amount):,.2f}", table_cell_bold),
        ])

    items_data.append([
        Paragraph("", table_cell),
        Paragraph("<b>Total Amount Paid (Reconciled)</b>", table_cell_bold),
        Paragraph("", table_cell),
        Paragraph(f"<b>Rs. {float(transaction.amount):,.2f}</b>", table_cell_bold),
    ])

    items_table = Table(items_data, colWidths=[35, 285, 95, 110])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#475569')),
        ('INNERGRID', (0,0), (-1,-2), 0.5, colors.HexColor('#CBD5E1')),
        ('LINEABOVE', (0,-1), (-1,-1), 1.2, colors.HexColor('#1E293B')),
        ('TOPPADDING', (0,0), (-1,-1), 5.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5.5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 10))

    # Amount in Words Box
    words = number_to_words_inr(transaction.amount)
    words_data = [[Paragraph(f"<b>Amount in Words:</b> <i>{words}</i>", meta_label)]]
    words_table = Table(words_data, colWidths=[525])
    words_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#94A3B8')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(words_table)
    story.append(Spacer(1, 16))

    # Verification & Signatures section
    footer_data = [
        [
            Paragraph("<b>E-Payment Verification:</b><br/><font size='7.5' color='#059669'>✓ Digitally Authenticated & Reconciled</font><br/><font size='7' color='#64748B'>Gateway Signature: " + (transaction.razorpay_signature or "SIG_VERIFIED")[:24] + "...</font>", meta_value),
            Paragraph(f"<b>For {society_display}</b><br/><br/><br/>___________________________<br/><font size='8'><b>Hon. Secretary / Treasurer</b></font>", ParagraphStyle('Sign', parent=meta_value, alignment=TA_RIGHT))
        ]
    ]
    footer_table = Table(footer_data, colWidths=[300, 225])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(KeepTogether([
        footer_table,
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=4),
        Paragraph("<i>This is a computer-generated official payment receipt. No physical signature is required.</i>", statutory_note_style)
    ]))

    # Build with background translucent society watermark on every page
    society_raw_name = society.name if society else "SocietyHub"
    def wm_callback(c, d):
        draw_society_watermark(c, d, society_name=society_raw_name)

    canvas_maker = get_watermark_canvas_maker(society_raw_name)
    doc.build(story, canvasmaker=canvas_maker, onFirstPage=wm_callback, onLaterPages=wm_callback)
    buffer.seek(0)
    return buffer


def get_or_create_schedule_config(society):
    """
    Returns the MaintenanceScheduleConfig for a society, creating customized defaults if not existing.
    Guarantees that different societies receive distinct maintenance schedules tailored to their profile.
    """
    from decimal import Decimal
    from .models import MaintenanceScheduleConfig
    config, created = MaintenanceScheduleConfig.objects.get_or_create(society=society)
    if created:
        name_lower = (society.name or "").lower()
        if "glass view" in name_lower:
            config.service_fixed = Decimal('2400.00')
            config.security_fixed = Decimal('1600.00')
            config.electricity_fixed = Decimal('950.00')
            config.water_fixed = Decimal('350.00')
            config.prop_tax_rate = Decimal('3.850')
            config.sinking_rate = Decimal('1.250')
            config.repair_rate = Decimal('2.400')
            config.save()
        elif "hub" in name_lower:
            config.service_fixed = Decimal('3000.00')
            config.security_fixed = Decimal('1800.00')
            config.electricity_fixed = Decimal('1100.00')
            config.water_fixed = Decimal('400.00')
            config.prop_tax_rate = Decimal('4.100')
            config.sinking_rate = Decimal('1.400')
            config.repair_rate = Decimal('2.800')
            config.save()
    return config


def execute_auto_dispatch_for_society(society, ref_date=None, force=False):
    """
    Automatically generates and dispatches itemized CHS maintenance bills
    to all approved residents/flats for the designated period on the scheduled date.
    
    Returns a dict with execution results:
    {
        'dispatched': bool,
        'period': str,
        'created_count': int,
        'total_amount': Decimal,
        'reason': str
    }
    """
    import datetime
    import json
    from decimal import Decimal
    from SocietyHub.users.models import UserProfile
    from .models import PaymentTransaction, MaintenanceScheduleConfig

    today = ref_date or datetime.date.today()
    config = get_or_create_schedule_config(society)

    if not config.is_auto_dispatch_active and not force:
        return {
            'dispatched': False,
            'reason': f"Auto-dispatch is disabled for society '{society.name}'."
        }

    period_label = config.get_current_period_label(today)

    # Check if today is on or after the scheduled dispatch day
    # (Unless force=True for testing/viva demonstration)
    if not force:
        if today.day < config.dispatch_day:
            return {
                'dispatched': False,
                'period': period_label,
                'reason': f"Today (day {today.day}) is prior to scheduled dispatch day ({config.dispatch_day})."
            }

    # Duplicate check: check if bills for this period have already been dispatched for this society
    existing_bills = PaymentTransaction.objects.filter(
        society=society,
        payment_type='maintenance',
        billing_period=period_label
    )
    if existing_bills.exists() and not force:
        return {
            'dispatched': False,
            'period': period_label,
            'created_count': 0,
            'reason': f"Maintenance bills for '{period_label}' have already been dispatched."
        }

    # Fetch eligible residents
    eligible_profiles = UserProfile.objects.filter(
        society=society,
        is_approved=True,
        role__in=['resident', 'secretary', 'chairperson']
    ).select_related('user').order_by('wing', 'flat_number', 'user__first_name')

    if not eligible_profiles.exists():
        return {
            'dispatched': False,
            'period': period_label,
            'created_count': 0,
            'reason': f"No approved residents found in society '{society.name}'."
        }

    # Bill Date and Due Date
    bill_date = today
    due_date = today + datetime.timedelta(days=int(config.due_days or 15))

    # Sequential Bill Numbering
    last_bill_seq = 28
    try:
        last_b = PaymentTransaction.objects.exclude(bill_number__isnull=True).exclude(bill_number='').order_by('-id').first()
        if last_b and last_b.bill_number:
            last_bill_seq = int(''.join(filter(str.isdigit, str(last_b.bill_number))))
    except Exception:
        last_bill_seq = 28

    created_count = 0
    total_amount = Decimal('0')

    for user_prof in eligible_profiles:
        # Check if bill for this specific resident in this period already exists
        if not force and PaymentTransaction.objects.filter(user=user_prof.user, society=society, payment_type='maintenance', billing_period=period_label).exists():
            continue

        sqft = user_prof.area_sqft or Decimal('850')

        # Convert all config fields safely to Decimal
        prop_tax_rate = Decimal(str(config.prop_tax_rate or '0'))
        prop_tax_fixed = Decimal(str(config.prop_tax_fixed or '0'))
        sinking_rate = Decimal(str(config.sinking_rate or '0'))
        sinking_fixed = Decimal(str(config.sinking_fixed or '0'))
        repair_rate = Decimal(str(config.repair_rate or '0'))
        repair_fixed = Decimal(str(config.repair_fixed or '0'))
        service_rate = Decimal(str(config.service_rate or '0'))
        service_fixed = Decimal(str(config.service_fixed or '0'))
        electricity_fixed = Decimal(str(config.electricity_fixed or '0'))
        water_fixed = Decimal(str(config.water_fixed or '0'))
        security_fixed = Decimal(str(config.security_fixed or '0'))
        parking_fixed = Decimal(str(config.parking_fixed or '0'))
        non_occupancy_fixed = Decimal(str(config.non_occupancy_fixed or '0'))

        # Area based calculations
        prop_tax_amt = (sqft * prop_tax_rate) + prop_tax_fixed if (prop_tax_rate or prop_tax_fixed) else Decimal('0')
        sinking_amt = (sqft * sinking_rate) + sinking_fixed if (sinking_rate or sinking_fixed) else Decimal('0')
        repair_amt = (sqft * repair_rate) + repair_fixed if (repair_rate or repair_fixed) else Decimal('0')
        service_amt = (sqft * service_rate) + service_fixed if (service_rate or service_fixed) else Decimal('0')

        particulars_list = []
        if prop_tax_amt > 0:
            particulars_list.append({"particular": "PROPERTY TAXES", "amount": float(prop_tax_amt)})
        if sinking_amt > 0:
            particulars_list.append({"particular": "SINKING FUND", "amount": float(sinking_amt)})
        if repair_amt > 0:
            particulars_list.append({"particular": "REPAIR FUND", "amount": float(repair_amt)})
        if electricity_fixed > 0:
            particulars_list.append({"particular": "ELECTRICITY CHARGES", "amount": float(electricity_fixed)})
        if water_fixed > 0:
            particulars_list.append({"particular": "WATER CHARGES", "amount": float(water_fixed)})
        if service_amt > 0:
            particulars_list.append({"particular": "SERVICE CHARGES", "amount": float(service_amt)})
        if security_fixed > 0:
            particulars_list.append({"particular": "SECURITY CHARGES", "amount": float(security_fixed)})
        if parking_fixed > 0:
            particulars_list.append({"particular": "PARKING CHARGES", "amount": float(parking_fixed)})
        if non_occupancy_fixed > 0:
            particulars_list.append({"particular": "NON-OCCUPANCY CHARGES", "amount": float(non_occupancy_fixed)})

        # Custom heads defined in config
        custom_heads = config.custom_heads or []
        for ch in custom_heads:
            ch_name = ch.get('name', '').strip()
            ch_type = ch.get('type', 'fixed')
            ch_val = Decimal(str(ch.get('amount', 0) or 0))
            ch_amt = (sqft * ch_val) if ch_type == 'per_sqft' else ch_val
            if ch_amt > Decimal('0'):
                particulars_list.append({"particular": ch_name.upper(), "amount": float(ch_amt)})

        subtotal = sum(Decimal(str(item['amount'])) for item in particulars_list)
        if subtotal <= Decimal('0'):
            continue

        # Look for existing unpaid arrears for this resident
        prev_unpaid = PaymentTransaction.objects.filter(
            user=user_prof.user,
            society=society,
            payment_type='maintenance',
            status='pending'
        ).exclude(billing_period=period_label)
        arrears = sum(b.amount for b in prev_unpaid) if prev_unpaid.exists() else Decimal('0')
        interest = (arrears * Decimal('0.21')) if arrears > 0 else Decimal('0')

        # Look for unadjusted advance payments / custom dues paid in advance
        from django.db.models import Q
        advance_payments = PaymentTransaction.objects.filter(
            user=user_prof.user,
            society=society,
            status='success',
            is_advance_adjusted=False
        ).filter(
            Q(bill_number__isnull=True) | Q(bill_number='')
        )
        advance_credit = sum((b.amount for b in advance_payments), Decimal('0.00'))

        gross_total = subtotal + arrears + interest
        applied_advance = min(advance_credit, gross_total)
        grand_total = max(Decimal('0.00'), gross_total - applied_advance)

        last_bill_seq += 1
        bill_no_str = str(last_bill_seq)

        desc_parts = [f"Maintenance Bill ({period_label}) - Auto Dispatched"]
        if user_prof.flat_name:
            desc_parts.append(f"Flat: {user_prof.flat_name}")
        elif user_prof.wing or user_prof.flat_number:
            desc_parts.append(f"Flat: {user_prof.wing or ''}-{user_prof.flat_number or ''}")
        desc_parts.append(f"({sqft} sq.ft)")

        tx_status = 'pending'
        tx_receipt_number = None
        if grand_total == Decimal('0.00') and applied_advance > 0:
            tx_status = 'success'
            tx_receipt_number = PaymentTransaction.generate_receipt_number()

        tx = PaymentTransaction.objects.create(
            user=user_prof.user,
            society=society,
            payment_type='maintenance',
            amount=grand_total,
            subtotal_amount=subtotal,
            advance_amount=applied_advance,
            arrears_amount=arrears,
            interest_amount=interest,
            bill_number=bill_no_str,
            bill_date=bill_date,
            due_date=due_date,
            billing_period=period_label,
            breakdown_json=json.dumps(particulars_list),
            status=tx_status,
            receipt_number=tx_receipt_number,
            remarks=" | ".join(desc_parts)
        )

        if applied_advance > 0:
            advance_payments.update(is_advance_adjusted=True)
        created_count += 1
        total_amount += grand_total

        try:
            from SocietyHub.core.push import notify_maintenance_bill
            notify_maintenance_bill(tx)
        except Exception:
            pass

    # Update config tracking
    config.last_dispatched_date = today
    config.last_dispatched_period = period_label
    config.save()

    return {
        'dispatched': True,
        'period': period_label,
        'created_count': created_count,
        'total_amount': total_amount,
        'reason': f"Dispatched {created_count} bills totaling ₹{total_amount:,.2f} for {period_label}."
    }

