import pygame
import random
import math
import os
import glob
import time # Not strictly needed for texture creation, but was in original

# PxANIC! Color Palette
P = {
    'VOID': (5, 5, 8),
    'WHITE': (200, 200, 205), 'BLACK': (25, 25, 30),
    'GREY_L': (150, 150, 160), 'GREY_M': (100, 100, 110), 'GREY_D': (50, 50, 60),
    'RED': (150, 50, 50), 'GREEN': (50, 90, 50), 'BLUE': (50, 70, 130),
    'YELLOW': (170, 150, 40), 'ORANGE': (150, 80, 30),
    'BROWN_L': (130, 100, 60), 'BROWN_M': (90, 60, 40), 'BROWN_D': (50, 35, 20),
    'WOOD_BASE': (90, 50, 30), 'WOOD_LIGHT': (120, 80, 50), 'WOOD_SHADOW': (50, 25, 15),
    'STONE_BASE': (70, 75, 85), 'STONE_LIGHT': (100, 105, 115), 'STONE_SHADOW': (40, 40, 50),
    'CONCRETE': (110, 110, 115), 'ASPHALT': (50, 50, 55), 'MARBLE': (200, 200, 210),
    'WATER_BASE': (40, 60, 100), 'WATER_LIGHT': (80, 120, 200), 'ICE_BASE': (180, 210, 230),
    'DIRT_BASE': (80, 65, 45), 'SAND_BASE': (170, 160, 110),
    'GRASS_BASE': (40, 70, 50), 'GRASS_LIGHT': (70, 110, 70), 'GRASS_SHADOW': (20, 35, 20),
    'BRICK_RED': (120, 50, 40), 'GOLD': (180, 140, 40), 'LAMP_ON': (255, 240, 180),
    'METAL_BASE': (90, 90, 95), 'METAL_LIGHT': (140, 140, 150), 'METAL_RUST': (110, 60, 50),
}

# Drawing Helpers (from PxANIC! tiles.py)
def fill(s, c): s.fill(c)
def rect(s, c, r, w=0, **kwargs): pygame.draw.rect(s, c, r, w, **kwargs)
def line(s, c, p1, p2, w=1, **kwargs): pygame.draw.line(s, c, p1, p2, w, **kwargs)
def circle(s, c, p, r, w=0, **kwargs): pygame.draw.circle(s, c, p, r, w, **kwargs)
def pixel(s, c, p): 
    try: s.set_at(p, c)
    except: pass # Ignore out of bounds for safety
def poly(s, c, pts, w=0, **kwargs): pygame.draw.polygon(s, c, pts, w, **kwargs)

def blend(c1, c2, r):
    return (int(c1[0]*(1-r)+c2[0]*r), int(c1[1]*(1-r)+c2[1]*r), int(c1[2]*(1-r)+c2[2]*r))

def noise_color(color, intensity=15):
    var = random.randint(-intensity, intensity)
    return (max(0, min(255, color[0]+var)), max(0, min(255, color[1]+var)), max(0, min(255, color[2]+var)))

def draw_pro_noise(surf, color, intensity=20):
    surf.fill(color)
    for _ in range(150):
        x, y = random.randint(0, 31), random.randint(0, 31)
        pixel(surf, noise_color(color, intensity), (x, y))

def draw_pixel_bevel(surf, rect_obj, base_col, light_col, dark_col, thickness=1):
    pygame.draw.rect(surf, base_col, rect_obj)
    pygame.draw.line(surf, dark_col, rect_obj.bottomleft, (rect_obj.right, rect_obj.bottom), thickness)
    pygame.draw.line(surf, dark_col, (rect_obj.right-1, rect_obj.top), (rect_obj.right-1, rect_obj.bottom), thickness)
    pygame.draw.line(surf, light_col, rect_obj.topleft, (rect_obj.right, rect_obj.top), thickness)
    pygame.draw.line(surf, light_col, rect_obj.topleft, (rect_obj.left, rect_obj.bottom), thickness)

def draw_wood_base(surf, color, vertical=False):
    dark = blend(color, P['BLACK'], 0.3)
    draw_pro_noise(surf, color, 15)
    if vertical:
        for x in range(0, 32, 8):
            line(surf, dark, (x, 0), (x, 31))
    else:
        for y in range(0, 32, 8):
            line(surf, dark, (0, y), (31, y))

