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

# ── Font sizes (px) – tuned for 58 mm paper ───────────────────────────
# Original ticket (15 cm long): font ~10-12 pt (23-25 px), 1.4x line spacing, 300px QR
DEFAULT_SIZE_TITLE  = 36    # Company name header  (~4.5 mm tall)
DEFAULT_SIZE_NORMAL = 23    # Body rows            (~2.9 mm, 11-12 pt)
DEFAULT_SIZE_BOLD   = 23    # Bold rows
DEFAULT_SIZE_LARGE  = 25    # Ticket No / seat
DEFAULT_SIZE_SMALL  = 18    # Footnotes, timestamps (~2.2 mm)


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


def load_fonts(scale: float = 1.0, base_size: int = 23) -> dict:
    """Load font dictionary with dynamic scale factor."""
    # Ratio relative to standard normal body font
    ratio = base_size / 23.0 * scale
    
    size_title  = max(16, int(round(DEFAULT_SIZE_TITLE * ratio)))
    size_normal = max(12, int(round(base_size * scale)))
    size_bold   = size_normal
    size_large  = max(14, int(round(DEFAULT_SIZE_LARGE * ratio)))
    size_small  = max(10, int(round(DEFAULT_SIZE_SMALL * ratio)))

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

def draw_left(draw, y, text, font, width=TICKET_WIDTH, pad=PADDING, canvas=None) -> int:
    avail = width - 2 * pad
    tw = _tw(font, text)
    th = _th(font, text)
    if tw <= avail or tw == 0 or canvas is None:
        draw.text((pad, y), text, font=font, fill=FG_COLOR)
    else:
        # Auto-condense text to fit within avail width cleanly (matches thermal printer font behavior)
        txt_img = Image.new("RGBA", (tw, th + 4), (255, 255, 255, 0))
        tdraw = ImageDraw.Draw(txt_img)
        tdraw.text((0, 0), text, font=font, fill=FG_COLOR)
        scaled_img = txt_img.resize((avail, th + 4), Image.BICUBIC)
        canvas.paste(scaled_img, (pad, y), scaled_img)
    return th

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
    # ── Formatting / Layout Options ─────────────────────────────────────
    ticket_mode:    str = "original_15cm",  # "original_15cm" or "compact_8cm"
    font_size:      int = 23,               # 23 px (11-12 pt @ 203 dpi) for original, 19 px for compact
    line_spacing:   float = 1.4,            # 1.4 line multiplier (8px gap) for original, 1.0 (3px gap) for compact
    qr_size:        int = 300,              # 300 px (80% width) for original, 210 px for compact
    # ── Output ──────────────────────────────────────────────────────────
    output_path:    str = "bus_ticket.png",
) -> str:
    """
    Generate a Rwanda-style thermal bus ticket PNG.
    Matches Volcano / Horizon / Ritco / AC Group (SU DIRECT) format.
    Returns the absolute path of the saved PNG.

    Physical output at 203 dpi:
      Width  : 384 px  ≈ 48 mm  (fits 58 mm roll with margins)
      Height : original mode ~1200 px ≈ 150 mm (15 cm long physical cut)
               compact mode  ~700 px  ≈ 85 mm (8.5 cm short physical cut)
    """

    # Handle preset mode overrides if defaults are passed with mode
    if ticket_mode == "compact_8cm" and font_size == 21 and line_spacing == 1.4 and qr_size == 325:
        font_size = 18
        line_spacing = 1.0
        qr_size = 220
    elif ticket_mode == "original_15cm" and (font_size is None or font_size <= 0):
        font_size = 21
        line_spacing = 1.4
        qr_size = 325

    # Calculate gap from line spacing factor
    g = max(2, int(round((line_spacing - 1.0) * font_size + (3 if line_spacing <= 1.1 else 4))))

    F = load_fonts(scale=1.0, base_size=font_size)
    W = TICKET_WIDTH
    P = PADDING

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
    canvas = Image.new("RGB", (W, 3500), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)
    y      = P + 6

    def nl(h: int, extra: int = 0):
        nonlocal y
        y += h + g + extra

    # ==================================================================
    # SECTION A – MAIN TICKET  (agent copy)
    # ==================================================================

    # ── Company header – centered, large bold ────────────────────────
    title_h = draw_centered(draw, y, company_name, F["title"], W)
    nl(title_h, extra=int(g * 0.8))

    # ── Phone ─────────(Direct transition, no dashed line under title)─
    nl(draw_left(draw, y, phone, F["reg"], W, P, canvas))

    # ── Passenger rows – left aligned, monospaced ───────────────────
    nl(draw_left(draw, y, f"NAMES: {customer}",     F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"FROM: {from_location}",  F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"TO: {to_location}",      F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"TRAVEL TIME: {dep_date} {dep_time}", F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"TICKET ID: {ticket_number}", F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"Ticket count: {seat_no}",    F["reg"], W, P, canvas))

    # ── PLATE No & PRICE – bold + underlined (matches sample) ────────
    y += g // 2

    ascent, descent = F["bold"].getmetrics()
    text_h = ascent + descent

    plate_text = f"PLATE No: {plate_no}"
    draw_left(draw, y, plate_text, F["bold"], W, P, canvas)
    draw_underline(draw, y + ascent + 2, P, P + _tw(F["bold"], plate_text), thickness=2)
    nl(text_h, extra=g // 2)

    price_text = f"PRICE: {price}"
    draw_left(draw, y, price_text, F["bold"], W, P, canvas)
    draw_underline(draw, y + ascent + 2, P, P + _tw(F["bold"], price_text), thickness=2)
    nl(text_h, extra=g)

    # ── QR Code – centered ───────────────────────────────────────────
    y += g * 2
    qr_x = (W - qr_img.width) // 2
    canvas.paste(qr_img, (qr_x, y))
    nl(qr_img.height, extra=g * 2)

    # ── Kinyarwanda passenger note – 4 exact lines ───────────────────
    kiny_lines = [
        "Mugenzi gumana itike yawe kugeza",
        "urugendo rurangiye. Cunga umuzi",
        "go wawe",
        "*Ukerewe ntasubizwa",
    ]
    for line in kiny_lines:
        nl(draw_left(draw, y, line, F["reg"], W, P, canvas))

    y += g // 2

    # ── Agent name ───────────────────────────────────────────────────
    nl(draw_left(draw, y, f"AGENT NAME: {cashier}({payment_method})", F["reg"], W, P, canvas))

    # ── Printed at ───────────────────────────────────────────────────
    nl(draw_left(draw, y, f"Printed at: {timestamp}", F["reg"], W, P, canvas))

    y += g * 2

    # ── Powered-by branding ──────────────────────────────────────────
    nl(draw_centered(draw, y, powered_by, F["sans_small"], W), extra=g)

    # ── Tear-line separator ──────────────────────────────────────────
    nl(draw_dashed(draw, y, F["small"], W), extra=g)

    # ==================================================================
    # SECTION B – PASSENGER STUB  (duplicate below tear line)
    # ==================================================================

    nl(draw_left(draw, y, f"NAMES: {customer}",     F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"FROM: {from_location}",  F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"TO: {to_location}",      F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"TRAVEL TIME: {dep_date} {dep_time}", F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"PLATE No: {plate_no}",        F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"PRICE: {price}",              F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"TICKET ID: {ticket_number}",  F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"Ticket count: {seat_no}",     F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"AGENT NAME: {cashier}({payment_method})", F["reg"], W, P, canvas))
    nl(draw_left(draw, y, f"Printed at: {timestamp}",     F["reg"], W, P, canvas))

    y += g * 2

    # ==================================================================
    # CROP & SAVE
    # ==================================================================
    final_height = y + P + 6
    ticket = canvas.crop((0, 0, W, final_height))

    # 1-bit monochrome → crisp thermal edges
    ticket = ticket.convert("1")

    abs_path = os.path.abspath(output_path)
    ticket.save(abs_path, dpi=(203, 203))

    w_mm = W / 203 * 25.4
    h_mm = final_height / 203 * 25.4
    main_mm = h_mm * 0.60
    print(f"Ticket saved  =>  {abs_path}")
    print(f"Canvas: {W} x {final_height} px  |  {w_mm:.1f} x {h_mm:.1f} mm ({h_mm/10:.1f} cm) @ 203 dpi")
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
        ticket_mode    = "original_15cm",
        output_path    = "bus_ticket.png",
    )
