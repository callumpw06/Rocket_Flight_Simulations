import math
import base64
import os

def get_base64_image(filepath):
    ext = filepath.split('.')[-1].lower()
    mime_type = "image/png"
    if ext in ['jpg', 'jpeg']:
        mime_type = "image/jpeg"
    elif ext == 'webp':
        mime_type = "image/webp"

    if not os.path.exists(filepath):
        print(f"Warning: '{filepath}' not found. Using linked path instead.")
        return filepath

    with open(filepath, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{b64_string}"

# --- Dimensions ---
diameter_mm = 6 * 25.4 
length_mm = 500
circumference_base = math.pi * diameter_mm
circumference_total = circumference_base + 15 

W = round(length_mm, 3) 
H = round(circumference_total, 3) 

q_height = circumference_base / 4
c0   = q_height * 0.5 
c90  = q_height * 1.5 
c180 = q_height * 2.5 
c270 = q_height * 3.5 

x_mid = W / 2
x_left = W / 2 - 75
x_right = W / 2 + 75

# Bounding boxes reduced to 75x75 (and LAS to 95x75) for slightly smaller logos
logos = [
    ("./logos/dusf-planet.png", x_mid, c0, 75, 75), 
    ("./logos/durham-university-shield.png", x_left, c90, 75, 75),
    ("./logos/launch-4-change.png", x_right, c90, 75, 75),
    ("./logos/viper.webp", x_left, c180, 75, 75),
    ("./logos/amnovis-preferred.png", x_right, c180, 75, 75),
    ("./logos/laser-additive-solutions.png", x_left, c270, 95, 75) 
]

blend_modes = {
    "./logos/durham-university-shield.png": 'style="mix-blend-mode: multiply;"',
    "./logos/launch-4-change.png": 'style="mix-blend-mode: multiply;"'
}

image_tags = ""
for href, cx, cy, bw, bh in logos:
    x = cx - (bw / 2)
    y = cy - (bh / 2)
    style = blend_modes.get(href, "")
    embedded_href = get_base64_image(href)
    image_tags += f'        <image href="{embedded_href}" x="{x:.3f}" y="{y:.3f}" width="{bw}" height="{bh}" preserveAspectRatio="xMidYMid meet" transform="rotate(-90 {cx} {cy})" {style}/>\n'

# --- Custom Text Generation ---
text_cx = x_right 
text_cy = c270    

text_tags = f'''
        <g transform="rotate(-90 {text_cx} {text_cy})">
            <text x="{text_cx - 4}" y="{text_cy - 6}" font-family="Montserrat, 'Segoe UI', sans-serif" font-size="12" font-weight="bold" fill="#333333" text-anchor="middle">PHYSICS MES</text>
            <text x="{text_cx - 4}" y="{text_cy + 10}" font-family="Montserrat, 'Segoe UI', sans-serif" font-size="12" font-weight="bold" fill="#333333" text-anchor="middle">WORKSHOP</text>
        </g>
'''

# --- SVG Generation ---
svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">
    <defs>
        <linearGradient id="marbleColors" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#ffffff"/>
            <stop offset="20%" stop-color="#c2e0ff"/> 
            <stop offset="45%" stop-color="#ffffff"/>
            <stop offset="70%" stop-color="#e0c2ed"/> 
            <stop offset="100%" stop-color="#ffffff"/>
        </linearGradient>

        <filter id="marbleFilter" filterUnits="userSpaceOnUse" x="-100" y="-100" width="{W + 200}" height="{H + 200}">
            <feTurbulence type="fractalNoise" baseFrequency="0.005 0.009" numOctaves="5" result="turbulence"/>
            <feDisplacementMap in="SourceGraphic" in2="turbulence" scale="250" xChannelSelector="R" yChannelSelector="G"/>
        </filter>
        
        <clipPath id="body-cutout">
            <rect x="0" y="0" width="{W}" height="{H}" />
        </clipPath>
    </defs>
    
    <g clip-path="url(#body-cutout)">
        <rect x="-100" y="-100" width="{W + 200}" height="{H + 200}" fill="url(#marbleColors)" filter="url(#marbleFilter)" />
{image_tags}
{text_tags}
    </g>
    
    <rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="black" stroke-width="1"/>
</svg>"""

filename = "body_tube_vinyl_template.svg"
with open(filename, "w", encoding="utf-8") as f:
    f.write(svg_content)
    
print(f"Saved self-contained vector path to '{filename}'")