from PIL import Image, ImageDraw
import math

def create_sun(path, color="#CCCCCC", size=100):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    radius = size // 4
    
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    
    ray_len = size // 5
    ray_width = max(2, size // 15)
    
    for i in range(8):
        angle = i * (math.pi / 4)
        x1 = cx + math.cos(angle) * (radius + size // 15)
        y1 = cy + math.sin(angle) * (radius + size // 15)
        x2 = cx + math.cos(angle) * (radius + ray_len + size // 15)
        y2 = cy + math.sin(angle) * (radius + ray_len + size // 15)
        draw.line([x1, y1, x2, y2], fill=color, width=ray_width)
        
    img.save(path)

def create_moon(path, color="#555555", size=100):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    
    mask = Image.new("L", (size, size), 0)
    m_draw = ImageDraw.Draw(mask)
    cx, cy = size // 2, size // 2
    radius = size // 3
    
    m_draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255)
    
    offset_x, offset_y = size // 6, -size // 10
    m_draw.ellipse([cx - radius + offset_x, cy - radius + offset_y, cx + radius + offset_x, cy + radius + offset_y], fill=0)
    
    solid = Image.new("RGBA", (size, size), color)
    img = Image.composite(solid, Image.new("RGBA", (size, size), (0,0,0,0)), mask)
    img.save(path)

# Sun will be displayed in Dark Mode (needs to be light gray)
create_sun("static/sun.png", color="#CCCCCC")
# Moon will be displayed in Light Mode (needs to be dark gray)
create_moon("static/moon.png", color="#666666")
