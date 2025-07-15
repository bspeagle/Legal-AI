"""
Create a logo image for the Legal AI Virtual Courtroom
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create a new image with a transparent background
width, height = 300, 300
image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Draw a gavel icon
# Main part (head of gavel)
draw.ellipse((60, 60, 180, 130), fill=(50, 50, 100, 255), outline=(30, 30, 80, 255), width=2)
# Handle of gavel
draw.rectangle((140, 120, 220, 140), fill=(120, 80, 40, 255), outline=(80, 50, 20, 255), width=2)
# Strike plate
draw.rectangle((60, 170, 140, 190), fill=(50, 50, 100, 255), outline=(30, 30, 80, 255), width=2)

# Draw a scale of justice
# Center post
draw.rectangle((190, 150, 210, 220), fill=(50, 50, 100, 255), outline=(30, 30, 80, 255), width=2)
# Top bar
draw.rectangle((150, 150, 250, 160), fill=(50, 50, 100, 255), outline=(30, 30, 80, 255), width=2)
# Left plate
draw.ellipse((140, 180, 170, 200), fill=(120, 120, 170, 255), outline=(80, 80, 140, 255), width=2)
# Right plate
draw.ellipse((230, 180, 260, 200), fill=(120, 120, 170, 255), outline=(80, 80, 140, 255), width=2)

# Add some text - "Legal AI"
try:
    font = ImageFont.truetype("Arial", 42)
except:
    font = ImageFont.load_default()

draw.text((80, 220), "Legal AI", fill=(30, 30, 80, 255), font=font)

# Save the image
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
image.save(logo_path)

print(f"Logo saved to {logo_path}")
