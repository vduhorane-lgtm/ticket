#!/usr/bin/env python3
"""
============================================================
  Rwanda Intercity & City Bus Ticket Generator
  Matches: Volcano / Horizon / Ritco / AC Group (SU DIRECT)
  Thermal 58 mm paper  (~384 px wide @ 167 dpi)
  Single cut length: 8 – 12 cm
============================================================

Dependencies:
    pip install Pillow qrcode[pil]

Usage:
    python ticket_generator.py
    or import and call generate_ticket(**kwargs)
"""

from PIL import Image, ImageDraw, ImageFont
import qrcode
import os


# ======================================================================
#  PAPER / LAYOUT CONSTANTS
# ======================================================================

# 58 mm thermal paper @ ~167 dpi  => 384 px wide
# Physical: 384 px / 167 * 25.4 mm = ~58 mm  ✓
TICKET_WIDTH = 384
PADDING      = 14           # left / right margin
GAP          = 3            # default vertical gap
BG_COLOR     = "white"
FG_COLOR     = "black"

# ── Font paths ─────────────────────────────────────────────────────────
LOCAL_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_CP_REG    = os.path.join(LOCAL_DIR, "CourierPrime.ttf")
_CP_BOLD   = os.path.join(LOCAL_DIR, "CourierPrime-Bold.ttf")
_WIN_REG   = "C:/Windows/Fonts/cour.ttf"
_WIN_BOLD  = "C:/Windows/Fonts/courbd.ttf"
_WIN_SANS  = "C:/Windows/Fonts/arialbd.ttf"

# ── Font sizes (px) – tuned for 58 mm paper, 8-12 cm cut length ──────
# At 203 dpi: 1 mm ≈ 8 px  |  2.5 mm body = 20 px  |  header 4 mm = 32 px
SIZE_TITLE  = 30    # Company name header  (~4 mm tall)
SIZE_NORMAL = 19    # Body rows            (~2.4 mm)
SIZE_BOLD   = 19    # Bold rows            (same size, different weight)
SIZE_LARGE  = 21    # Ticket No / seat     (slightly larger)
SIZE_SMALL  = 16    # Footnotes, timestamps (~2 mm)


# ======================================================================
#  FONT LOADER
# ======================================================================

