import os
import zipfile

# 检查如果只有压缩包，没有解压后的字体，就自动在云端解压它
if os.path.exists("fonts/general_bold.zip") and not os.path.exists("fonts/general_bold.ttf"):
    with zipfile.ZipFile("fonts/general_bold.zip", 'r') as zip_ref:
        zip_ref.extractall("fonts/")
import streamlit as st
import random
import os
import colorsys
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from colorthief import ColorThief

# ====================================================================
# 🔴 【核心设置】Streamlit 配置与 2K 极简皮肤注入
# ====================================================================
st.set_page_config(
    page_title="游戏买量图批量生成系统", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 注入极简主义 CSS：框定 2K 屏幕视觉布局，去除冗余间距，增加分层色块
st.markdown("""
    <style>
        /* 框定大屏优化，防止 2K 屏幕下内容极度拉伸 */
        .main .block-container {
            max-width: 2560px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
        }
        
        /* 标题与文字样式简化 */
        h1, h2, h3 {
            font-weight: 600 !important;
            color: #222222 !important;
        }

        .tool-hero {
            padding: 22px 0 18px 0;
            border-bottom: 1px solid #e5e7eb;
            margin-bottom: 22px;
        }
        .tool-title {
            font-size: 34px;
            line-height: 1.2;
            font-weight: 700;
            color: #111827;
            margin: 0 0 8px 0;
        }
        .tool-subtitle {
            font-size: 14px;
            color: #4b5563;
            margin: 0;
        }
        .step-hint {
            color: #6b7280;
            font-size: 13px;
            margin: -6px 0 8px 0;
        }
        .result-toolbar {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px 16px 16px;
            margin-bottom: 14px;
        }
        .result-toolbar-title {
            font-size: 16px;
            font-weight: 650;
            color: #111827;
            margin-bottom: 4px;
        }
        .result-toolbar-desc {
            color: #6b7280;
            font-size: 13px;
            margin-bottom: 10px;
        }
        div.stDownloadButton > button {
            font-weight: 600 !important;
        }
        
        /* 操作区步骤卡片分层色块 (Expander / Container) */
        div[data-testid="stExpander"] {
            background-color: #f8f9fa !important;
            border: 1px solid #e9ecef !important;
            border-radius: 6px !important;
        }
        
        /* 单独微调模式下的 Tabs 色块分层 */
        div[data-testid="stTabs"] button {
            background-color: #f1f3f5 !important;
            margin-right: 4px !important;
            border-radius: 4px 4px 0 0 !important;
            color: #495057 !important;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            background-color: #212529 !important;
            color: #ffffff !important;
        }

        /* 优化布局组件间距 */
        [data-testid="stVerticalBlockBorderWrapper"] > div > div { justify-content: flex-start !important; }
        [data-testid="stVerticalBlock"] { gap: 0.55rem !important; }
        div[data-testid="stFormElement"] { margin-bottom: 0px !important; }
    </style>
""", unsafe_allow_html=True)

# 自动创建模板4所需的图库文件夹
T4_DIR = "template4_cards"
if not os.path.exists(T4_DIR):
    os.makedirs(T4_DIR)

# ==================== 1. 初始化系统状态 ====================
if 'random_seed' not in st.session_state:
    st.session_state.random_seed = random.randint(0, 99999)

if 'is_shuffled' not in st.session_state:
    st.session_state.is_shuffled = False

if 'custom_main_title' not in st.session_state:
    st.session_state.custom_main_title = "和对象第一次玩到凌晨"
if 'custom_sub_title' not in st.session_state:
    st.session_state.custom_sub_title = "这游戏也太解压了吧！"

if 'custom_tag_text' not in st.session_state:
    st.session_state.custom_tag_text = "App Store"

if 'lock_copywriting' not in st.session_state:
    st.session_state.lock_copywriting = False
if 'lock_background' not in st.session_state:
    st.session_state.lock_background = False

if 'individual_configs' not in st.session_state:
    st.session_state.individual_configs = {}

if 'forked_cards' not in st.session_state:
    st.session_state.forked_cards = set()

if 'individual_control_versions' not in st.session_state:
    st.session_state.individual_control_versions = {}

if 'edit_view_mode' not in st.session_state:
    st.session_state.edit_view_mode = "批量预览模式"


# ==================== 2. 全局独立辅助工具 ====================
def mask_rounded_rectangle(img, radius):
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + img.size, radius=radius, fill=255)
    img.putalpha(mask)
    return img

def get_image_main_hue(image_path):
    try:
        ct = ColorThief(image_path)
        r, g, b = ct.get_color(quality=10)
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        return h
    except:
        return 0.0

def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*'
    safe_name = ''.join('_' if char in invalid_chars else char for char in name)
    return safe_name.strip() or "template"

def make_background_config(source, gradient_type="同色清爽渐变", uploaded_file=None):
    return {
        "bg_source": source,
        "bg_type": gradient_type,
        "bg_image_bytes": uploaded_file.getvalue() if uploaded_file is not None else None
    }

