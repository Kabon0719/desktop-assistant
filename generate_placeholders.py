import os
import math
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "animations")

def get_font(size=14):
    try:
        # Windows default fonts
        return ImageFont.truetype("msyh.ttc", size) # Microsoft YaHei
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def draw_monk_base(draw, center_x, center_y, scale=1.0, monk_color=(235, 140, 40, 255), skin_color=(255, 215, 180, 255)):
    """繪製基本Q版武僧造型 (光頭、僧袍)"""
    head_r = int(24 * scale)
    head_center = (center_x, center_y - int(25 * scale))
    
    # 僧袍 (身體)
    body_w = int(32 * scale)
    body_h = int(38 * scale)
    draw.polygon([
        (center_x - body_w, center_y + body_h),
        (center_x + body_w, center_y + body_h),
        (center_x + int(body_w * 0.7), center_y),
        (center_x - int(body_w * 0.7), center_y)
    ], fill=monk_color, outline=(180, 90, 10, 255), width=2)
    
    # 袈裟紅色斜帶
    draw.line([
        (center_x - int(body_w * 0.5), center_y),
        (center_x + int(body_w * 0.7), center_y + body_h)
    ], fill=(200, 30, 30, 255), width=int(5 * scale))

    # 光頭頭部
    draw.ellipse([
        head_center[0] - head_r, head_center[1] - head_r,
        head_center[0] + head_r, head_center[1] + head_r
    ], fill=skin_color, outline=(190, 140, 100, 255), width=2)
    
    # 戒疤 (三個小點)
    for i in [-6, 0, 6]:
        dot_x = head_center[0] + int(i * scale)
        dot_y = head_center[1] - int(14 * scale)
        draw.ellipse([dot_x-1, dot_y-1, dot_x+1, dot_y+1], fill=(160, 100, 60, 255))

    # 眼睛與笑臉
    eye_y = head_center[1] - int(2 * scale)
    draw.arc([head_center[0] - int(12*scale), eye_y - 2, head_center[0] - int(4*scale), eye_y + 4], start=180, end=360, fill=(40, 40, 40, 255), width=2)
    draw.arc([head_center[0] + int(4*scale), eye_y - 2, head_center[0] + int(12*scale), eye_y + 4], start=180, end=360, fill=(40, 40, 40, 255), width=2)
    draw.arc([head_center[0] - int(5*scale), eye_y + int(8*scale), head_center[0] + int(5*scale), eye_y + int(14*scale)], start=0, end=180, fill=(180, 50, 50, 255), width=2)

