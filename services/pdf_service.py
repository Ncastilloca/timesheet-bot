"""
PDF timesheet generator - ReportLab. Fixed signature style bug.
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)

NAVY  = colors.HexColor("#1A3A5C")
BLUE  = colors.HexColor("#2C5F8A")
LIGHT = colors.HexColor("#EAF2FB")
GRAY  = colors.HexColor("#F5F5F5")
MID   = colors.HexColor("#CCCCCC")
WHITE = colors.white
BLACK = colors.black

# Define ALL styles as module-level objects so they are never passed as strings
_H   = ParagraphStyle("H",   fontName="Helvetica-Bold", fontSize=20, textColor=WHITE,  alignment=TA_CENTER)
_LBL = ParagraphStyle("LBL", fontName="Helvetica-Bold", fontSize=8,  textColor=BLUE)
_VAL = ParagraphStyle("VAL", fontName="Helvetica",      fontSize=10)
_CH  = ParagraphStyle("CH",  fontName="Helvetica-Bold", fontSize=9,  textColor=WHITE,  alignment=TA_CENTER)
_CC  = ParagraphStyle("CC",  fontName="Helvetica",      fontSize=9,  alignment=TA_CENTER)
_CB  = ParagraphStyle("CB",  fontName="Helvetica-Bold", fontSize=9,  textColor=BLUE,   alignment=TA_CENTER)
_CL  = ParagraphStyle("CL",  fontName="Helvetica",      fontSize=8,  alignment=TA_LEFT)
_TV  = ParagraphStyle("TV",  fontName="Helvetica-Bold", fontSize=12, textColor=WHITE,  alignment=TA_CENTER)
_SL  = ParagraphStyle("SL",  fontName="Helvetica-Bold", fontSize=8,  textColor=BLUE)
_SL2 = ParagraphStyle("SL2", fontName="Helvetica",      fontSize=8,  textColor=colors.HexColor("#666666"))
_FT  = ParagraphStyle("FT",  fontName="Helvetica",      fontSize=7,  textColor=colors.HexColor("#AAAAAA"), alignment=TA_CENTER)


def make_pdf(name: str, period: dict, entries: list,
             dfmt: str = "MM/DD/YYYY", tfmt: str = "12h") -> bytes:
    from utils.time_utils import fmt_date, fmt_time, fmt_hours

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch,  bottomMargin=0.75*inch)
    W = letter[0] - 1.5*inch
    story = []

    # ── Header ──────────────────────────────────────────────────
    hdr = Table([[Paragraph("EMPLOYEE TIMESHEET", _H)]], colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 16),
        ("BOTTOMPADDING", (0,0),(-1,-1), 16),
    ]))
    story += [hdr, Spacer(1, 0.18*inch)]

    # ── Info row ─────────────────────────────────────────────────
    start = fmt_date(period["start_date"], dfmt)
    end   = fmt_date(period["end_date"],   dfmt) if period.get("end_date") else "Present"
    gen   = datetime.now().strftime("%B %d, %Y  %I:%M %p")

    info = Table([
        [Paragraph("EMPLOYEE", _LBL),  Paragraph("PAY PERIOD", _LBL), Paragraph("GENERATED", _LBL)],
        [Paragraph(name,       _VAL),  Paragraph(f"{start} — {end}", _VAL), Paragraph(gen, _VAL)],
    ], colWidths=[W*0.35, W*0.38, W*0.27])
    info.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), LIGHT),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("LINEBELOW",     (0,1),(-1,1), 1, BLUE),
    ]))
    story += [info, Spacer(1, 0.22*inch)]

    # ── Entries table ─────────────────────────────────────────────
    rows = [[
        Paragraph("#",        _CH),
        Paragraph("DATE",     _CH),
        Paragraph("DAY",      _CH),
        Paragraph("TIME IN",  _CH),
        Paragraph("TIME OUT", _CH),
        Paragraph("HOURS",    _CH),
        Paragraph("NOTES",    _CH),
    ]]
    total_h = 0.0
    for i, e in enumerate(entries, 1):
        try:
            day = datetime.strptime(e["work_date"], "%Y-%m-%d").strftime("%a")
        except Exception:
            day = ""
        h = float(e.get("total_hours") or 0)
        total_h += h
        rows.append([
            Paragraph(str(i),                          _CC),
            Paragraph(fmt_date(e["work_date"], dfmt),  _CC),
            Paragraph(day,                             _CC),
            Paragraph(fmt_time(e["time_in"],   tfmt),  _CC),
            Paragraph(fmt_time(e["time_out"],  tfmt),  _CC),
            Paragraph(fmt_hours(h),                    _CB),
            Paragraph(str(e.get("notes") or ""),       _CL),
        ])
    # Pad to minimum 10 rows
    for _ in range(max(0, 10 - len(entries))):
        rows.append([Paragraph("", _CC)] * 7)

    cw = [W*0.05, W*0.13, W*0.07, W*0.13, W*0.13, W*0.10, W*0.39]
    tbl = Table(rows, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  NAVY),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, GRAY]),
        ("GRID",           (0,0),(-1,-1), 0.4, MID),
        ("LINEBELOW",      (0,0),(-1,0),  1.5, BLUE),
        ("TOPPADDING",     (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 6),
        ("LEFTPADDING",    (0,0),(-1,-1), 4),
        ("RIGHTPADDING",   (0,0),(-1,-1), 4),
        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [tbl, Spacer(1, 0.15*inch)]

    # ── Totals bar ────────────────────────────────────────────────
    tot = Table([[
        Paragraph(f"Days Worked: {len(entries)}", _TV),
        Paragraph(f"TOTAL HOURS:  {fmt_hours(total_h)}  ({total_h:.2f} hrs)", _TV),
    ]], colWidths=[W*0.38, W*0.62])
    tot.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), BLUE),
        ("TOPPADDING",    (0,0),(-1,-1), 11),
        ("BOTTOMPADDING", (0,0),(-1,-1), 11),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
    ]))
    story += [tot, Spacer(1, 0.35*inch)]

    # ── Signatures ────────────────────────────────────────────────
    # IMPORTANT: always pass style OBJECTS, never strings
    sig = Table([
        [Paragraph("EMPLOYEE SIGNATURE",   _SL), Paragraph("", _SL2),
         Paragraph("SUPERVISOR SIGNATURE", _SL), Paragraph("", _SL2)],
        [HRFlowable(width="100%", thickness=1, color=BLACK), Paragraph("", _SL2),
         HRFlowable(width="100%", thickness=1, color=BLACK), Paragraph("", _SL2)],
        [Paragraph(name,                   _SL2), Paragraph("", _SL2),
         Paragraph("Manager / Supervisor", _SL2), Paragraph("", _SL2)],
        [Paragraph("Date: _______________",_SL2), Paragraph("", _SL2),
         Paragraph("Date: _______________",_SL2), Paragraph("", _SL2)],
    ], colWidths=[W*0.42, W*0.06, W*0.42, W*0.10])
    sig.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("VALIGN",        (0,0),(-1,-1), "BOTTOM"),
    ]))
    story += [sig, Spacer(1, 0.15*inch)]

    # ── Footer ────────────────────────────────────────────────────
    story += [
        HRFlowable(width="100%", thickness=0.5, color=MID),
        Spacer(1, 0.05*inch),
        Paragraph(f"Generated by TimeSheet Bot  •  {gen}  •  Confidential", _FT),
    ]

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf
