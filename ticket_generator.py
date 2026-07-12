#!/usr/bin/env python3
"""
============================================================
  Volcano Express Ltd - Bus Ticket Generator
  Powered by Centrika Ltd ticketing format
  Generates a thermal-style receipt PNG matching the sample.
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
#  LAYOUT CONSTANTS
# ======================================================================

TICKET_WIDTH = 760          # Total image width in pixels (~80 mm thermal paper)
PADDING      = 28           # Left / right margin
GAP          = 6            # Default vertical gap between elements
BG_COLOR     = "white"
FG_COLOR     = "black"

# Windows Courier New paths (closest to thermal receipt look)
FONT_REGULAR = "C:/Windows/Fonts/cour.ttf"
FONT_BOLD    = "C:/Windows/Fonts/courbd.ttf"

# Local bundled Courier Prime fonts
LOCAL_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
LOCAL_REG    = os.path.join(LOCAL_DIR, "CourierPrime.ttf")
LOCAL_BOLD   = os.path.join(LOCAL_DIR, "CourierPrime-Bold.ttf")

SIZE_TITLE  = 58   # "Volcano Express Ltd"
SIZE_LARGE  = 36   # Ticket number, seat
SIZE_NORMAL = 26   # Body text
SIZE_SMALL  = 22   # Timestamp, tagline


# ======================================================================
#  FONT HELPERS
# ======================================================================

def _load(primary_path: str, size: int, is_bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a TTF font; tries local, then primary, then system fallbacks, then PIL default."""
    local_path = LOCAL_BOLD if is_bold else LOCAL_REG
    candidates = [local_path, primary_path]
    
    # Try local and primary paths first
    for path in candidates:
        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass

    # Try Windows system Fonts folder fallback
    basename = os.path.basename(primary_path)
    try:
        alt = os.path.join(
            os.environ.get("WINDIR", "C:/Windows"),
            "Fonts", basename
        )
        return ImageFont.truetype(alt, size)
    except Exception:
        pass

    # Final fallback to PIL default
    return ImageFont.load_default()


def load_fonts() -> dict:
    return {
        "title":      _load(FONT_BOLD,    SIZE_TITLE,  is_bold=True),
        "large":      _load(FONT_BOLD,    SIZE_LARGE,  is_bold=True),
        "bold":       _load(FONT_BOLD,    SIZE_NORMAL, is_bold=True),
        "bold_small": _load(FONT_BOLD,    SIZE_SMALL,  is_bold=True),
        "reg":        _load(FONT_REGULAR, SIZE_NORMAL, is_bold=False),
        "small":      _load(FONT_REGULAR, SIZE_SMALL,  is_bold=False),
    }


# ======================================================================
#  DRAWING PRIMITIVES
# ======================================================================

def _th(font, text: str = "Ay") -> int:
    """Pixel height of text in the given font."""
    b = font.getbbox(text)
    return b[3] - b[1]


def _tw(font, text: str) -> int:
    """Pixel width of text in the given font."""
    b = font.getbbox(text)
    return b[2] - b[0]


def draw_centered(draw, y: int, text: str, font, width: int) -> int:
    x = (width - _tw(font, text)) // 2
    draw.text((x, y), text, font=font, fill=FG_COLOR)
    return _th(font, text)


def draw_left(draw, y: int, text: str, font, padding: int) -> int:
    draw.text((padding, y), text, font=font, fill=FG_COLOR)
    return _th(font, text)


def draw_two_col(draw, y: int,
                 left: str, left_font,
                 right: str, right_font,
                 width: int, padding: int) -> int:
    """Left-aligned + right-aligned text on the same row."""
    draw.text((padding, y), left, font=left_font, fill=FG_COLOR)
    rx = width - padding - _tw(right_font, right)
    draw.text((rx, y), right, font=right_font, fill=FG_COLOR)
    return max(_th(left_font, left), _th(right_font, right))


def draw_dashed_line(draw, y: int, font, width: int, padding: int) -> int:
    char_w = max(_tw(font, "-"), 1)
    n = (width - 2 * padding) // char_w
    line = "-" * n
    draw.text((padding, y), line, font=font, fill=FG_COLOR)
    return _th(font, line)


def draw_hash_line(draw, y: int, font, width: int, padding: int) -> int:
    char_w = max(_tw(font, "#"), 1)
    n = (width - 2 * padding) // char_w
    line = "#" * n
    draw.text((padding, y), line, font=font, fill=FG_COLOR)
    return _th(font, line)


# ======================================================================
#  QR CODE
# ======================================================================