def draw_brick_base(surf, color):
    fill(surf, P['GREY_D'])
    for y in range(0, 32, 8):
        off = 8 if (y // 8) % 2 else 0
        for x in range(off - 16, 32, 16):
            r_obj = pygame.Rect(x + 1, y + 1, 14, 6)
            draw_pixel_bevel(surf, r_obj, color, blend(color, P['WHITE'], 0.15), blend(color, P['BLACK'], 0.3))

def draw_grass_detailed(surf, base_col):
    fill(surf, base_col)
    light, shadow = P['GRASS_LIGHT'], P['GRASS_SHADOW']
    for _ in range(15):
        cx, cy = random.randint(2, 28), random.randint(2, 28)
        line(surf, shadow, (cx, cy), (cx, cy+3), 1)
        pixel(surf, light, (cx-1, cy-1))
        pixel(surf, light, (cx+1, cy-1))
        pixel(surf, light, (cx, cy))

# --- Specific Tile Drawing Functions (from PxANIC! tiles.py) ---
# Each function draw_XXXX(s) draws a 32x32 texture onto the surface 's'
def draw_1110000(s): draw_pro_noise(s, P['DIRT_BASE'], 25)
def draw_1110001(s):
    fill(s, P['GRASS_BASE'])
    for _ in range(15):
        cx, cy = random.randint(2, 28), random.randint(2, 28)
        line(s, P['GRASS_SHADOW'], (cx, cy), (cx, cy+3))
        pixel(s, P['GRASS_LIGHT'], (cx-1, cy-1))
def draw_1110002(s):
    draw_pro_noise(s, P['GREY_M'], 10)
    for _ in range(15): circle(s, P['GREY_D'], (random.randint(4,27), random.randint(4,27)), 2)
def draw_1110003(s):
    draw_pro_noise(s, P['SAND_BASE'], 10)
    for y in [10, 22]:
        for x in range(0, 32, 4):
            pixel(s, P['BROWN_L'], (x, y + int(math.sin(x)*2)))
def draw_1110004(s):
    fill(s, P['WATER_BASE'])
    for y in range(4, 32, 8): line(s, P['WHITE'], (4, y), (12, y), 1)
def draw_1110005(s):
    draw_pro_noise(s, P['STONE_SHADOW'], 40)
    for _ in range(3): circle(s, P['BLACK'], (random.randint(5,25), random.randint(5,25)), 4)
def draw_1110006(s):
    draw_pro_noise(s, P['STONE_BASE'], 20)
    for _ in range(6): circle(s, P['GREEN'], (random.randint(4,27), random.randint(4,27)), random.randint(3,6))
def draw_1110007(s):
    draw_pro_noise(s, P['WOOD_LIGHT'], 15)
    for y in range(0, 32, 8): line(s, P['BROWN_D'], (0, y), (31, y))
def draw_1110008(s):
    draw_pro_noise(s, P['WOOD_BASE'], 15)
    for x in range(0, 32, 8): line(s, P['BROWN_D'], (x, 0), (x, 31))
def draw_1110009(s):
    draw_pro_noise(s, P['WHITE'], 5)
    for _ in range(3): line(s, P['GREY_L'], (random.randint(0,31), 0), (random.randint(0,31), 31))
def draw_1110010(s):
    draw_pro_noise(s, P['CONCRETE'], 10)
    rect(s, P['GREY_D'], (4, 4, 2, 2))
    rect(s, P['GREY_D'], (24, 24, 2, 2))
def draw_1110011(s):
    draw_pro_noise(s, P['ASPHALT'], 30)
    for _ in range(20): pixel(s, P['GREY_L'], (random.randint(0,31), random.randint(0,31)))
def draw_1110012(s):
    draw_pro_noise(s, P['ASPHALT'], 20)
    rect(s, P['WHITE'], (12, 2, 8, 28))
def draw_1110013(s):
    draw_pro_noise(s, P['CONCRETE'], 15)
    line(s, P['BLACK'], (16, 16), (4, 4))
    line(s, P['BLACK'], (16, 16), (28, 10))
def draw_1110014(s):
    fill(s, P['BLACK'])
    for i in range(4, 32, 8):
        line(s, P['METAL_BASE'], (i, 0), (i, 31), 2)
        line(s, P['METAL_BASE'], (0, i), (31, i), 2)
def draw_1110015(s):
    draw_pro_noise(s, P['ICE_BASE'], 5)
    line(s, (255, 255, 255, 150), (5, 5), (20, 25), 2)
def draw_1120016(s):
    fill(s, (20, 30, 60))
    for y in range(0, 32, 4): line(s, (10, 20, 40), (0, y), (31, y))
def draw_1120017(s):
    fill(s, P['RED'])
    for _ in range(5): circle(s, P['ORANGE'], (random.randint(4, 27), random.randint(4, 27)), 5)
    for _ in range(3): pixel(s, P['BLACK'], (random.randint(0, 31), random.randint(0, 31)))
def draw_1120018(s):
    fill(s, P['BROWN_D'])
    poly(s, P['BLACK'], [(0, 0), (15, 0), (0, 31)])
def draw_2110000(s):
    for y in range(0, 32, 16):
        for x in range(0, 32, 16):
            c = P['WHITE'] if (x+y)%32==0 else P['GREY_M']
            rect(s, c, (x, y, 16, 16))
            rect(s, P['BLACK'], (x, y, 16, 16), 1)
def draw_2110001(s):
    draw_pro_noise(s, P['RED'], 5)
    rect(s, P['GOLD'], (2, 2, 28, 28), 1)
    circle(s, P['GOLD'], (16, 16), 4, 1)
def draw_2110002(s):
    draw_pro_noise(s, P['BLUE'], 5)
    for i in range(4, 32, 8): line(s, P['WHITE'], (i, 4), (i, 28))
def draw_2110003(s):
    draw_pro_noise(s, P['WHITE'], 5)
    rect(s, P['GREY_L'], (0, 0, 32, 32), 1)
    line(s, P['GREY_L'], (16, 0), (16, 31))
    line(s, P['GREY_L'], (0, 16), (31, 16))
def draw_3220000(s):
    fill(s, P['GREY_D'])
    for y in range(0, 32, 8):
        off = 8 if (y//8)%2 else 0
        for x in range(off-16, 32, 16): rect(s, P['BRICK_RED'], (x+1, y+1, 14, 6))
def draw_3220001(s):
    fill(s, P['BLACK'])
    for y in range(0, 32, 8):
        for x in range(0, 32, 8): rect(s, P['STONE_BASE'], (x+1, y+1, 6, 6))
def draw_3220002(s):
    fill(s, P['STONE_BASE'])
    for y in range(0, 32, 8):
        off = 8 if (y // 8) % 2 else 0
        for x in range(off - 16, 32, 16):
            r_obj = pygame.Rect(x + 1, y + 1, 14, 6)
            draw_pixel_bevel(s, r_obj, P['STONE_BASE'], P['STONE_LIGHT'], P['STONE_SHADOW'])
    for _ in range(4): circle(s, blend(P['GREEN'], P['BLACK'], 0.2), (random.randint(5, 25), random.randint(5, 25)), random.randint(4, 7))
def draw_3220003(s):
    dark = blend(P['WOOD_BASE'], P['BLACK'], 0.3)
    draw_pro_noise(s, P['WOOD_BASE'], 15)
    for x in range(0, 32, 8): line(s, dark, (x, 0), (x, 31))
def draw_3220004(s):
    dark = blend(P['WOOD_SHADOW'], P['BLACK'], 0.3)
    draw_pro_noise(s, P['WOOD_SHADOW'], 15)
    for y in range(0, 32, 8): line(s, dark, (0, y), (31, y))
def draw_3220005(s):
    draw_pro_noise(s, P['WHITE'], 8)
    rect(s, P['GREY_M'], (0, 30, 32, 2))
def draw_3220006(s):
    draw_pro_noise(s, (200, 160, 160), 5)
    for y in range(4, 32, 12):
        for x in range(4, 32, 12): poly(s, P['RED'], [(x, y-3), (x+3, y), (x, y+3), (x-3, y)])
def draw_3220007(s):
    fill(s, (220, 230, 255))
    for i in range(0, 32, 8):
        line(s, (180, 190, 220), (i, 0), (i, 31))
        line(s, (180, 190, 220), (0, i), (31, i))
def draw_3220008(s):
    draw_pixel_bevel(s, pygame.Rect(0, 0, 32, 32), P['METAL_LIGHT'], P['WHITE'], P['BLACK'])
    circle(s, P['GREY_D'], (4, 4), 1)
    circle(s, P['GREY_D'], (28, 28), 1)
def draw_3220009(s):
    draw_pro_noise(s, P['METAL_BASE'], 10)
    for _ in range(12): circle(s, P['METAL_RUST'], (random.randint(0, 31), random.randint(0, 31)), random.randint(2, 4))
def draw_3220010(s):
    fill(s, (150, 200, 255, 100))
    line(s, P['WHITE'], (5, 31), (31, 5), 2)
def draw_3220011(s):
    fill(s, (150, 200, 255, 120))
    for i in range(0, 32, 8):
        line(s, P['BLACK'], (i, 0), (i, 31))
        line(s, P['BLACK'], (0, i), (31, i))
def draw_3220012(s):
    draw_pro_noise(s, P['BROWN_M'], 15)
    for x in range(0, 32, 8): line(s, P['BLACK'], (x, 0), (x, 31))
    for y in [6, 16, 26]:
        rect(s, P['BLACK'], (2, y, 28, 2))
        for x in range(4, 28, 4):
            if random.random() > 0.3: rect(s, random.choice([P['RED'], P['BLUE'], P['WHITE']]), (x, y-4, 3, 4))
def draw_3220013(s):
    draw_pro_noise(s, P['STONE_SHADOW'], 40)
    line(s, P['BLACK'], (0, 10), (12, 15), 2)
    line(s, P['BLACK'], (12, 15), (31, 12), 2)
def draw_4220000(s):
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_M'], (4, 0, 6, 32))
    rect(s, P['BROWN_M'], (22, 0, 6, 32))
    rect(s, P['BROWN_D'], (0, 6, 32, 4))
    rect(s, P['BROWN_D'], (0, 22, 32, 4))
def draw_4220001(s):
    fill(s, (0, 0, 0, 0))
    for x in [4, 12, 20, 28]: rect(s, P['METAL_BASE'], (x, 0, 2, 32))
    rect(s, P['GREY_D'], (0, 4, 32, 2))
def draw_4220002(s):
    fill(s, (0, 0, 0, 0))
    for x in range(4, 32, 8): rect(s, P['GREY_D'], (x, 0, 3, 32))
def draw_door(s, tid, name, col):
    # This is a complex function. It needs to know background (which is now done by Block3D base)
    # For now, let's simplify to match the 8251Ngine Block3D rendering with a simpler 2D top
    # We will let the Block3D's base cube render the sides.
    # This only draws the top face details for the door/chest.
    
    # Fill with base color (done by Block3D)
    # fill(s, P['STONE_SHADOW']) # No, let block3D decide base
    
    if "Open" in name:
        rect(s, P['BLACK'], (4, 4, 24, 24))
        rect(s, col, (24, 4, 4, 24))
    elif tid == 5310005: # Broken Door
        rect(s, P['BLACK'], (4, 4, 24, 24))
        line(s, col, (4, 4), (20, 20), 3)
    else: # Closed or Locked
        draw_pixel_bevel(s, pygame.Rect(4,4,24,24), col, blend(col, P['WHITE'], 0.2), blend(col, P['BLACK'], 0.3))
        if "Locked" in name:
            rect(s, P['GOLD'], (13, 14, 6, 5))
            circle(s, P['GOLD'], (16, 14), 2, 1)
        else: # Simple handle
            circle(s, P['YELLOW'], (22, 16), 2)
def draw_chest(s, tid, name):
    # This assumes Block3D provides the base
    if "Closed" in name:
        rect(s, P['WOOD_BASE'], (4, 8, 24, 16))
        rect(s, P['GOLD'], (14, 10, 4, 6)) # Lock
    else: # Open
        rect(s, P['WOOD_SHADOW'], (2, 2, 28, 6)) # Lid
        rect(s, P['WOOD_BASE'], (4, 8, 24, 16))
def draw_6310000(s): draw_flower(s, P['RED']) # Red Flower
def draw_6310001(s): draw_flower(s, P['YELLOW']) # Yellow Flower
def draw_6310002(s):
    fill(s, (0, 0, 0, 0)) # Transparent background
    for _ in range(3): line(s, P['GREEN'], (16, 31), (random.randint(10, 22), 10), 2) # Weeds
def draw_6310003(s):
    fill(s, (0, 0, 0, 0))
    circle(s, P['GREEN'], (16, 16), 12)
    poly(s, (0, 0, 0, 0), [(16, 16), (28, 8), (28, 24)]) # Lotus (partially transparent)
def draw_6310008(s):
    fill(s, (0, 0, 0, 0))
    rect(s, P['GREEN'], (13, 8, 6, 24)) # Cactus body
    rect(s, P['GREEN'], (6, 14, 8, 4)) # Arm
def draw_6310104(s):
    fill(s, (0, 0, 0, 0))
    for ox, oy in [(10, 14), (22, 14), (16, 8), (16, 22)]: circle(s, P['GRASS_BASE'], (ox, oy), 8) # Bush
def draw_6310105(s):
    fill(s, (0, 0, 0, 0))
    rect(s, P['GREEN'], (14, 10, 4, 22))
    circle(s, P['YELLOW'], (16, 8), 5) # Corn
def draw_6310106(s): # Tree Trunk
    fill(s, (0, 0, 0, 0))
    rect(s, P['WOOD_SHADOW'], (12, 0, 8, 32))
    line(s, P['BLACK'], (12, 10), (20, 10))
def draw_6310107(s): # Dead Tree
    fill(s, (0, 0, 0, 0))
    line(s, P['WOOD_SHADOW'], (16, 31), (16, 10), 3)
    line(s, P['WOOD_SHADOW'], (16, 20), (6, 10), 2)
def draw_7310000(s): # Pebble
    fill(s, (0, 0, 0, 0))
    circle(s, P['GREY_M'], (12, 20), 4)
    circle(s, P['GREY_L'], (20, 24), 3)
def draw_7310007(s): # Portal
    fill(s, (0, 0, 0, 0))
    for _ in range(5): circle(s, (100, 50, 200, 100), (16, 16), random.randint(5, 15))
def draw_7310008(s): # Exit Mark
    fill(s, (0, 0, 0, 0))
    poly(s, P['YELLOW'], [(4, 16), (16, 4), (16, 12), (28, 12), (28, 20), (16, 20), (16, 28)])
def draw_7310009(s): # Spike Trap
    fill(s, P['METAL_BASE'])
    for x in [8, 24]: poly(s, P['GREY_L'], [(x, 31), (x-4, 16), (x+4, 16)])
def draw_7310010(s): # Street Light
    fill(s, (0, 0, 0, 0))
    rect(s, P['METAL_BASE'], (15, 10, 2, 22))
    circle(s, P['LAMP_ON'], (16, 10), 6)
def draw_7310011(s): # CCTV Camera
    fill(s, (0, 0, 0, 0))
    poly(s, P['GREY_M'], [(4, 4), (16, 10), (4, 16)])
    circle(s, P['RED'], (16, 10), 2)
def draw_7310101(s): # Dense Fog
    fill(s, (200, 200, 200, 80))
    for _ in range(3): circle(s, (255, 255, 255, 40), (random.randint(8, 24), random.randint(8, 24)), 8)
def draw_7310102(s): # Shadow
    fill(s, (0, 0, 0, 0))
    circle(s, (0, 0, 0, 120), (16, 16), 12)
def draw_7310103(s): # Laundry
    fill(s, (0, 0, 0, 0))
    rect(s, P['WHITE'], (6, 6, 20, 24))
    circle(s, P['BLUE'], (16, 16), 6, 2)
def draw_7320005(s): # Fountain
    fill(s, (0, 0, 0, 0))
    rect(s, P['GREY_M'], (4, 24, 24, 6))
    rect(s, P['BLUE'], (14, 10, 4, 14))
def draw_7320006(s): # Well
    fill(s, (0, 0, 0, 0))
    circle(s, P['GREY_D'], (16, 16), 14, 3)
    circle(s, P['BLACK'], (16, 16), 10)
def draw_7320204(s): # Rock
    fill(s, (0, 0, 0, 0))
    poly(s, P['STONE_BASE'], [(8, 28), (4, 16), (16, 4), (28, 16), (24, 28)])
def draw_8310016(s): # Lamp
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_D'], (14, 20, 4, 12))
    poly(s, P['YELLOW'], [(8, 20), (24, 20), (16, 8)])
def draw_8310208(s): # Box
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_L'], (4, 8, 24, 20))
    line(s, P['BLACK'], (4, 8), (28, 28))
def draw_8320001(s): # Wood Chair
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_L'], (8, 4, 16, 16))
    rect(s, P['BROWN_M'], (8, 20, 3, 8))
def draw_8320004(s): # TV
    fill(s, (0, 0, 0, 0))
    rect(s, P['BLACK'], (2, 6, 28, 20))
    rect(s, P['GREY_D'], (4, 8, 24, 16))
def draw_8320007(s): # Piano
    fill(s, P['BLACK'])
    rect(s, P['WHITE'], (4, 20, 24, 8))
    for x in range(6, 28, 4): rect(s, P['BLACK'], (x, 20, 2, 5))
def draw_8320017(s): # Fireplace
    fill(s, P['BRICK_RED'])
    rect(s, P['BLACK'], (8, 12, 16, 20), border_top_left_radius=8)
def draw_8320018(s): # Exit Sign
    fill(s, P['GREEN'])
    rect(s, P['WHITE'], (6, 10, 20, 12), 1)
def draw_8320200(s): # Dining Table
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_M'], (2, 8, 28, 16))
    rect(s, P['BROWN_D'], (4, 24, 4, 6))
def draw_8320202(s): # Sofa
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_D'], (4, 8, 24, 16), border_radius=4)
def draw_8320203(s): # Bookshelf
    draw_wood_base(s, P['BROWN_M'], True)
    for y in [10, 22]: line(s, P['BLACK'], (2, y), (30, y), 2)
def draw_8320205(s): # Refrigerator
    fill(s, (0, 0, 0, 0))
    rect(s, P['WHITE'], (4, 2, 24, 28))
    line(s, P['GREY_M'], (4, 12), (28, 12))
def draw_8320209(s): # Closet
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_M'], (4, 2, 24, 28))
    line(s, P['BLACK'], (16, 2), (16, 30))
def draw_8320210(s): # Desk
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_M'], (2, 10, 28, 12))
    rect(s, P['BROWN_D'], (4, 22, 4, 8))
def draw_8320212(s): # Trash Can
    fill(s, (0, 0, 0, 0))
    rect(s, P['GREY_M'], (10, 10, 12, 18))
def draw_8320213(s): # Vent
    fill(s, P['GREY_M'])
    for i in range(6, 30, 6): line(s, P['BLACK'], (4, i), (28, i), 2)
def draw_8320214(s): # Drum Barrel
    fill(s, (0, 0, 0, 0))
    rect(s, P['RED'], (8, 4, 16, 24), border_radius=3)
def draw_8320215(s): # Toilet
    fill(s, (0, 0, 0, 0))
    circle(s, P['WHITE'], (16, 22), 8)
    rect(s, P['WHITE'], (8, 4, 16, 10))
def draw_8321006(s): # Vending Machine
    fill(s, (0, 0, 0, 0))
    rect(s, P['RED'], (4, 2, 24, 28))
    rect(s, P['BLACK'], (8, 6, 16, 12))
def draw_8321211(s): # Bed
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_D'], (2, 4, 28, 24))
    rect(s, P['WHITE'], (4, 6, 24, 8))
    rect(s, P['BLUE'], (4, 14, 24, 14))
def draw_9312000(s): draw_farm_base(s, 'Empty Field') # Empty Field
def draw_9312001(s): draw_farm_base(s, 'Sprout Field') # Sprout Field
def draw_9312002(s): draw_farm_base(s, 'Grown Field') # Grown Field
def draw_9312003(s): draw_1110004(s) # Fishing Spot is Shallow Water
def draw_9322004(s): # Iron Ore
    draw_pro_noise(s, P['STONE_SHADOW'], 20)
    for _ in range(4): circle(s, P['METAL_LIGHT'], (random.randint(8, 24), random.randint(8, 24)), 4)
def draw_9322005(s): # Rubble
    fill(s, (0, 0, 0, 0))
    for _ in range(6):
        pts_list = [(random.randint(0, 31), random.randint(0, 31)) for _ in range(3)]
        poly(s, P['GREY_M'], pts_list)
def draw_9322006(s): # Furnace
    fill(s, P['GREY_D'])
    rect(s, P['BLACK'], (8, 12, 16, 16), border_top_left_radius=8)
    circle(s, P['ORANGE'], (16, 22), 5)
def draw_9322007(s): # Cutting Board
    fill(s, (0, 0, 0, 0))
    rect(s, P['BROWN_L'], (4, 12, 24, 14))
    rect(s, P['WHITE'], (10, 14, 12, 8))
def draw_9322008(s): # Microscope
    fill(s, (0, 0, 0, 0))
    rect(s, P['BLACK'], (10, 24, 12, 4))
    line(s, P['BLACK'], (16, 24), (16, 10), 4)
def draw_9322009(s): # Surgery Table
    fill(s, P['METAL_LIGHT'])
    rect(s, P['RED'], (14, 2, 4, 4))
def draw_9322010(s): # Broken Panel
    draw_pro_noise(s, P['METAL_RUST'], 10)
    circle(s, P['YELLOW'], (16, 16), 2)
def draw_9322011(s): # Computer
    fill(s, P['METAL_BASE'])
    rect(s, P['BLACK'], (6, 6, 20, 14))

# Helper for farm tiles which share base drawing
def draw_farm_base(s, name):
    fill(s, P['DIRT_BASE'])
    for i in range(4, 32, 8):
        line(s, P['BROWN_D'], (0, i), (31, i), 1)
    if "Sprout" in name:
        line(s, P['GREEN'], (16, 20), (16, 12), 2)
    elif "Grown" in name:
        circle(s, P['ORANGE'], (16, 15), 4)

# Helper for flowers
def draw_flower(s, col):
    fill(s, (0, 0, 0, 0))
    line(s, P['GREEN'], (16, 31), (16, 16), 2)
    circle(s, col, (16, 12), 6)
    circle(s, P['YELLOW'], (16, 12), 2)


class TileEngine:
    TILE_DATA = {}
    TEXTURE_CACHE = {} # Memory cache
    
    # Disk cache settings (simplified, original had cleanup logic)
    # CACHE_DIR = "cache_tiles" # Removed for simplicity, rely on memory cache for now

    @staticmethod
    def init(data):
        TileEngine.TILE_DATA = data
        print(f"[TileEngine] Initialized with {len(data)} tiles")

    @staticmethod
    def create_texture(tid, size=32):
        """
        Creates a procedural texture for a given tile ID using PxANIC! logic.
        """
        if tid in TileEngine.TEXTURE_CACHE:
            return TileEngine.TEXTURE_CACHE[tid]

        s = pygame.Surface((size, size), pygame.SRCALPHA)
        tid_int = int(tid)
        
        d = TileEngine.TILE_DATA.get(str(tid_int), {}) # JSON keys are strings
        name = d.get('name', 'Unknown')
        col = tuple(d.get('color', P['GREY_M']))

        # Dispatch to specific drawing functions based on Tile ID
        if tid_int == 1110000: draw_1110000(s)
        elif tid_int == 1110001: draw_1110001(s)
        elif tid_int == 1110002: draw_1110002(s)
        elif tid_int == 1110003: draw_1110003(s)
        elif tid_int == 1110004: draw_1110004(s)
        elif tid_int == 1110005: draw_1110005(s)
        elif tid_int == 1110006: draw_1110006(s)
        elif tid_int == 1110007: draw_1110007(s)
        elif tid_int == 1110008: draw_1110008(s)
        elif tid_int == 1110009: draw_1110009(s)
        elif tid_int == 1110010: draw_1110010(s)
        elif tid_int == 1110011: draw_1110011(s)
        elif tid_int == 1110012: draw_1110012(s)
        elif tid_int == 1110013: draw_1110013(s)
        elif tid_int == 1110014: draw_1110014(s)
        elif tid_int == 1110015: draw_1110015(s)
        elif tid_int == 1120016: draw_1120016(s)
        elif tid_int == 1120017: draw_1120017(s)
        elif tid_int == 1120018: draw_1120018(s)
        elif tid_int == 2110000: draw_2110000(s)
        elif tid_int == 2110001: draw_2110001(s)
        elif tid_int == 2110002: draw_2110002(s)
        elif tid_int == 2110003: draw_2110003(s)
        elif tid_int == 3220000: draw_3220000(s)
        elif tid_int == 3220001: draw_3220001(s)
        elif tid_int == 3220002: draw_3220002(s)
        elif tid_int == 3220003: draw_3220003(s)
        elif tid_int == 3220004: draw_3220004(s)
        elif tid_int == 3220005: draw_3220005(s)
        elif tid_int == 3220006: draw_3220006(s)
        elif tid_int == 3220007: draw_3220007(s)
        elif tid_int == 3220008: draw_3220008(s)
        elif tid_int == 3220009: draw_3220009(s)
        elif tid_int == 3220010: draw_3220010(s)
        elif tid_int == 3220011: draw_3220011(s)
        elif tid_int == 3220012: draw_3220012(s)
        elif tid_int == 3220013: draw_3220013(s)
        elif tid_int == 4220000: draw_4220000(s)
        elif tid_int == 4220001: draw_4220001(s)
        elif tid_int == 4220002: draw_4220002(s)
        elif tid_int // 1000000 == 5: # Doors and Chests
            if tid_int in [5321025, 5310025]: draw_chest(s, tid_int, name)
            else: draw_door(s, tid_int, name, col)
        elif tid_int == 6310000: draw_6310000(s)
        elif tid_int == 6310001: draw_6310001(s)
        elif tid_int == 6310002: draw_6310002(s)
        elif tid_int == 6310003: draw_6310003(s)
        elif tid_int == 6310008: draw_6310008(s)
        elif tid_int == 6310104: draw_6310104(s)
        elif tid_int == 6310105: draw_6310105(s)
        elif tid_int == 6310106: draw_6310106(s)
        elif tid_int == 6310107: draw_6310107(s)
        elif tid_int == 7310000: draw_7310000(s)
        elif tid_int == 7310007: draw_7310007(s)
        elif tid_int == 7310008: draw_7310008(s)
        elif tid_int == 7310009: draw_7310009(s)
        elif tid_int == 7310010: draw_7310010(s)
        elif tid_int == 7310011: draw_7310011(s)
        elif tid_int == 7310101: draw_7310101(s)
        elif tid_int == 7310102: draw_7310102(s)
        elif tid_int == 7310103: draw_7310103(s)
        elif tid_int == 7320005: draw_7320005(s)
        elif tid_int == 7320006: draw_7320006(s)
        elif tid_int == 7320204: draw_7320204(s)
        elif tid_int == 8310016: draw_8310016(s)
        elif tid_int == 8310208: draw_8310208(s)
        elif tid_int == 8320001: draw_8320001(s)
        elif tid_int == 8320004: draw_8320004(s)
        elif tid_int == 8320007: draw_8320007(s)
        elif tid_int == 8320017: draw_8320017(s)
        elif tid_int == 8320018: draw_8320018(s)
        elif tid_int == 8320200: draw_8320200(s)
        elif tid_int == 8320202: draw_8320202(s)
        elif tid_int == 8320203: draw_8320203(s)
        elif tid_int == 8320205: draw_8320205(s)
        elif tid_int == 8320209: draw_8320209(s)
        elif tid_int == 8320210: draw_8320210(s)
        elif tid_int == 8320212: draw_8320212(s)
        elif tid_int == 8320213: draw_8320213(s)
        elif tid_int == 8320214: draw_8320214(s)
        elif tid_int == 8320215: draw_8320215(s)
        elif tid_int == 8321006: draw_8321006(s)
        elif tid_int == 8321211: draw_8321211(s)
        elif tid_int == 9312000: draw_farm_base(s, 'Empty Field')
        elif tid_int == 9312001: draw_farm_base(s, 'Sprout Field')
        elif tid_int == 9312002: draw_farm_base(s, 'Grown Field')
        elif tid_int == 9312003: draw_1110004(s) # Fishing Spot is Shallow Water
        elif tid_int == 9322004: draw_9322004(s)
        elif tid_int == 9322005: draw_9322005(s)
        elif tid_int == 9322006: draw_9322006(s)
        elif tid_int == 9322007: draw_9322007(s)
        elif tid_int == 9322008: draw_9322008(s)
        elif tid_int == 9322009: draw_9322009(s)
        elif tid_int == 9322010: draw_9322010(s)
        elif tid_int == 9322011: draw_9322011(s)
        else:
            # Fallback procedural noise if no specific drawing function
            draw_pro_noise(s, col, 20)

        TileEngine.TEXTURE_CACHE[tid] = s
        return s

    @staticmethod
    def get_tile_category(tid): return int(tid) // 1000000 # Helper for other modules