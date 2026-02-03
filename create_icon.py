#!/usr/bin/env python3
"""Generate DealBot icon."""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a professional DealBot icon."""
    sizes = [1024, 512, 256, 128, 64, 32, 16]
    
    for size in sizes:
        # Create image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate dimensions
        padding = size // 10
        
        # Draw main circle with solid color
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=(41, 128, 185, 255),  # Solid blue
            outline=(52, 152, 219, 255),  # Lighter blue outline
            width=max(3, size // 64)
        )
        
        # Draw shopping tag icon
        tag_size = size // 3
        tag_x = size // 2 - tag_size // 2
        tag_y = size // 2 - tag_size // 2
        
        # Tag body (rectangle with rounded corner)
        tag_points = [
            (tag_x, tag_y),
            (tag_x + tag_size, tag_y),
            (tag_x + tag_size, tag_y + tag_size - tag_size // 4),
            (tag_x + tag_size // 2, tag_y + tag_size),
            (tag_x, tag_y + tag_size - tag_size // 4),
        ]
        draw.polygon(tag_points, fill=(255, 255, 255, 255))
        
        # Draw percentage symbol
        try:
            font_size = max(12, size // 4)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            text = "%"
            # Get text bbox to center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = size // 2 - text_width // 2
            text_y = size // 2 - text_height // 2 - size // 20
            
            draw.text((text_x, text_y), text, fill=(41, 128, 185, 255), font=font)
        except:
            # Fallback if font fails
            pass
        
        # Save PNG
        output_dir = 'resources'
        os.makedirs(output_dir, exist_ok=True)
        img.save(f'{output_dir}/icon-{size}.png', 'PNG')
        print(f"Created {size}x{size} icon")
    
    # Also create a simple unified icon.png for Briefcase
    img = Image.open('resources/icon-1024.png')
    img.save('resources/icon.png', 'PNG')
    print("Created resources/icon.png")

if __name__ == '__main__':
    create_icon()
    print("\n✅ All icons created successfully!")