def generate_train_meditate(size=300, frames=12):
    """修煉動畫 A: 盤腿冥想，光環起伏"""
    out_dir = os.path.join(ASSETS_DIR, "train_meditate")
    ensure_dir(out_dir)
    font = get_font(16)
    
    for i in range(frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx, cy = size // 2, size // 2 + 10
        phase = math.sin(i / frames * 2 * math.pi)
        
        # 冥想光環 (呼吸效果)
        aura_r = int(70 + phase * 8)
        aura_alpha = int(90 + phase * 40)
        draw.ellipse([cx - aura_r, cy - aura_r, cx + aura_r, cy + aura_r], 
                     outline=(255, 215, 0, aura_alpha), width=3)
        draw.ellipse([cx - aura_r + 10, cy - aura_r + 10, cx + aura_r - 10, cy + aura_r - 10], 
                     outline=(255, 170, 0, aura_alpha // 2), width=2)
        
        # 身體些微浮動
        draw_monk_base(draw, cx, cy + int(phase * 3), scale=1.1)
        
        # 標籤文字
        draw.text((cx - 45, size - 35), "【修煉：靜心打坐】", font=font, fill=(255, 230, 150, 240))
        
        img.save(os.path.join(out_dir, f"frame_{i:02d}.png"))
    print("Generated train_meditate frames.")

def generate_train_dummy(size=300, frames=12):
    """修煉動畫 B: 木人樁練拳，左右交替出拳"""
    out_dir = os.path.join(ASSETS_DIR, "train_dummy")
    ensure_dir(out_dir)
    font = get_font(16)
    
    for i in range(frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx, cy = size // 2 - 25, size // 2 + 10
        phase = i % 6
        is_left = (i // 6) == 0
        
        # 繪製木人樁
        dummy_x = size // 2 + 55
        draw.rectangle([dummy_x - 12, cy - 60, dummy_x + 12, cy + 60], fill=(140, 85, 35, 255), outline=(90, 50, 20, 255), width=2)
        # 木樁木臂
        draw.rectangle([dummy_x - 30, cy - 20, dummy_x + 12, cy - 10], fill=(160, 100, 45, 255))
        draw.rectangle([dummy_x - 25, cy + 10, dummy_x + 12, cy + 20], fill=(160, 100, 45, 255))
        
        # 武僧
        draw_monk_base(draw, cx, cy, scale=1.1)
        
        # 出拳特效
        punch_reach = phase * 6
        if is_left:
            punch_x = cx + 25 + punch_reach
            punch_y = cy - 15
        else:
            punch_x = cx + 25 + punch_reach
            punch_y = cy + 10
            
        draw.ellipse([punch_x - 8, punch_y - 8, punch_x + 8, punch_y + 8], fill=(255, 215, 180, 255), outline=(180, 90, 10, 255), width=2)
        if phase >= 3:
            # 撞擊風紋
            draw.arc([punch_x + 5, punch_y - 12, punch_x + 20, punch_y + 12], start=270, end=90, fill=(255, 255, 100, 200), width=3)
            
        draw.text((size // 2 - 50, size - 35), "【修煉：木人樁拳法】", font=font, fill=(255, 230, 150, 240))
        img.save(os.path.join(out_dir, f"frame_{i:02d}.png"))
    print("Generated train_dummy frames.")

def generate_ask_fist(size=300, frames=10):
    """詢問待命 A: 抱拳以禮相待，微動呼吸"""
    out_dir = os.path.join(ASSETS_DIR, "ask_fist")
    ensure_dir(out_dir)
    font = get_font(16)
    
    for i in range(frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2 + 10
        phase = math.sin(i / frames * 2 * math.pi)
        
        draw_monk_base(draw, cx, cy + int(phase * 2), scale=1.2)
        
        # 抱拳手勢
        hand_y = cy + int(phase * 2) + 5
        draw.ellipse([cx - 15, hand_y - 8, cx, hand_y + 8], fill=(255, 215, 180, 255), outline=(180, 90, 10, 255), width=2)
        draw.rectangle([cx - 2, hand_y - 8, cx + 15, hand_y + 8], fill=(255, 215, 180, 255), outline=(180, 90, 10, 255), width=2)
        
        draw.text((cx - 45, size - 35), "【待命：抱拳候教】", font=font, fill=(180, 230, 255, 250))
        img.save(os.path.join(out_dir, f"frame_{i:02d}.png"))
    print("Generated ask_fist frames.")

def generate_ask_pray(size=300, frames=10):
    """詢問待命 B: 雙手合十念佛"""
    out_dir = os.path.join(ASSETS_DIR, "ask_pray")
    ensure_dir(out_dir)
    font = get_font(16)
    
    for i in range(frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2 + 10
        phase = math.sin(i / frames * 2 * math.pi)
        
        draw_monk_base(draw, cx, cy + int(phase * 2), scale=1.2)
        
        # 合十雙手
        hand_y = cy + int(phase * 2) + 2
        draw.polygon([
            (cx - 8, hand_y + 12),
            (cx, hand_y - 12),
            (cx + 8, hand_y + 12)
        ], fill=(255, 215, 180, 255), outline=(180, 90, 10, 255), width=2)
        
        draw.text((cx - 45, size - 35), "【待命：合十聽令】", font=font, fill=(180, 230, 255, 250))
        img.save(os.path.join(out_dir, f"frame_{i:02d}.png"))
    print("Generated ask_pray frames.")

def generate_act_punch(size=300, frames=12):
    """一次性動作: 爆喝出拳 / 猛虎推掌發功"""
    out_dir = os.path.join(ASSETS_DIR, "act_punch")
    ensure_dir(out_dir)
    font = get_font(18)
    
    for i in range(frames):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2 + 10
        
        # 聚氣 (0-3), 出拳 (4-8), 收勢 (9-11)
        if i <= 3:
            # 蓄力後撤
            scale = 1.15
            shift_x = - (i * 4)
            draw_monk_base(draw, cx + shift_x, cy, scale=scale)
            # 藍色氣旋
            r = (i + 1) * 12
            draw.ellipse([cx + shift_x - r, cy - r, cx + shift_x + r, cy + r], outline=(100, 200, 255, 180), width=2)
            draw.text((cx - 30, size - 35), "【蓄力...】", font=font, fill=(100, 220, 255, 250))
        elif 4 <= i <= 8:
            # 破空出拳！
            scale = 1.3
            shift_x = (i - 3) * 12
            draw_monk_base(draw, cx + 15, cy, scale=scale)
            # 大金色拳風衝擊波
            blast_r = (i - 3) * 22
            blast_x = cx + 55 + shift_x
            draw.ellipse([blast_x - blast_r, cy - blast_r, blast_x + blast_r, cy + blast_r], 
                         fill=(255, 230, 100, 120), outline=(255, 120, 0, 240), width=4)
            draw.text((cx - 40, size - 35), "【破！出拳！】", font=font, fill=(255, 80, 80, 255))
        else:
            # 收招
            scale = 1.2
            draw_monk_base(draw, cx, cy, scale=scale)
            draw.text((cx - 40, size - 35), "【收勢如山】", font=font, fill=(200, 255, 200, 240))
            
        img.save(os.path.join(out_dir, f"frame_{i:02d}.png"))
    print("Generated act_punch frames.")

if __name__ == "__main__":
    generate_train_meditate()
    generate_train_dummy()
    generate_ask_fist()
    generate_ask_pray()
    generate_act_punch()
    print("All placeholder animation frames generated successfully!")
