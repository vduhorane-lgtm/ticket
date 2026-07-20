"""
Side-by-side comparison of the real and generated ticket.
Produces: evaluation/side_by_side.png
"""
from PIL import Image, ImageDraw, ImageFont
import os

DIR = os.path.dirname(os.path.abspath(__file__))

real = Image.open(os.path.join(DIR, "real_ticket.jpeg")).convert("L")
gen  = Image.open(os.path.join(DIR, "generated_ticket.png")).convert("L")

# Scale real ticket to same width as generated for fair comparison
scale = gen.width / real.width
real_resized = real.resize((gen.width, int(real.height * scale)), Image.LANCZOS)

# Build canvas
gap = 40
label_h = 30
max_h = max(real_resized.height, gen.height)
canvas_w = gen.width * 2 + gap
canvas_h = max_h + label_h + 10
canvas = Image.new("L", (canvas_w, canvas_h), 255)

# Paste
canvas.paste(real_resized, (0, label_h))
canvas.paste(gen, (gen.width + gap, label_h))

# Labels
draw = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("arial.ttf", 18)
except:
    font = ImageFont.load_default()

draw.text((gen.width // 2 - 60, 4), "REAL TICKET", fill=0, font=font)
draw.text((gen.width + gap + gen.width // 2 - 80, 4), "GENERATED TICKET", fill=0, font=font)

# Vertical centre line
for yy in range(0, canvas_h, 4):
    draw.point((gen.width + gap // 2, yy), fill=128)

out = os.path.join(DIR, "side_by_side.png")
canvas.save(out, dpi=(203, 203))
print(f"Saved => {out}  ({canvas_w}x{canvas_h})")