def build_qr(data: str, px: int = 260) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=9,
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
    # Operator
    company_name:   str = "Volcano Express Ltd",
    phone:          str = "null",
    # Passenger
    customer:       str = "Jean",
    from_location:  str = "NYABUGOGO",
    to_location:    str = "MUHANGA",
    # Schedule
    dep_date:       str = "2025-07-02",
    dep_time:       str = "14:00",
    boarding_time:  str = "14:10",
    # Ticket identifiers
    ticket_number:  str = "935953259130612713",
    seat_no:        str = "25",
    plate_no:       str = "RAB006U",
    # Financials
    price:          str = "2,040RWF",
    # Staff
    cashier:        str = "Aimee Honorine INYIZYI NANA",
    # System
    timestamp:      str = "2025-07-02 13:50:57",
    transaction_id: str = "N88QWUK0834",
    # Output
    output_path:    str = "volcano_express_ticket.png",
    qr_size:        int = 260,
) -> str:
    """
    Generate a Volcano Express Ltd / Centrika thermal-style ticket PNG.
    Returns the absolute path of the saved image.
    """

    F = load_fonts()
    W = TICKET_WIDTH
    P = PADDING
    g = GAP

    # QR encodes the key ticket fields
    qr_data = (
        f"TKT:{ticket_number}|FROM:{from_location}|TO:{to_location}|"
        f"DATE:{dep_date} {dep_time}|SEAT:{seat_no}|PLATE:{plate_no}|"
        f"TS:{timestamp}|ID:{transaction_id}"
    )
    qr_img = build_qr(qr_data, qr_size)

    # Split cashier name onto two lines if > 3 words
    words = cashier.split()
    cashier_l1 = " ".join(words[:3])
    cashier_l2 = " ".join(words[3:]) if len(words) > 3 else ""

    # Draw onto a tall canvas; crop at the end
    canvas = Image.new("RGB", (W, 2600), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)
    y      = P

    def nl(h: int, extra: int = 0):
        """Advance cursor by h + gap + optional extra pixels."""
        nonlocal y
        y += h + g + extra

    # ------------------------------------------------------------------
    # SECTION A  -  MAIN (AGENT) TICKET
    # ------------------------------------------------------------------

    # Company title – large, bold, centered
    nl(draw_centered(draw, y, company_name, F["title"], W), extra=6)

    # Phone
    nl(draw_left(draw, y, f"Phone : {phone}", F["reg"], P))

    # Separator line
    nl(draw_dashed_line(draw, y, F["reg"], W, P), extra=4)

    # Customer
    nl(draw_left(draw, y, f"Customer: {customer}", F["reg"], P))

    # From / To – bold labels and values to match sample
    nl(draw_two_col(draw, y,
                    f"From :{from_location}", F["bold"],
                    f"To :{to_location}",     F["bold"],
                    W, P))

    # Column header: Dep. Date/Time  |  Boarding Time
    nl(draw_two_col(draw, y,
                    "Dep. Date/Time", F["bold"],
                    "Boarding Time",  F["bold"],
                    W, P))

    # Values: date + time  |  boarding time
    nl(draw_two_col(draw, y,
                    f"{dep_date} {dep_time}", F["reg"],
                    boarding_time,            F["reg"],
                    W, P))

    # Column header: Ticket Number  |  S.NO
    nl(draw_two_col(draw, y,
                    "Ticket Number", F["bold"],
                    "S.NO",          F["bold"],
                    W, P))

    # Values (large bold): ticket number  |  seat
    nl(draw_two_col(draw, y,
                    ticket_number, F["large"],
                    seat_no,       F["large"],
                    W, P))

    # Price row – both sides bold
    nl(draw_two_col(draw, y,
                    "PRICE :", F["bold"],
                    price,     F["bold"],
                    W, P))

    # Plate No row – both sides bold
    nl(draw_two_col(draw, y,
                    "Plate No", F["bold"],
                    plate_no,   F["bold"],
                    W, P))

    # Cashier (up to two lines)
    nl(draw_left(draw, y, f"Cashier : {cashier_l1}", F["reg"], P))
    if cashier_l2:
        nl(draw_left(draw, y, cashier_l2, F["reg"], P))

    # QR Code – centered
    y += g * 2
    canvas.paste(qr_img, ((W - qr_img.width) // 2, y))
    nl(qr_img.height, extra=g)

    # Timestamp + transaction ID below QR
    nl(draw_centered(draw, y,
                     f"{timestamp}  {transaction_id}",
                     F["small"], W), extra=6)

    # Centrika branding
    nl(draw_centered(draw, y, "A Product of  CENTRIKA LTD", F["bold"], W),
       extra=8)

    # Separator
    nl(draw_dashed_line(draw, y, F["reg"], W, P), extra=8)

    # ------------------------------------------------------------------
    # SECTION B  -  KINYARWANDA PASSENGER NOTE
    # ------------------------------------------------------------------

    for line in [
        "Kugenda hamwwe Like yavu kugenza",
        "urugendo ruranzeiyo/cumma umuco no",
        "wano ukarwema ntasubiriwe",
    ]:
        nl(draw_left(draw, y, line, F["reg"], P))

    y += g
    nl(draw_hash_line(draw, y, F["bold"], W, P), extra=8)

    # ------------------------------------------------------------------
    # SECTION C  -  PASSENGER COPY (DUPLICATE)
    # ------------------------------------------------------------------

    # Operator name – bold, left-aligned  (UPPERCASE to match sample)
    nl(draw_left(draw, y, "VOLCANO Express Ltd", F["bold"], P))

    # Customer
    nl(draw_left(draw, y, f"Customer: {customer}", F["reg"], P))

    # From / To – bold to match sample
    nl(draw_two_col(draw, y,
                    f"From :{from_location}", F["bold"],
                    f"To :{to_location}",     F["bold"],
                    W, P))

    # Dep. Date/Time  |  Boarding Time labels
    nl(draw_two_col(draw, y,
                    "Dep. Date/Time", F["bold"],
                    "Boarding Time",  F["bold"],
                    W, P))

    # Values
    nl(draw_two_col(draw, y,
                    f"{dep_date} {dep_time}", F["reg"],
                    boarding_time,            F["reg"],
                    W, P))

    # Ticket Number  |  S.NO labels
    nl(draw_two_col(draw, y,
                    "Ticket Number", F["bold"],
                    "S.NO",          F["bold"],
                    W, P))

    # Values (large bold)
    nl(draw_two_col(draw, y,
                    ticket_number, F["large"],
                    seat_no,       F["large"],
                    W, P))

    # Price
    nl(draw_two_col(draw, y,
                    "PRICE :", F["bold"],
                    price,     F["bold"],
                    W, P))

    # Plate No
    nl(draw_two_col(draw, y,
                    "Plate No", F["bold"],
                    plate_no,   F["bold"],
                    W, P))

    # Separator
    nl(draw_dashed_line(draw, y, F["reg"], W, P), extra=4)

    # Served By – VOLCANO uppercase to match sample
    nl(draw_left(draw, y, "  Served By : VOLCANO Express Ltd", F["reg"], P))

    # Cashier
    nl(draw_left(draw, y, f"Cashier : {cashier_l1}", F["reg"], P))
    if cashier_l2:
        nl(draw_left(draw, y, cashier_l2, F["reg"], P))

    # Timestamp + ID (left-aligned in the duplicate)
    nl(draw_left(draw, y,
                 f"{timestamp}  {transaction_id}",
                 F["small"], P))

    # Powered By
    nl(draw_left(draw, y, "Powered By Centrika Ltd.", F["bold"], P))

    # Tagline – centered
    nl(draw_centered(draw, y,
                     "*** Be On Time, Save Lives!***",
                     F["small"], W))

    # ------------------------------------------------------------------
    # Crop and save
    # ------------------------------------------------------------------
    final_height = y + P
    ticket = canvas.crop((0, 0, W, final_height))

    abs_path = os.path.abspath(output_path)
    ticket.save(abs_path, dpi=(300, 300))
    print(f"Ticket saved  =>  {abs_path}  ({W} x {final_height} px)")
    return abs_path


# ======================================================================
#  CLI ENTRY POINT  -  edit the values below to customise the ticket
# ======================================================================

if __name__ == "__main__":
    generate_ticket(
        company_name   = "Volcano Express Ltd",
        phone          = "null",
        customer       = "Jean",
        from_location  = "NYABUGOGO",
        to_location    = "MUHANGA",
        dep_date       = "2025-07-02",
        dep_time       = "14:00",
        boarding_time  = "14:10",
        ticket_number  = "935953259130612713",
        seat_no        = "25",
        plate_no       = "RAB006U",
        price          = "2,040RWF",
        cashier        = "Aimee Honorine INYIZYI NANA",
        timestamp      = "2025-07-02 13:50:57",
        transaction_id = "N88QWUK0834",
        output_path    = "volcano_express_ticket.png",
    )