def _load(path: str, size: int, is_bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load font with graceful fallback chain."""
    local = _CP_BOLD if is_bold else _CP_REG
    win   = _WIN_BOLD if is_bold else _WIN_REG
    for p in [path, local, win]:
        if p:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def load_fonts(font_size_val: int = 21) -> dict:
    scale = font_size_val / 21.0
    size_title = int(24 * scale)   # original printer ROM font renders ~24px — Arial Bold 30 was too large
    size_normal = int(19 * scale)
    size_bold = int(19 * scale)
    size_large = int(font_size_val)
    size_small = int(16 * scale)
    return {
        "title":      _load(_WIN_SANS,  size_title,  is_bold=True),
        "reg":        _load(_CP_REG,    size_normal, is_bold=False),
        "bold":       _load(_CP_BOLD,   size_bold,   is_bold=True),
        "large":      _load(_CP_BOLD,   size_large,  is_bold=True),
        "small":      _load(_CP_REG,    size_small,  is_bold=False),
        "small_bold": _load(_CP_BOLD,   size_small,  is_bold=True),
        "sans":       _load(_WIN_SANS,  size_normal, is_bold=True),
        "sans_small": _load(_WIN_SANS,  size_small,  is_bold=True),
    }


# ======================================================================
#  DRAWING PRIMITIVES
# ======================================================================

def _th(font, text: str = "Ay") -> int:
    b = font.getbbox(text)
    return b[3] - b[1]

def _tw(font, text: str) -> int:
    b = font.getbbox(text)
    return b[2] - b[0]

def draw_centered(draw, y, text, font, width) -> int:
    x = (width - _tw(font, text)) // 2
    draw.text((x, y), text, font=font, fill=FG_COLOR)
    return _th(font, text)

def draw_left(draw, y, text, font, pad=PADDING) -> int:
    draw.text((pad, y), text, font=font, fill=FG_COLOR)
    return _th(font, text)

def draw_two_col(draw, y, left, lf, right, rf, width, pad=PADDING) -> int:
    draw.text((pad, y), left, font=lf, fill=FG_COLOR)
    rx = width - pad - _tw(rf, right)
    draw.text((rx, y), right, font=rf, fill=FG_COLOR)
    return max(_th(lf, left), _th(rf, right))

def draw_underline(draw, y_baseline, x1, x2, thickness=2):
    """Solid underline rule under text."""
    draw.line([(x1, y_baseline), (x2, y_baseline)], fill=FG_COLOR, width=thickness)

def draw_dashed(draw, y, font, width, pad=PADDING) -> int:
    cw = max(_tw(font, "-"), 1)
    n  = (width - 2 * pad) // cw
    s  = "-" * n
    draw.text((pad, y), s, font=font, fill=FG_COLOR)
    return _th(font, s)

def draw_equals(draw, y, font, width, pad=PADDING) -> int:
    cw = max(_tw(font, "="), 1)
    n  = (width - 2 * pad) // cw
    s  = "=" * n
    draw.text((pad, y), s, font=font, fill=FG_COLOR)
    return _th(font, s)

def wrap_text(text, font, max_width, pad=PADDING) -> list:
    """Word-wrap text to fit within (max_width - 2*pad)."""
    avail = max_width - 2 * pad
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if _tw(font, test) <= avail:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


# ======================================================================
#  QR CODE BUILDER
# ======================================================================

def build_qr(data: str, px: int = 210) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((px, px), Image.NEAREST)


# ======================================================================
#  MAIN GENERATOR
# ======================================================================

def generate_ticket(
    # ── Operator ────────────────────────────────────────────────────────
    company_name:   str = "SU DIRECT",
    phone:          str = "0796604155",
    # ── Passenger ───────────────────────────────────────────────────────
    customer:       str = "Dinyo",
    from_location:  str = "RUHANGO",
    to_location:    str = "NYANZA",
    # ── Schedule ────────────────────────────────────────────────────────
    dep_date:       str = "Jul 16 2026",
    dep_time:       str = "20:30",
    boarding_time:  str = "20:00",
    # ── Ticket IDs ──────────────────────────────────────────────────────
    ticket_number:  str = "39086948",
    seat_no:        str = "30",           # displayed as "Ticket count"
    plate_no:       str = "RAK319C",
    # ── Financials ──────────────────────────────────────────────────────
    price:          str = "753 RWF",
    # ── Staff ───────────────────────────────────────────────────────────
    cashier:        str = "NIYOBUHORO",
    payment_method: str = "CASH",
    # ── System ──────────────────────────────────────────────────────────
    timestamp:      str = "Jul 16 2026 19:34",
    transaction_id: str = "39086948",
    # ── Branding ────────────────────────────────────────────────────────
    powered_by:     str = "TAP&GO/POWERED BY AC Mobility",
    # ── Layout Settings ─────────────────────────────────────────────────
    paper_width:    str = "57mm",
    ticket_mode:    str = "original_15cm",
    font_size:      int = 21,
    line_spacing:   float = 1.4,
    # ── Output ──────────────────────────────────────────────────────────
    output_path:    str = "bus_ticket.png",
    qr_size:        int = 210,
    **kwargs,
) -> str:
    """
    Generate a Rwanda-style thermal bus ticket PNG.
    Matches Volcano / Horizon / Ritco / AC Group (SU DIRECT) format.
    Returns the absolute path of the saved PNG.

    Physical output at 203 dpi:
      Width  : 384 px  ≈ 48 mm  (fits 58 mm roll with margins)
      Height : auto-cropped; main section ≈ 85-105 mm (8.5–10.5 cm)
    """

    F = load_fonts(font_size)
    if paper_width in ("50mm", "5cm"):
        W = 400  # 50 mm = 5.0 cm @ 203 DPI
    elif paper_width == "80mm":
        W = 576  # 80 mm = 7.2 cm @ 203 DPI
    else:
        W = 384  # 57 mm / 58 mm = 4.8 cm printable area @ 203 DPI
    P = PADDING
    g = max(2, int(3 * (font_size / 21.0)))

    # ── QR payload ──────────────────────────────────────────────────────
    qr_data = (
        f"TKT:{ticket_number}|NAMES:{customer}|"
        f"FROM:{from_location}|TO:{to_location}|"
        f"TRAVEL:{dep_date} {dep_time}|PLATE:{plate_no}|"
        f"PRICE:{price}|AGENT:{cashier}({payment_method})|"
        f"PRINTED:{timestamp}"
    )
    qr_img = build_qr(qr_data, qr_size)

    # ── Canvas ──────────────────────────────────────────────────────────
    canvas = Image.new("RGB", (W, 2800), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)
    y      = 10  # Tight short top margin (~1.2 mm) above header

    def nl(h: int, extra: int = 0):
        nonlocal y
        line_gap = int(h * (line_spacing - 1.0))
        y += h + max(0, line_gap) + extra

    # ==================================================================
    # SECTION A – MAIN TICKET  (agent copy)
    # ==================================================================

    # ── Company header – centered, large bold ────────────────────────
    title_h = draw_centered(draw, y, company_name, F["title"], W)
    nl(title_h, extra=6)

    # ── Thin separator (between title and phone) ────────────────────
    nl(draw_dashed(draw, y, F["small"], W), extra=2)

    # ── Phone ───────────────────────────────────────────────────────
    nl(draw_left(draw, y, phone, F["reg"]))

    # ── Passenger rows – left aligned, monospaced ───────────────────
    nl(draw_left(draw, y, f"NAMES: {customer}",     F["reg"]))
    nl(draw_left(draw, y, f"FROM: {from_location}",  F["reg"]))
    nl(draw_left(draw, y, f"TO: {to_location}",      F["reg"]))
    nl(draw_left(draw, y, f"TRAVEL TIME: {dep_date} {dep_time}", F["reg"]))
    nl(draw_left(draw, y, f"TICKET ID: {ticket_number}", F["reg"]))
    nl(draw_left(draw, y, f"Ticket count: {seat_no}",    F["reg"]))

    # ── PLATE No & PRICE – bold + underlined (matches sample) ────────────────
    y += g * 1

    ascent, descent = F["bold"].getmetrics()
    text_h = ascent + descent

    plate_text = f"PLATE No: {plate_no}"
    draw.text((P, y), plate_text, font=F["bold"], fill=FG_COLOR)
    draw_underline(draw, y + ascent + 2, P, P + _tw(F["bold"], plate_text), thickness=2)
    nl(text_h, extra=2)

    price_text = f"PRICE: {price}"
    draw.text((P, y), price_text, font=F["bold"], fill=FG_COLOR)
    draw_underline(draw, y + ascent + 2, P, P + _tw(F["bold"], price_text), thickness=2)
    nl(text_h, extra=2)

    # ── QR Code – centered ───────────────────────────────────────────
    y += g * 1
    qr_x = (W - qr_img.width) // 2
    canvas.paste(qr_img, (qr_x, y))
    y += qr_img.height + g * 2   # advance past QR directly — skip nl() to avoid line_spacing multiplier

    # ── Kinyarwanda passenger note ─────────────────────────────────────
    # Original ticket: line 1 flush-left, line 2 indented 1 space, rest flush-left
    kiny_lines = [
        ("Mugenzi gumana itike yawe kugeza", False),
        (" urugendo rurangiye. Cunga umuzi", False),   # leading space matches original indent
        ("go wawe",                          False),
        ("*Ukerewe ntasubizwa",              False),
    ]
    for line, _bold in kiny_lines:
        for wl in wrap_text(line, F["reg"], W, P):
            nl(draw_left(draw, y, wl, F["reg"]))

    y += g

    # ── Agent name ───────────────────────────────────────────────────
    nl(draw_left(draw, y, f"AGENT NAME:  {cashier}({payment_method})", F["reg"]))

    # ── Printed at ───────────────────────────────────────────────────
    nl(draw_left(draw, y, f"Printed at: {timestamp}", F["reg"]))

    y += g * 1

    # ── Powered-by branding ──────────────────────────────────────────
    # Original: normal weight regular font, left-aligned, small gap after
    nl(draw_left(draw, y, powered_by, F["reg"]), extra=2)

    if ticket_mode != "compact_8cm":
        # ── Tear-line separator ──────────────────────────────────────────
        nl(draw_dashed(draw, y, F["small"], W), extra=4)

        # ==================================================================
        # SECTION B – PASSENGER STUB  (duplicate below tear line)
        # ==================================================================

        nl(draw_left(draw, y, f"NAMES: {customer}",     F["reg"]))
        nl(draw_left(draw, y, f"FROM: {from_location}",  F["reg"]))
        nl(draw_left(draw, y, f"TO: {to_location}",      F["reg"]))
        nl(draw_left(draw, y, f"TRAVEL TIME: {dep_date} {dep_time}", F["reg"]))
        nl(draw_left(draw, y, f"PLATE No: {plate_no}",        F["reg"]))
        nl(draw_left(draw, y, f"PRICE: {price}",              F["reg"]))
        nl(draw_left(draw, y, f"TICKET ID: {ticket_number}",  F["reg"]))
        nl(draw_left(draw, y, f"Ticket count: {seat_no}",     F["reg"]))
        nl(draw_left(draw, y, f"AGENT NAME:  {cashier}({payment_method})", F["reg"]))
        nl(draw_left(draw, y, f"Printed at: {timestamp}",     F["reg"]))

        y += g * 2

    # ==================================================================
    # CROP & SAVE TO EXACT PHYSICAL MEASUREMENTS
    # ==================================================================
    # Target 15 cm (150 mm) height @ 203 DPI = 1199 px for original_15cm preset
    content_height = y + P + 4
    if ticket_mode == "original_15cm":
        target_15cm_px = int(150 / 25.4 * 203)  # 1199 px = 15.0 cm
        final_height = max(content_height, target_15cm_px)
    elif ticket_mode == "compact_8cm":
        target_8cm_px = int(80 / 25.4 * 203)    # 639 px = 8.0 cm
        final_height = max(content_height, target_8cm_px)
    else:
        final_height = content_height

    ticket = canvas.crop((0, 0, W, final_height))

    # 1-bit monochrome → crisp thermal edges
    ticket = ticket.convert("1")

    abs_path = os.path.abspath(output_path)
    ticket.save(abs_path, dpi=(203, 203))

    w_mm = W / 203 * 25.4
    h_mm = final_height / 203 * 25.4
    # Section A alone (above tear line) is approx first 65-70% of height
    main_mm = h_mm * 0.60
    print(f"Ticket saved  =>  {abs_path}")
    print(f"Canvas: {W} x {final_height} px  |  {w_mm:.1f} x {h_mm:.1f} mm @ 203 dpi")
    print(f"Main section (above tear): ~{main_mm:.0f} mm ({main_mm/10:.1f} cm)")
    return abs_path


# ======================================================================
#  CLI ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    generate_ticket(
        company_name   = "SU DIRECT",
        phone          = "0796604155",
        customer       = "Dinyo",
        from_location  = "RUHANGO",
        to_location    = "NYANZA",
        dep_date       = "Jul 16 2026",
        dep_time       = "20:30",
        boarding_time  = "20:00",
        ticket_number  = "39086948",
        seat_no        = "30",
        plate_no       = "RAK319C",
        price          = "753 RWF",
        cashier        = "NIYOBUHORO",
        payment_method = "CASH",
        timestamp      = "Jul 16 2026 19:34",
        transaction_id = "39086948",
        powered_by     = "TAP&GO/POWERED BY AC Mobility",
        output_path    = "bus_ticket.png",
        qr_size        = 210,
    )
