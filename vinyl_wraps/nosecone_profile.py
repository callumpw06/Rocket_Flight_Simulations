import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({
    'font.size': 18,
    'axes.titlesize': 18,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["cmr10"],
    "mathtext.fontset": "cm",
    "axes.formatter.use_mathtext": True,
})

# --- Dimensions ---
R = 0.076          
L_nose = 0.456     
# Dynamically calculates cylinder length to hit 1.2m exactly    
C_haack = 1/3      
num_gores = 1      
cutoff = 0.090 
L_cyl = 1.0 - L_nose + cutoff    

# --- 1. Nosecone Geometry ---
x_nose = np.linspace(cutoff, L_nose, 1000)

theta = np.arccos(1 - (2 * x_nose) / L_nose)
r_nose = (R / np.sqrt(np.pi)) * np.sqrt(theta - (np.sin(2*theta)/2) + C_haack * (np.sin(theta)**3))

s_nose = np.zeros_like(x_nose)
for i in range(1, len(x_nose)):
    dx = x_nose[i] - x_nose[i-1]
    dr = r_nose[i] - r_nose[i-1]
    s_nose[i] = s_nose[i-1] + np.sqrt(dx**2 + dr**2)

# --- 2. Cylinder Geometry ---
x_cyl = np.linspace(0, L_cyl, 100)
r_cyl = np.full_like(x_cyl, R)

s_cyl = s_nose[-1] + x_cyl

# --- 3. Combine and Unroll ---
s_total = np.concatenate((s_nose, s_cyl))
r_total = np.concatenate((r_nose, r_cyl))

circumference = ((2 * np.pi * r_total) / num_gores) + 0.015

y_top = circumference / 2
y_bottom = -circumference / 2

# --- 4. Export to CSV ---
flat_pattern_df = pd.DataFrame({
    'Surface_Distance_m (X)': s_total,
    'Top_Edge_m (Y)': y_top,
    'Bottom_Edge_m (Y)': y_bottom
})
flat_pattern_df.to_csv("./nosecone_vinyl_template.csv", index=False)
print("Saved raw coordinates to 'nosecone_vinyl_template.csv'")

# --- 5. Export HIGH-DEF Vector Marble SVG ---
x_mm = s_total * 1000
y_top_mm = y_top * 1000
y_bottom_mm = y_bottom * 1000

width_mm = np.max(x_mm)
height_mm = np.max(y_top_mm) - np.min(y_bottom_mm)

max_y = np.max(y_top_mm)
y_top_svg = max_y - y_top_mm
y_bottom_svg = max_y - y_bottom_mm

points_str = ""
for x, y in zip(x_mm, y_top_svg):
    points_str += f"{x:.3f},{y:.3f} "
for x, y in zip(reversed(x_mm), reversed(y_bottom_svg)):
    points_str += f"{x:.3f},{y:.3f} "

svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" viewBox="0 0 {width_mm} {height_mm}">
    <defs>
        <linearGradient id="marbleColors" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#ffffff"/>
            <stop offset="20%" stop-color="#c2e0ff"/> 
            <stop offset="45%" stop-color="#ffffff"/>
            <stop offset="70%" stop-color="#e0c2ed"/> 
            <stop offset="100%" stop-color="#ffffff"/>
        </linearGradient>

        <filter id="marbleFilter" filterUnits="userSpaceOnUse" x="-500" y="-500" width="{width_mm + 1000}" height="{height_mm + 1000}">
            <feTurbulence type="fractalNoise" baseFrequency="0.005 0.009" numOctaves="5" result="turbulence"/>
            <feDisplacementMap in="SourceGraphic" in2="turbulence" scale="250" xChannelSelector="R" yChannelSelector="G"/>
        </filter>
        
        <clipPath id="nosecone-cutout">
            <polygon points="{points_str.strip()}"/>
        </clipPath>
    </defs>
    
    <g clip-path="url(#nosecone-cutout)">
        <rect x="-500" y="-500" width="{width_mm + 1000}" height="{height_mm + 1000}" fill="url(#marbleColors)" filter="url(#marbleFilter)" />
    </g>
    
    <polygon points="{points_str.strip()}" fill="none" stroke="black" stroke-width="1"/>
</svg>'''

with open("nosecone_vinyl_template.svg", "w") as f:
    f.write(svg_content)
print("Saved High-Def vector marble path to 'nosecone_vinyl_template.svg'")

# --- 6. Plot the Template Shape (Preview) ---
plt.figure(figsize=(10, 4))
plt.plot(s_total, y_top, 'b-', label='Outer Edge')
plt.plot(s_total, y_bottom, 'b-')
plt.fill_between(s_total, y_top, y_bottom, color='blue', alpha=0.1)

plt.title(f"2D Flat Pattern Template (LV-Haack + {L_cyl*100:.1f}cm Cylinder)")
plt.xlabel("Surface Distance from Cut Edge (m)")
plt.ylabel("Unrolled Width (m)")
plt.axvline(x=s_nose[-1], color='r', linestyle='--', label='Nose-to-Cylinder Transition')
plt.legend()
plt.grid(True)
plt.axis('equal') 
plt.tight_layout()
plt.savefig("./nosecone_vinyl_template.png", dpi=300)
plt.show()