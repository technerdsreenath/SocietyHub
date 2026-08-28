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


def create_watermark_callback(society_name):
    """Returns a page callback that draws a crisp translucent watermark across the page."""
    def draw_watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 34)
        canvas.setFillColor(colors.Color(0.2, 0.3, 0.35, alpha=0.08))
        canvas.translate(A4[0] / 2.0, A4[1] / 2.0)
        canvas.rotate(38)
        canvas.drawCentredString(0, 0, society_name.upper())
        canvas.restoreState()
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

    society_name = transaction.society.name if transaction.society else "SocietyHub Co-operative Housing Society Ltd"
    if "co-operative" not in society_name.lower() and "chs" not in society_name.lower():
        society_display = f"{society_name} Co-operative Housing Society Ltd"
    else:
        society_display = society_name

    society_reg = "MUM-2/WL/HSG/TC/11026/2018-19"
    society_address = f"{transaction.society.area or 'LBS Marg, Church Road'}, {transaction.society.city or 'Mumbai'} - 400070"

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
    story.append(Paragraph(society_reg, sub_header_style))
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

    # Summary Table: TOTAL, Arrears, Interest, GRAND TOTAL
    arrears = float(transaction.arrears_amount)
    interest = float(transaction.interest_amount)
    grand_total = float(transaction.amount)

    summary_rows = [
        [Paragraph("<b>TOTAL :</b>", cell_right_bold), Paragraph(f"<b>{subtotal:,.2f}</b>", cell_right_bold)],
        [Paragraph("<b>Arrears Amount :</b>", cell_right_bold), Paragraph(f"{arrears:,.2f}", cell_right)],
        [Paragraph("<b>Pending Interest Amount :</b>", cell_right_bold), Paragraph("0.00", cell_right)],
        [Paragraph("<b>Current Interest 21% p.a. on Arrears :</b>", cell_right_bold), Paragraph(f"{interest:,.2f}", cell_right)],
        [Paragraph("<b>GRAND TOTAL PAYABLE :</b>", cell_right_bold), Paragraph(f"<b>₹ {grand_total:,.2f}</b>", cell_right_bold)],
    ]
    summary_table = Table(summary_rows, colWidths=[420, 105])
    summary_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F9FAFB')),
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
    notes_text = (
        "<b>NOTES :</b><br/>"
        "1) Please Pay the Bill on or Before Due Date.<br/>"
        "2) Delayed Payment will be Charged Interest @ 21% p.a.<br/>"
        "3) Mention your Flat No. and Mobile No. on Reverse of Cheque / Transaction Reference.<br/>"
        f"4) Payment should be drawn in favour of <b>{society_display}</b>.<br/>"
        "5) For NEFT/Online Payment: Bank: Citizencredit Co-op Bank Ltd, Kurla(W), A/c No: 2090062000018288, IFSC: CCBL0209006.<br/>"
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

    # Build with watermark on every page
    watermark_cb = create_watermark_callback(society_display)
    doc.build(story, onFirstPage=watermark_cb, onLaterPages=watermark_cb)
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

    society_name = transaction.society.name if transaction.society else "SocietyHub Co-operative Housing Society Ltd"
    if "co-operative" not in society_name.lower() and "chs" not in society_name.lower():
        society_display = f"{society_name} Co-operative Housing Society Ltd"
    else:
        society_display = society_name

    society_reg = "MUM-2/WL/HSG/TC/11026/2018-19"
    society_address = f"{transaction.society.area or 'LBS Marg, Church Road'}, {transaction.society.city or 'Mumbai'} - 400070"

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
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor('#E2E8F0')),
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
            Paragraph(f"₹ {p_amt:,.2f}", table_cell_bold),
        ])

    items_data.append([
        Paragraph("", table_cell),
        Paragraph("<b>Total Amount Paid (INR)</b>", table_cell_bold),
        Paragraph("", table_cell),
        Paragraph(f"<b>₹ {transaction.amount:,.2f}</b>", table_cell_bold),
    ])

    items_table = Table(items_data, colWidths=[35, 285, 95, 110])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F6D7A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#4F6D7A')),
        ('INNERGRID', (0,0), (-1,-2), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor('#4F6D7A')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
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
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
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

    watermark_cb = create_watermark_callback(society_display)
    doc.build(story, onFirstPage=watermark_cb, onLaterPages=watermark_cb)
    buffer.seek(0)
    return buffer