def create_background_canvas(bg_config, idx, icon_hue):
    img_width, img_height = 1280, 1706
    source = bg_config.get("bg_source", "纯白背景")
    gradient_type = bg_config.get("bg_type", "同色清爽渐变")
    bg_seed = bg_config.get("bg_seed")
    if bg_seed is not None:
        random.seed(bg_seed)

    if source == "模板4智能库":
        t4_files = [f for f in os.listdir(T4_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if t4_files:
            similar_bgs = []
            for f in t4_files:
                bg_hue = get_image_main_hue(os.path.join(T4_DIR, f))
                if min(abs(bg_hue - icon_hue), 1.0 - abs(bg_hue - icon_hue)) < 0.15:
                    similar_bgs.append(f)
            if similar_bgs and random.random() < 0.7:
                chosen_bg = random.choice(similar_bgs)
            else:
                chosen_bg = random.choice(t4_files)
            with open(os.path.join(T4_DIR, chosen_bg), "rb") as f_img:
                with Image.open(f_img) as bg_img:
                    canvas = bg_img.convert("RGB").copy()
            return canvas, canvas.size[0], canvas.size[1]
        return Image.new("RGB", (img_width, img_height), color=(255, 255, 255)), img_width, img_height

    if source == "上传背景图" and bg_config.get("bg_image_bytes"):
        bg_img = Image.open(io.BytesIO(bg_config["bg_image_bytes"])).convert("RGB")
        canvas = bg_img.resize((img_width, img_height), Image.Resampling.LANCZOS).copy()
        return canvas, img_width, img_height

    if source == "背景文件夹库随机匹配":
        bg_dir = "backgrounds"
        if not os.path.exists(bg_dir):
            os.makedirs(bg_dir)
        bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if bg_files:
            chosen_bg_name = bg_files[(st.session_state.random_seed + idx) % len(bg_files)]
            with open(os.path.join(bg_dir, chosen_bg_name), "rb") as f_img:
                with Image.open(f_img) as bg_img:
                    canvas = bg_img.convert("RGB").resize((img_width, img_height), Image.Resampling.LANCZOS).copy()
            return canvas, img_width, img_height
        return Image.new("RGB", (img_width, img_height), color=(255, 255, 255)), img_width, img_height

    if source == "AI智能渐变生成":
        random_hue_1 = random.random()
        if "同色清爽" in gradient_type:
            opt_s1, opt_l1 = 1.3, 0.88
            opt_s2, opt_l2 = 0.12, 0.98
            rgb_1 = [int(x*255) for x in colorsys.hls_to_rgb(random_hue_1, opt_l1, opt_s1)]
            rgb_2 = [int(x*255) for x in colorsys.hls_to_rgb(random_hue_1, opt_l2, opt_s2)]
        else:
            opt_l, opt_s = 0.97, 0.7
            random_hue_2 = (random_hue_1 + 0.15) % 1.0
            rgb_1 = [int(x*255) for x in colorsys.hls_to_rgb(random_hue_1, opt_l - 0.2, opt_s)]
            rgb_2 = [int(x*255) for x in colorsys.hls_to_rgb(random_hue_2, opt_l - 0.2, opt_s)]

        canvas = Image.new("RGB", (img_width, img_height), color=tuple(rgb_1))
        draw_bg = ImageDraw.Draw(canvas)
        for y in range(img_height):
            blend = y / img_height
            curr_r = max(0, min(255, int(rgb_1[0] * (1 - blend) + rgb_2[0] * blend)))
            curr_g = max(0, min(255, int(rgb_1[1] * (1 - blend) + rgb_2[2] * blend)))
            curr_b = max(0, min(255, int(rgb_1[2] * (1 - blend) + rgb_2[2] * blend)))
            draw_bg.line([(0, y), (img_width, y)], fill=(curr_r, curr_g, curr_b))
        return canvas, img_width, img_height

    return Image.new("RGB", (img_width, img_height), color=(255, 255, 255)), img_width, img_height

def mark_card_independent(idx):
    if idx not in st.session_state.forked_cards:
        st.session_state.forked_cards.add(idx)
        return True
    return False

def reset_individual_controls(idx):
    current_version = st.session_state.individual_control_versions.get(idx, 0)
    st.session_state.individual_control_versions[idx] = current_version + 1

def individual_key(name, idx):
    version = st.session_state.individual_control_versions.get(idx, 0)
    return f"{name}_{idx}_{version}"

MAIN_SUB_COPYWRITING_POOL = {
    "和对象第一次玩到三点": "发现得有点晚，但体验很不错",
    "这才是iPad该玩的游戏": "我就喜欢玩这种不用动脑的游戏…",
    "假期 被窝 我和游戏": "被不少人关注的游戏来啦!",
    "这也太解压了吧": "玩完心情都变掉了",
    "坐高铁必备的解压游戏": "说好只玩5分钟，结果玩了2小时",
    "你敢挑战吗": "据说没人能过第2关",
    "救命这也太好玩了吧": "最新高热度游戏来啦"
}

# ====================================================================
# 🎯 🔴 【模板引擎】（保持原样，不改变任何渲染效果细节）
# ====================================================================

def render_template_1(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors):
    img_width, img_height = canvas.size
    draw = ImageDraw.Draw(canvas)
    icon_target_size = 720 
   
    icon_y_ratio = 0.15      
    main_title_y = 1110      
    line_spacing = 145       
    
    icon_scaled = icon_src.resize((icon_target_size, icon_target_size), Image.Resampling.LANCZOS)
    icon_radius = int(icon_target_size * 0.20) 
    
    mask = Image.new('L', (icon_target_size, icon_target_size), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([(0, 0), (icon_target_size, icon_target_size)], radius=icon_radius, fill=255)
    
    icon_rounded = Image.new("RGBA", (icon_target_size, icon_target_size), (0,0,0,0))
    icon_rounded.paste(icon_scaled, (0, 0), mask)
    
    border_thickness = 20   
    blur_radius = 12        
    shadow_alpha = 20      
    
    inner_mask = Image.new('L', (icon_target_size, icon_target_size), 0)
    inner_draw = ImageDraw.Draw(inner_mask)
    inner_draw.rounded_rectangle(
        [(border_thickness, border_thickness), (icon_target_size - border_thickness, icon_target_size - border_thickness)], 
        radius=max(1, icon_radius - border_thickness), 
        fill=255
    )
    all_edge_mask = ImageChops.subtract(mask, inner_mask)
    
    edge_shadow = Image.new("RGBA", (icon_target_size, icon_target_size), (0, 0, 0, shadow_alpha))
    edge_emboss_layer = Image.new("RGBA", (icon_target_size, icon_target_size), (0, 0, 0, 0))
    edge_emboss_layer.paste(edge_shadow, (0, 0), all_edge_mask)
    edge_emboss_layer = edge_emboss_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    
    edge_emboss_clipped = Image.new("RGBA", (icon_target_size, icon_target_size), (0, 0, 0, 0))
    edge_emboss_clipped.paste(edge_emboss_layer, (0, 0), mask)
    
    icon_final = Image.alpha_composite(icon_rounded, edge_emboss_clipped)
    
    pad = 120  
    layer_w = icon_target_size + pad * 2
    layer_h = icon_target_size + pad * 2
    effect_layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    
    shadow_core = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    sc_draw = ImageDraw.Draw(shadow_core)
    sc_draw.rounded_rectangle([pad, pad + 14, pad + icon_target_size, pad + icon_target_size + 14], radius=icon_radius, fill=(0, 0, 0, 70))
    shadow_core = shadow_core.filter(ImageFilter.GaussianBlur(10))
    
    shadow_soft = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    ss_draw = ImageDraw.Draw(shadow_soft)
    ss_draw.rounded_rectangle([pad + 6, pad + 26, pad + icon_target_size - 6, pad + icon_target_size + 26], radius=icon_radius, fill=(0, 0, 0, 50))
    shadow_soft = shadow_soft.filter(ImageFilter.GaussianBlur(20))
    
    effect_layer = Image.alpha_composite(effect_layer, shadow_soft)
    effect_layer = Image.alpha_composite(effect_layer, shadow_core)
    effect_layer.paste(icon_final, (pad, pad), icon_final)
    
    bubble_size = int(icon_target_size * 0.28) 
    bubble = Image.new("RGBA", (bubble_size, bubble_size), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bubble)
    b_draw.ellipse([(0, 0), (bubble_size, bubble_size)], fill=(234, 61, 47, 255))
    
    rand_num = random.choice([1, 2, 99])
    f_size = int(bubble_size * 0.58) if rand_num != 99 else int(bubble_size * 0.45)
    try: b_font = ImageFont.truetype("arial.ttf", f_size)
    except: b_font = ImageFont.load_default().font_variant(size=f_size)
    b_draw.text((bubble_size/2, bubble_size/2), str(rand_num), font=b_font, fill=(255,255,255,255), anchor="mm")
     
    bx = pad + icon_target_size - int(bubble_size * 0.7)
    by = pad - int(bubble_size * 0.35)
    effect_layer.paste(bubble, (bx, by), bubble)
    
    icon_x = (img_width - icon_target_size) // 2
    icon_y = int(img_height * icon_y_ratio) 
    canvas.paste(effect_layer, (icon_x - pad, icon_y - pad), effect_layer)
    
    main_font_size = int(img_width * 0.098)  
    sub_font_size = int(img_width * 0.062)   
    try:
        font_main_large = font_main.font_variant(size=main_font_size)
        sub_font_large = sub_font.font_variant(size=sub_font_size)
    except:
        font_main_large, sub_font_large = font_main, sub_font

    draw.text((img_width // 2, main_title_y), main_title, fill=colors["main"], font=font_main_large, anchor="mm")
    sub_title_y = main_title_y + line_spacing  
    draw.text((img_width // 2, sub_title_y), sub_title, fill=colors["sub"], font=sub_font_large, anchor="mm")
    return canvas

def render_template_2(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors, custom_tag_text="App Store"):
    img_width, img_height = canvas.size
    draw = ImageDraw.Draw(canvas)
    icon_size = 400          
    icon_y = 240             
    icon_radius_ratio = 0.22 
    tag_y = icon_y + icon_size + 80  
    tag_font_size = 70       
    main_title_y = 1100  
    sub_title_y = 1260       

    icon_scaled = icon_src.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    radius_px = int(icon_size * icon_radius_ratio)
    icon_rounded = mask_rounded_rectangle(icon_scaled, radius_px)
    
    icon_x = (img_width - icon_size) // 2
    canvas.paste(icon_rounded, (icon_x, icon_y), icon_rounded)
    
    try: font_tag = sub_font.font_variant(size=tag_font_size)
    except: font_tag = sub_font
    draw.text((img_width // 2, tag_y), custom_tag_text, fill=colors["tag"], font=font_tag, anchor="mm")
    
    main_size = int(img_width * 0.088)  
    sub_size = int(img_width * 0.088)
    try:
        f_main = font_main.font_variant(size=main_size)
        f_sub = font_main.font_variant(size=sub_size) 
    except:
        f_main, f_sub = font_main, font_main

    draw.text((img_width // 2, main_title_y), main_title, fill=colors["main"], font=f_main, anchor="mm")
    draw.text((img_width // 2, sub_title_y), sub_title, fill=colors["sub"], font=f_sub, anchor="mm")
    return canvas

def render_template_3(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors):
    img_width, img_height = canvas.size
    draw = ImageDraw.Draw(canvas)
    main_font_size = int(img_width * 0.12)  
    sub_font_size = int(img_width * 0.082)   
    try:
        font_main_large = font_main.font_variant(size=main_font_size)
        sub_font_large = sub_font.font_variant(size=sub_font_size)
    except:
        font_main_large, sub_font_large = font_main, sub_font

    main_title_y = 400
    sub_title_y = 560
    draw.text((img_width // 2, main_title_y), main_title, fill=colors["main"], font=font_main_large, anchor="mm")
    draw.text((img_width // 2, sub_title_y), sub_title, fill=colors["sub"], font=sub_font_large, anchor="mm")
    
    icon_target_size = 560
    icon_radius = int(icon_target_size * 0.12)  
    icon_scaled = icon_src.resize((icon_target_size, icon_target_size), Image.Resampling.LANCZOS)
    
    mask = Image.new('L', (icon_target_size, icon_target_size), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([(0, 0), (icon_target_size, icon_target_size)], radius=icon_radius, fill=255)
    
    icon_rounded = Image.new("RGBA", (icon_target_size, icon_target_size), (0,0,0,0))
    icon_rounded.paste(icon_scaled, (0, 0), mask)
    
    border_thickness = 8
    inner_mask = Image.new('L', (icon_target_size, icon_target_size), 0)
    inner_draw = ImageDraw.Draw(inner_mask)
    inner_draw.rounded_rectangle(
        [(border_thickness, border_thickness), (icon_target_size - border_thickness, icon_target_size - border_thickness)], 
        radius=max(1, icon_radius - border_thickness), 
        fill=255
    )
    all_edge_mask = ImageChops.subtract(mask, inner_mask)
    edge_shadow = Image.new("RGBA", (icon_target_size, icon_target_size), (0, 0, 0, 10))
    edge_emboss_layer = Image.new("RGBA", (icon_target_size, icon_target_size), (0, 0, 0, 0))
    edge_emboss_layer.paste(edge_shadow, (0, 0), all_edge_mask)
    edge_emboss_layer = edge_emboss_layer.filter(ImageFilter.GaussianBlur(4))
    
    icon_final = Image.alpha_composite(icon_rounded, edge_emboss_layer)
    pad = 120
    layer_w = icon_target_size + pad * 3
    layer_h = icon_target_size + pad * 3
    effect_layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    
    shadow = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle([pad, pad + 15, pad + icon_target_size, pad + icon_target_size + 15], radius=icon_radius, fill=(0, 0, 0, 45))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12)) 
    
    effect_layer = Image.alpha_composite(effect_layer, shadow)
    effect_layer.paste(icon_final, (pad, pad), icon_final)
    
    icon_x = (img_width - icon_target_size) // 2
    icon_y = 760
    canvas.paste(effect_layer, (icon_x - pad, icon_y - pad), effect_layer)
    return canvas

def render_template_4(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors):
    canvas = canvas.copy()
    img_width, img_height = canvas.size
    draw = ImageDraw.Draw(canvas)
    
    MAIN_FONT_SIZE = int(img_width * 0.09)   
    MAIN_TITLE_Y = 335                    
    
    SUB_FONT_SIZE = int(img_width * 0.07)   
    SUB_TITLE_OFFSET_Y = 76             
     
    np_img = np.array(canvas.convert("RGB"))
    white_mask = (np_img[:, :, 0] > 242) & (np_img[:, :, 1] > 242) & (np_img[:, :, 2] > 242)
    y_indices, x_indices = np.where(white_mask)
  
    if len(y_indices) > 500 and len(x_indices) > 500:
        x_min, x_max = int(np.min(x_indices)), int(np.max(x_indices))
        y_min, y_max = int(np.min(y_indices)), int(np.max(y_indices))
        
        box_w = x_max - x_min + 1
        box_h = y_max - y_min + 1
        aspect_ratio = box_w / box_h if box_h > 0 else 0
        
        if 0.8 <= aspect_ratio <= 1.25 and (img_width * 0.2 < box_w < img_width * 0.7):
            icon_scaled = icon_src.resize((box_w, box_h), Image.Resampling.LANCZOS)
            computed_radius = int(box_w * 0.18)
            icon_final = mask_rounded_rectangle(icon_scaled, computed_radius)
            canvas.paste(icon_final, (x_min, y_min), icon_final)
            
            try: f_main = font_main.font_variant(size=MAIN_FONT_SIZE)
            except: f_main = font_main
            draw.text((img_width // 2, MAIN_TITLE_Y), main_title, fill=colors["main"], font=f_main, anchor="mm")
            
            try: f_sub = sub_font.font_variant(size=SUB_FONT_SIZE)
            except: f_sub = sub_font
            draw.text((x_min + (box_w // 2), y_max + SUB_TITLE_OFFSET_Y), sub_title, fill=colors["sub"], font=f_sub, anchor="mt")
            return canvas

    box_w = int(img_width * 0.45)
    box_h = box_w
    x_min = (img_width - box_w) // 2
    y_min = int(img_height * 0.42)
    
    icon_scaled = icon_src.resize((box_w, box_h), Image.Resampling.LANCZOS)
    icon_final = mask_rounded_rectangle(icon_scaled, int(box_w * 0.18))
    canvas.paste(icon_final, (x_min, y_min), icon_final)
    
    try: f_main = font_main.font_variant(size=MAIN_FONT_SIZE)
    except: f_main = font_main
    draw.text((img_width // 2, MAIN_TITLE_Y), main_title, fill=colors["main"], font=f_main, anchor="mm")
    
    try: f_sub = sub_font.font_variant(size=SUB_FONT_SIZE)
    except: f_sub = sub_font
    draw.text((img_width // 2, y_min + box_h + SUB_TITLE_OFFSET_Y), sub_title, fill=colors["sub"], font=f_sub, anchor="mt")
    
    return canvas

# 📍 [UI名称修改点] 下方字典的 Key 为前端显示的模板选择项名称
TEMPLATE_REGISTRY = {
    "模板1：质感大icon": render_template_1,
    "模板2：经典小icon": render_template_2,
    "模板3：极简吸睛流": render_template_3,
    "模板4：app模拟类": render_template_4
}

@st.cache_data(show_spinner=False, max_entries=128)
def render_card_png_bytes(
    icon_bytes,
    idx,
    card_seed,
    template_choice,
    bold_font_path,
    regular_font_path,
    main_title,
    sub_title,
    tag_text,
    colors_items,
    bg_source,
    bg_type,
    bg_image_bytes,
    bg_seed
):
    random.seed(card_seed)
    icon_src = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")

    try:
        color_thief = ColorThief(io.BytesIO(icon_bytes))
        raw_rgb = color_thief.get_color(quality=1)
        icon_hue, icon_l, icon_s = colorsys.rgb_to_hls(raw_rgb[0]/255.0, raw_rgb[1]/255.0, raw_rgb[2]/255.0)
    except:
        raw_rgb = (230, 45, 45)
        icon_hue = 0.0

    try:
        font_main = ImageFont.truetype(bold_font_path, 72)
        sub_font = ImageFont.truetype(regular_font_path, 44)
    except:
        font_main = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    colors = dict(colors_items)
    bg_config = {
        "bg_source": bg_source,
        "bg_type": bg_type,
        "bg_image_bytes": bg_image_bytes,
        "bg_seed": bg_seed
    }
    canvas, img_width, img_height = create_background_canvas(bg_config, idx, icon_hue)

    render_function = TEMPLATE_REGISTRY[template_choice]
    if template_choice == "模板2：经典UA流":
        canvas = render_template_2(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors, tag_text)
    else:
        canvas = render_function(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors)

    img_buffer = io.BytesIO()
    canvas.save(img_buffer, format="PNG")
    return img_buffer.getvalue()


# ====================================================================
# 🌐 3. 前端 UI 渲染（左侧操作区，右侧预览区格局）
# ====================================================================
# 📍 [UI名称修改点] 系统主标题与子说明
st.markdown("""
    <div class="tool-hero">
        <div class="tool-title">游戏买量图批量生成工作台</div>
        <p class="tool-subtitle">上传 Icon，选择模板与背景，批量生成 1280×1706 高清投放图。</p>
    </div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([4, 6], gap="large")

# ----------------- 左侧：精简纯文字操作面板 -----------------
with col_left:
    # 📍 [UI名称修改点] 步骤一：选择排版模板
    st.header("1. 选择排版模板")
    st.markdown('<div class="step-hint">先决定整体版式，再选择适合游戏气质的视觉风格。</div>', unsafe_allow_html=True)
    template_choice = st.selectbox("排版方案", list(TEMPLATE_REGISTRY.keys()))
    
    TEMPLATE_TEXT_MAP = {
        "模板1：质感大icon": ("和对象第一次玩到凌晨", "这游戏也太解压了吧！"),
        "模板2：经典小icon": ("这款游戏！", "ios终于能玩啦！！"),
        "模板3：极简吸睛流": ("我的无聊救星", "莫名其妙就玩了一整天"),
        "模板4：app模拟1": ("为低精力人设计的游戏", "这里改名字")
    }

    if not st.session_state.lock_copywriting:
        current_mapped_main, current_mapped_sub = TEMPLATE_TEXT_MAP.get(template_choice, ("这款游戏！", "ios终于能玩啦！！"))
        
        if st.session_state.get('last_template','') != template_choice:
            st.session_state.custom_main_title = current_mapped_main
            st.session_state.custom_sub_title = current_mapped_sub
            st.session_state.last_template = template_choice
        
    # 📍 [UI名称修改点] 视觉风格选项
    style_choice = st.selectbox("视觉风格", ["通用高端风", "可爱休闲风", "硬核竞技风"])

    # 📍 [UI名称修改点] 步骤二：上传 Icon
    st.header("2. 上传游戏 Icon")
    st.markdown('<div class="step-hint">支持 PNG、JPG，可一次上传多张，最多处理 9 张。</div>', unsafe_allow_html=True)
    uploaded_icons = st.file_uploader("选择 Icon 图像", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="icon_uploader")
    
    if uploaded_icons and len(uploaded_icons) > 9:
        st.error("最多支持处理 9 张 Icon，超出部分将被自动截断。")
    
    uploaded_icons = uploaded_icons[:9]
    if uploaded_icons:
        st.success(f"已载入 {len(uploaded_icons)} 张 Icon")

    # 📍 [UI名称修改点] 步骤三：背景画布设置
    st.header("3. 背景画布设置")
    st.markdown('<div class="step-hint">为当前模板选择背景来源，锁定后重新生成时会保留背景。</div>', unsafe_allow_html=True)
    st.session_state.lock_background = st.toggle("锁定当前背景", value=st.session_state.lock_background)
    
    uploaded_bg = None
    bg_source = "纯白初始背景"
    bg_type = "同色清爽渐变"
    
    if "模板4" in template_choice:
        st.info("已开启全自动随机智能匹配。")
        bg_source = "模板4智能库"
    else:
        if "模板2" in template_choice:
            # 📍 [UI名称修改点] 模板2背景单选
            bg_source = st.radio("选择背景来源：", ["背景文件夹库随机匹配", "上传背景图"])
        else:
            # 📍 [UI名称修改点] 通用模板背景单选
            bg_source = st.radio("选择背景来源：", ["纯白背景", "AI智能渐变生成", "上传背景图"])

    if bg_source == "AI智能渐变生成":
        bg_type = st.selectbox("选择渐变美学风格：", ["同色清爽渐变", "多色梦幻渐变"])
    elif bg_source == "上传背景图":  # 🛠️ 修复：与单选框定义的字符串保持完全一致
        uploaded_bg = st.file_uploader("上传自定义背景大图：", type=["png", "jpg", "jpeg"], key="bg_uploader")

    global_background_config = make_background_config(bg_source, bg_type, uploaded_bg)

    # 📍 [UI名称修改点] 步骤四：批量文案与颜色设置
    st.header("4. 批量文案与颜色设置")
    st.markdown('<div class="step-hint">这里的文案会同步应用到所有图片，单张细调可在右侧完成。</div>', unsafe_allow_html=True)
    st.session_state.lock_copywriting = st.toggle("锁定当前文字文案", value=st.session_state.lock_copywriting)
    
    global_colors_config = {"tag": "#000000", "main": "#000000", "sub": "#000000"}
    
    if "模板2" in template_choice:
        global_tag_text = st.text_input("批量-下方小字：", value=st.session_state.custom_tag_text)
        st.session_state.custom_tag_text = global_tag_text
        global_main_title = st.text_input("批量-主宣传语（第一排）：", value=st.session_state.custom_main_title)
        st.session_state.custom_main_title = global_main_title
        global_sub_title = st.text_input("批量-副宣传语（第二排）：", value=st.session_state.custom_sub_title)
        st.session_state.custom_sub_title = global_sub_title
        
        # 使用 Expander 包裹实现分层灰底色块
        with st.expander("文字配色管理", expanded=True):
            c1, c2, c3 = st.columns(3)
            global_colors_config["tag"] = c1.color_picker("标签颜色", "#000000")
            global_colors_config["main"] = c2.color_picker("主标颜色", "#000000")
            global_colors_config["sub"] = c3.color_picker("副标颜色", "#000000")
            
    elif "模板4" in template_choice:
        global_main_title = st.text_input("批量-上方宣传文案：", value=st.session_state.custom_main_title)
        st.session_state.custom_main_title = global_main_title
        global_sub_title = st.text_input("批量-下方小字文案：", value=st.session_state.custom_sub_title)
        st.session_state.custom_sub_title = global_sub_title
       
        with st.expander("文字配色管理", expanded=True):
            c1, c2 = st.columns(2)
            global_colors_config["main"] = c1.color_picker("上方大字", "#FFFFFF")
            global_colors_config["sub"] = c2.color_picker("下方小字", "#FFFFFF")
    else:
        global_main_title = st.text_input("批量-主宣传语（第一排）：", value=st.session_state.custom_main_title)
        st.session_state.custom_main_title = global_main_title
        global_sub_title = st.text_input("批量-副宣传语（第二排）：", value=st.session_state.custom_sub_title)
        st.session_state.custom_sub_title = global_sub_title
        
        with st.expander("文字配色管理", expanded=True):
            c1, c2 = st.columns(2)
            global_colors_config["main"] = c1.color_picker("第一排文字", "#000000")
            global_colors_config["sub"] = c2.color_picker("第二排文字", "#000000")


# ====================================================================
# ⚙️ 4. 后端中央核心逻辑与渲染处理（保持逻辑完好不变）
# ====================================================================
generated_canvases = []  

if uploaded_icons:
    font_map = {
        "可爱休闲风": {"bold": "fonts/cute_bold.ttf", "regular": "fonts/cute_regular.ttf"},
        "硬核竞技风": {"bold": "fonts/hardcore_bold.ttf", "regular": "fonts/hardcore_regular.ttf"},
        "通用高端风": {"bold": "fonts/general_bold.ttf", "regular": "fonts/general_regular.ttf"}
    }
    chosen_bold_path = font_map[style_choice]["bold"]
    chosen_regular_path = font_map[style_choice]["regular"]
    if not os.path.exists(chosen_bold_path): chosen_bold_path = chosen_bold_path.replace(".ttf", ".otf")
    if not os.path.exists(chosen_regular_path): chosen_regular_path = chosen_regular_path.replace(".ttf", ".otf")

    for idx, single_icon in enumerate(uploaded_icons):
        default_card_config = {
            "main_title": st.session_state.custom_main_title,
            "sub_title": st.session_state.custom_sub_title,
            "tag_text": st.session_state.custom_tag_text,
            "colors": global_colors_config.copy(),
            "background": global_background_config.copy()
        }
        default_card_config["background"]["bg_seed"] = st.session_state.random_seed + idx

        if idx not in st.session_state.individual_configs:
            st.session_state.individual_configs[idx] = default_card_config
        elif idx not in st.session_state.forked_cards:
            st.session_state.individual_configs[idx] = {
                "main_title": st.session_state.custom_main_title,
                "sub_title": st.session_state.custom_sub_title,
                "tag_text": st.session_state.custom_tag_text,
                "colors": global_colors_config.copy(),
                "background": global_background_config.copy()
            }
            st.session_state.individual_configs[idx]["background"]["bg_seed"] = st.session_state.random_seed + idx
        
        cfg = st.session_state.individual_configs[idx]
        if "background" not in cfg:
            cfg["background"] = global_background_config.copy()
            cfg["background"]["bg_seed"] = st.session_state.random_seed + idx

        icon_bytes = single_icon.getvalue()
        bg_cfg = cfg.get("background", global_background_config.copy())
        card_seed = bg_cfg.get("bg_seed", st.session_state.random_seed + idx)
        rendered_png = render_card_png_bytes(
            icon_bytes,
            idx,
            card_seed,
            template_choice,
            chosen_bold_path,
            chosen_regular_path,
            cfg["main_title"],
            cfg["sub_title"],
            cfg["tag_text"],
            tuple(sorted(cfg["colors"].items())),
            bg_cfg.get("bg_source", "纯白背景"),
            bg_cfg.get("bg_type", "同色清爽渐变"),
            bg_cfg.get("bg_image_bytes"),
            card_seed
        )
        canvas = Image.open(io.BytesIO(rendered_png)).convert("RGB").copy()

        generated_canvases.append((single_icon.name, canvas))


# ==================== 5. 右侧渲染结果展示（2K 弹性工作区） ====================
with col_right:
    # 📍 [UI名称修改点] 工作台主标题
    st.markdown("### 高清预览图")
    
    if uploaded_icons and generated_canvases:
        # 📍 [UI名称修改点] 步骤五主标题
        st.header("生成结果控制")

        zip_buffer = io.BytesIO()
        safe_template_name = sanitize_filename(template_choice)
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, (_, current_canvas) in enumerate(generated_canvases, start=1):
                img_buffer = io.BytesIO()
                current_canvas.save(img_buffer, format="PNG")
                zip_file.writestr(f"{idx:02d}_{safe_template_name}.png", img_buffer.getvalue())

        st.markdown(
            f"""
            <div class="result-toolbar">
                <div class="result-toolbar-title">已生成 {len(generated_canvases)} 张图片</div>
                <div class="result-toolbar-desc">当前模板：{template_choice}。可单张下载，也可一键打包下载全部 PNG。</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        download_col, zip_note_col = st.columns([5, 3])
        with download_col:
            st.download_button(
                label="一键下载全部图片 ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"{safe_template_name}_全部图片.zip",
                mime="application/zip",
                use_container_width=True,
                key="download_all_zip"
            )
        with zip_note_col:
            st.caption("压缩包内命名：01_模板名.png")
          
        # 📍 [UI名称修改点] 单选切换模式的文字名称
        st.session_state.edit_view_mode = st.radio(
            "选择编辑与预览模式：",
            ["批量预览模式", "单张精细微调"],
            horizontal=True
        )
        
        st.markdown("---")

        # 🖼️ 模式 A：批量预览模式
        if st.session_state.edit_view_mode == "批量预览模式":
            grid_cols_count = 3
            total_images = len(generated_canvases)
            
            for i in range(0, total_images, grid_cols_count):
                chunk = generated_canvases[i:i+grid_cols_count]
                columns = st.columns(grid_cols_count)
                for col_idx, (name, current_canvas) in enumerate(chunk):
                    global_idx = i + col_idx
                    
                    with columns[col_idx]:
                        img_buffer = io.BytesIO()
                        current_canvas.save(img_buffer, format="PNG")
                        img_bytes = img_buffer.getvalue()
                      
                        status_label = " (已独立微调)" if global_idx in st.session_state.forked_cards else " (全局同步)"
                        st.image(img_buffer, caption=f"卡片 {global_idx+1}{status_label}", use_container_width=True)
                        
                        # 📍 [UI名称修改点] 批量列表下的单张下载按钮名称
                        dl_col, lock_col = st.columns([5, 1])
                        with dl_col:
                            st.download_button(
                                label=f"下载卡片 {global_idx+1}", 
                                data=img_bytes, 
                                file_name=f"ad_layout_{global_idx+1}.png", 
                                mime="image/png",
                                key=f"dl_grid_btn_{global_idx}",
                                use_container_width=True
                            )
                        with lock_col:
                            lock_label = "🔒" if global_idx in st.session_state.forked_cards else "🔓"
                            if st.button(lock_label, key=f"grid_lock_{global_idx}", help="锁定后不再受左侧批量设置影响", use_container_width=True):
                                if global_idx in st.session_state.forked_cards:
                                    st.session_state.forked_cards.remove(global_idx)
                                    reset_individual_controls(global_idx)
                                else:
                                    st.session_state.forked_cards.add(global_idx)
                                st.rerun()

        # 🖼️ 模式 B：单张精细微调
        else:
            # 📍 [UI名称修改点] 标签分类卡命名格式
            tabs = st.tabs([f"卡片 {i+1}" for i, (name, _) in enumerate(generated_canvases)])

            for idx, tab in enumerate(tabs):
                with tab:
                    filename, current_canvas = generated_canvases[idx]
                    
                    img_buffer = io.BytesIO()
                    current_canvas.save(img_buffer, format="PNG")
                    img_bytes = img_buffer.getvalue()

                    preview_col, edit_col = st.columns([5, 5])
                    
                    with preview_col:
                        st.image(img_buffer, caption=f"实时渲染图 {idx+1}", width=340)
                        
                        # 📍 [UI名称修改点] 独享控制台下的导出按钮
                        st.download_button(
                            label=f"导出当前图片", 
                            data=img_bytes, 
                            file_name=f"ad_layout_individual_{idx+1}.png", 
                            mime="image/png",
                            key=f"dl_btn_{idx}"
                        )

                    with edit_col:
                        # 📍 [UI名称修改点] 单独配置小表单标题
                        st.markdown(f"**进行单独微调 (卡片 {idx+1})**")
                        current_cfg = st.session_state.individual_configs[idx]
                        lock_text = "已锁定，不受左侧批量设置影响" if idx in st.session_state.forked_cards else "未锁定，会跟随左侧批量设置"
                        lock_action = "解锁当前图片" if idx in st.session_state.forked_cards else "锁定当前图片"
                        lock_col_a, lock_col_b = st.columns([3, 2])
                        with lock_col_a:
                            st.caption(lock_text)
                        with lock_col_b:
                            if st.button(lock_action, key=f"individual_lock_{idx}", use_container_width=True):
                                if idx in st.session_state.forked_cards:
                                    st.session_state.forked_cards.remove(idx)
                                    reset_individual_controls(idx)
                                else:
                                    st.session_state.forked_cards.add(idx)
                                st.rerun()
                        
                        if "模板2" in template_choice:
                            # 📍 [UI名称修改点] 单独改动文字框组件名
                            new_tag = st.text_input("独立小字：", value=current_cfg["tag_text"], key=individual_key("individual_tag", idx))
                            if new_tag != current_cfg["tag_text"]:
                                mark_card_independent(idx)
                            st.session_state.individual_configs[idx]["tag_text"] = new_tag
                    
                        new_main = st.text_input("独立主标题：", value=current_cfg["main_title"], key=individual_key("individual_main", idx))
                        new_sub = st.text_input("独立副标题：", value=current_cfg["sub_title"], key=individual_key("individual_sub", idx))
                        
                        if new_main != current_cfg["main_title"] or new_sub != current_cfg["sub_title"]:
                            mark_card_independent(idx)
                        st.session_state.individual_configs[idx]["main_title"] = new_main
                        st.session_state.individual_configs[idx]["sub_title"] = new_sub
                        
                        with st.expander("细节配色方案", expanded=False):
                            if "模板2" in template_choice:
                                c_t = st.color_picker("小字色", value=current_cfg["colors"].get("tag", "#000000"), key=individual_key("cp_t", idx))
                                if c_t != current_cfg["colors"].get("tag", "#000000"):
                                    mark_card_independent(idx)
                                st.session_state.individual_configs[idx]["colors"]["tag"] = c_t
        
                            c_m = st.color_picker("主字色", value=current_cfg["colors"].get("main", "#000000"), key=individual_key("cp_m", idx))
                            c_s = st.color_picker("副字色", value=current_cfg["colors"].get("sub", "#000000"), key=individual_key("cp_s", idx))
              
                            if c_m != current_cfg["colors"].get("main", "#000000") or c_s != current_cfg["colors"].get("sub", "#000000"):
                                mark_card_independent(idx)
                            st.session_state.individual_configs[idx]["colors"]["main"] = c_m
                            st.session_state.individual_configs[idx]["colors"]["sub"] = c_s

                        with st.expander("单张背景设置", expanded=False):
                            current_bg_cfg = current_cfg.get("background", global_background_config.copy())
                            old_bg_source = current_bg_cfg.get("bg_source", "纯白背景")
                            old_bg_type = current_bg_cfg.get("bg_type", "同色清爽渐变")
                            old_bg_image_bytes = current_bg_cfg.get("bg_image_bytes")
                            bg_options = ["纯白背景", "AI智能渐变生成", "上传背景图"]
                            current_bg_source = current_bg_cfg.get("bg_source", "纯白背景")
                            if current_bg_source not in bg_options:
                                current_bg_source = "纯白背景"
                            new_bg_source = st.radio(
                                "独立背景来源：",
                                bg_options,
                                index=bg_options.index(current_bg_source),
                                key=individual_key("individual_bg_source", idx)
                            )
                            new_bg_type = current_bg_cfg.get("bg_type", "同色清爽渐变")
                            if new_bg_source == "AI智能渐变生成":
                                gradient_options = ["同色清爽渐变", "多色梦幻渐变"]
                                if new_bg_type not in gradient_options:
                                    new_bg_type = "同色清爽渐变"
                                new_bg_type = st.selectbox(
                                    "独立渐变美学风格：",
                                    gradient_options,
                                    index=gradient_options.index(new_bg_type),
                                    key=individual_key("individual_bg_type", idx)
                                )
                            new_bg_upload = None
                            if new_bg_source == "上传背景图":
                                new_bg_upload = st.file_uploader(
                                    "上传当前图片专用背景：",
                                    type=["png", "jpg", "jpeg"],
                                    key=individual_key("individual_bg_upload", idx)
                                )
                            bg_image_bytes = current_bg_cfg.get("bg_image_bytes")
                            if new_bg_upload is not None:
                                bg_image_bytes = new_bg_upload.getvalue()
                            st.session_state.individual_configs[idx]["background"] = {
                                "bg_source": new_bg_source,
                                "bg_type": new_bg_type,
                                "bg_image_bytes": bg_image_bytes if new_bg_source == "上传背景图" else None,
                                "bg_seed": current_bg_cfg.get("bg_seed", st.session_state.random_seed + idx)
                            }
                            bg_changed = (
                                new_bg_source != old_bg_source or
                                new_bg_type != old_bg_type or
                                (bg_image_bytes if new_bg_source == "上传背景图" else None) != old_bg_image_bytes
                            )
                            if bg_changed:
                                mark_card_independent(idx)
                                st.rerun()
                          
                        # 📍 [UI名称修改点] 应用独立改动的确认按钮
                        if st.button("保存当前微调", key=f"apply_individual_{idx}"):
                            st.session_state.forked_cards.add(idx)
                            st.rerun()

        # ----------------- 底部中央全剧重置按钮区 -----------------
        st.markdown("---")
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col2:
            def do_change_seed():
                if not st.session_state.lock_background:
                    st.session_state.random_seed = random.randint(0, 99999)
                
                if not st.session_state.lock_copywriting:
                    if "模板4" not in template_choice:
                        default_main = random.choice(list(MAIN_SUB_COPYWRITING_POOL.keys()))
                        st.session_state.custom_main_title = default_main
                        st.session_state.custom_sub_title = MAIN_SUB_COPYWRITING_POOL[default_main]
                
                locked_configs = {
                    card_idx: cfg
                    for card_idx, cfg in st.session_state.individual_configs.items()
                    if card_idx in st.session_state.forked_cards
                }
                st.session_state.individual_configs = locked_configs
                st.session_state.is_shuffled = True
                
            # 📍 [UI名称修改点] 全局一键随机重洗按钮
            st.button("批量随机重新生成", on_click=do_change_seed, use_container_width=True)
            
    else:
        st.info("请在左侧上传您的游戏 Icon 以启动批量排版系统。")
