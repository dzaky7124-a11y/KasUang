import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

icons_dir = Path("static/icons")
icons_dir.mkdir(parents=True, exist_ok=True)

def create_app_icon(size: int, output_path: Path):
    # Create image with smooth emerald-to-teal gradient background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded rectangle background
    corner_radius = size // 5
    # Gradient simulation
    c1 = (16, 185, 129)  # Emerald 500
    c2 = (13, 148, 136)  # Teal 600

    for i in range(size):
        r = int(c1[0] + (c2[0] - c1[0]) * (i / size))
        g = int(c1[1] + (c2[1] - c1[1]) * (i / size))
        b = int(c1[2] + (c2[2] - c1[2]) * (i / size))
        draw.line([(0, i), (size, i)], fill=(r, g, b, 255))

    # Mask with rounded corners
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size, size)], corner_radius, fill=255)
    img.putalpha(mask)

    # Draw Wallet / Kas symbol
    draw = ImageDraw.Draw(img)
    center = size // 2
    w_width = int(size * 0.55)
    w_height = int(size * 0.42)
    left = center - w_width // 2
    top = center - w_height // 2

    # Outer wallet card
    draw.rounded_rectangle(
        [(left, top), (left + w_width, top + w_height)],
        radius=int(size * 0.08),
        fill=(255, 255, 255, 240)
    )

    # Wallet fold / flap
    flap_height = int(w_height * 0.45)
    flap_right = left + w_width
    flap_top = top + int(w_height * 0.28)
    draw.rounded_rectangle(
        [(center + int(w_width * 0.05), flap_top), (flap_right, flap_top + flap_height)],
        radius=int(size * 0.04),
        fill=(16, 185, 129, 255)
    )

    # Gold coin / latch dot
    dot_radius = int(size * 0.035)
    dot_cx = center + int(w_width * 0.26)
    dot_cy = flap_top + flap_height // 2
    draw.ellipse(
        [(dot_cx - dot_radius, dot_cy - dot_radius), (dot_cx + dot_radius, dot_cy + dot_radius)],
        fill=(245, 158, 11, 255)
    )

    # Currency accent line
    draw.line(
        [(left + int(w_width * 0.15), top + int(w_height * 0.4)), (left + int(w_width * 0.45), top + int(w_height * 0.4))],
        fill=(16, 185, 129, 200),
        width=max(2, size // 50)
    )
    draw.line(
        [(left + int(w_width * 0.15), top + int(w_height * 0.65)), (left + int(w_width * 0.38), top + int(w_height * 0.65))],
        fill=(100, 116, 139, 150),
        width=max(2, size // 50)
    )

    img.save(output_path, "PNG")
    print(f"Generated {output_path} ({size}x{size})")

create_app_icon(192, icons_dir / "icon-192.png")
create_app_icon(512, icons_dir / "icon-512.png")
create_app_icon(180, icons_dir / "apple-touch-icon.png")
create_app_icon(32, icons_dir / "favicon-32.png")
