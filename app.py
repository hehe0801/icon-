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

if 'copywriting_mode' not in st.session_state:
    st.session_state.copywriting_mode = "单组文案应用全部图片"
if 'batch_game_name' not in st.session_state:
    st.session_state.batch_game_name = st.session_state.custom_tag_text
if 'batch_promo_text' not in st.session_state:
    st.session_state.batch_promo_text = f"{st.session_state.custom_main_title}\n{st.session_state.custom_sub_title}"

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

if 'fast_preview_mode' not in st.session_state:
    st.session_state.fast_preview_mode = True
if 'prepare_hd_downloads' not in st.session_state:
    st.session_state.prepare_hd_downloads = False
if 'last_render_signature' not in st.session_state:
    st.session_state.last_render_signature = None
if 'selected_templates' not in st.session_state:
    st.session_state.selected_templates = []
if 'template_copy_configs' not in st.session_state:
    st.session_state.template_copy_configs = {}


# ==================== 2. 全局独立辅助工具 ====================
def mask_rounded_rectangle(img, radius):
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + img.size, radius=radius, fill=255)
    img.putalpha(mask)
    return img

def make_rounded_icon_cover(icon_src, size, radius_ratio=0.155):
    icon_scaled = icon_src.resize((size, size), Image.Resampling.LANCZOS)
    mask_scale = 3
    mask = Image.new('L', (size * mask_scale, size * mask_scale), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        (0, 0, size * mask_scale, size * mask_scale),
        radius=int(size * radius_ratio * mask_scale),
        fill=255
    )
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    icon_final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    icon_final.paste(icon_scaled, (0, 0))
    icon_final.putalpha(mask)
    return icon_final

def get_image_main_hue(image_path):
    try:
        ct = ColorThief(image_path)
        r, g, b = ct.get_color(quality=10)
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        return h
    except:
        return 0.0

@st.cache_data(show_spinner=False, max_entries=256)
def get_cached_image_main_hue(image_path, modified_time):
    return get_image_main_hue(image_path)

@st.cache_data(show_spinner=False, max_entries=128)
def load_background_png_bytes(image_path, modified_time, target_size=None):
    with open(image_path, "rb") as f_img:
        with Image.open(f_img) as bg_img:
            canvas = bg_img.convert("RGB")
            if target_size is not None:
                canvas = canvas.resize(target_size, Image.Resampling.LANCZOS)
            img_buffer = io.BytesIO()
            canvas.save(img_buffer, format="PNG", compress_level=1)
            return img_buffer.getvalue()

def sanitize_filename(name):
    invalid_chars = '<>:"/\\|?*'
    safe_name = ''.join('_' if char in invalid_chars else char for char in name)
    return safe_name.strip() or "template"

TEMPLATE_DEFAULTS = {
    "模板1：质感大icon": {
        "mode": "智能批量宣传语",
        "main_title": "和对象第一次玩到凌晨",
        "sub_title": "这游戏也太解压了吧！",
        "promo_text": "和对象第一次玩到凌晨\n这游戏也太解压了吧！",
        "colors": {"tag": "#000000", "main": "#000000", "sub": "#000000"},
        "auto_color": False
    },
    "模板2：经典小icon": {
        "mode": "单组文案应用该模板全部图片",
        "main_title": "这个游戏！",
        "sub_title": "iOS终于能玩啦！！",
        "promo_text": "这个游戏！\niOS终于能玩啦！！",
        "colors": {"tag": "#000000", "main": "#000000", "sub": "#000000"},
        "auto_color": True
    },
    "模板3：极简吸睛流": {
        "mode": "智能批量宣传语",
        "main_title": "我的无聊救星",
        "sub_title": "莫名其妙就玩了一整天",
        "promo_text": "我的无聊救星\n莫名其妙就玩了一整天",
        "colors": {"tag": "#000000", "main": "#000000", "sub": "#000000"},
        "auto_color": False
    },
    "模板4：app模拟类": {
        "mode": "单组文案应用该模板全部图片",
        "main_title": "为低精力人设计的游戏",
        "sub_title": "",
        "promo_text": "为低精力人设计的游戏",
        "colors": {"tag": "#FFFFFF", "main": "#FFFFFF", "sub": "#FFFFFF"},
        "auto_color": False
    }
}

def ensure_template_copy_config(template_name):
    if template_name not in st.session_state.template_copy_configs:
        default_cfg = TEMPLATE_DEFAULTS.get(template_name, TEMPLATE_DEFAULTS["模板1：质感大icon"])
        st.session_state.template_copy_configs[template_name] = {
            "mode": default_cfg["mode"],
            "main_title": default_cfg["main_title"],
            "sub_title": default_cfg["sub_title"],
            "promo_text": default_cfg["promo_text"],
            "colors": default_cfg["colors"].copy(),
            "auto_color": default_cfg["auto_color"]
        }
    return st.session_state.template_copy_configs[template_name]

def get_template_label(template_name):
    return template_name.split("：")[0]

def get_card_id(template_name, idx):
    return f"{template_name}__{idx}"

def get_template2_auto_colors(raw_rgb):
    r, g, b = raw_rgb
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    main_rgb = colorsys.hls_to_rgb(h, 0.34, min(0.86, max(0.42, s + 0.12)))
    sub_rgb = colorsys.hls_to_rgb((h + 0.04) % 1.0, 0.42, min(0.72, max(0.36, s)))
    tag_rgb = colorsys.hls_to_rgb((h + 0.96) % 1.0, 0.50, min(0.66, max(0.30, s)))
    def to_hex(rgb_tuple):
        return "#{:02X}{:02X}{:02X}".format(*[max(0, min(255, int(v * 255))) for v in rgb_tuple])
    return {
        "main": to_hex(main_rgb),
        "sub": to_hex(sub_rgb),
        "tag": to_hex(tag_rgb)
    }

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
                bg_path = os.path.join(T4_DIR, f)
                bg_hue = get_cached_image_main_hue(bg_path, os.path.getmtime(bg_path))
                if min(abs(bg_hue - icon_hue), 1.0 - abs(bg_hue - icon_hue)) < 0.15:
                    similar_bgs.append(f)
            if similar_bgs and random.random() < 0.7:
                chosen_bg = random.choice(similar_bgs)
            else:
                chosen_bg = random.choice(t4_files)
            bg_path = os.path.join(T4_DIR, chosen_bg)
            bg_bytes = load_background_png_bytes(bg_path, os.path.getmtime(bg_path))
            canvas = Image.open(io.BytesIO(bg_bytes)).convert("RGB").copy()
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
            bg_path = os.path.join(bg_dir, chosen_bg_name)
            bg_bytes = load_background_png_bytes(bg_path, os.path.getmtime(bg_path), (img_width, img_height))
            canvas = Image.open(io.BytesIO(bg_bytes)).convert("RGB").copy()
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
    st.session_state.prepare_hd_downloads = False
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

def get_template_promo_line_count(template_choice):
    if "模板4" in template_choice:
        return 1
    return 2

def parse_promo_groups(promo_text, line_count):
    lines = [line.strip() for line in promo_text.splitlines() if line.strip()]
    if not lines:
        return []

    groups = []
    for start in range(0, len(lines), line_count):
        chunk = lines[start:start + line_count]
        if line_count == 1:
            groups.append((chunk[0], ""))
        else:
            first_line = chunk[0]
            second_line = chunk[1] if len(chunk) > 1 else ""
            groups.append((first_line, second_line))
    return groups

def get_copywriting_for_card(idx, template_choice, mode, game_name, single_main, single_sub, promo_groups):
    if mode == "智能批量宣传语" and promo_groups:
        group_idx = min(idx, len(promo_groups) - 1)
        promo_line_1, promo_line_2 = promo_groups[group_idx]
    else:
        promo_line_1, promo_line_2 = single_main, single_sub

    if "模板2" in template_choice:
        return {
            "main_title": promo_line_1,
            "sub_title": promo_line_2,
            "tag_text": game_name
        }

    if "模板4" in template_choice:
        return {
            "main_title": promo_line_1,
            "sub_title": game_name,
            "tag_text": game_name
        }

    return {
        "main_title": promo_line_1,
        "sub_title": promo_line_2,
        "tag_text": game_name
    }

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
     
    detect_scale = 0.25
    detect_size = (max(1, int(img_width * detect_scale)), max(1, int(img_height * detect_scale)))
    detect_canvas = canvas.convert("RGB").resize(detect_size, Image.Resampling.BILINEAR)
    np_img = np.array(detect_canvas)
    white_mask = (np_img[:, :, 0] > 242) & (np_img[:, :, 1] > 242) & (np_img[:, :, 2] > 242)
    y_indices, x_indices = np.where(white_mask)
  
    if len(y_indices) > 50 and len(x_indices) > 50:
        x_min = max(0, int(np.min(x_indices) / detect_scale))
        x_max = min(img_width - 1, int(np.max(x_indices) / detect_scale))
        y_min = max(0, int(np.min(y_indices) / detect_scale))
        y_max = min(img_height - 1, int(np.max(y_indices) / detect_scale))
        
        box_w = x_max - x_min + 1
        box_h = y_max - y_min + 1
        aspect_ratio = box_w / box_h if box_h > 0 else 0
        
        if 0.8 <= aspect_ratio <= 1.25 and (img_width * 0.2 < box_w < img_width * 0.7):
            cover_pad = max(6, int(box_w * 0.025))
            cover_size = max(box_w, box_h) + cover_pad * 2
            icon_final = make_rounded_icon_cover(icon_src, cover_size)
            canvas.paste(icon_final, (x_min - cover_pad, y_min - cover_pad), icon_final)
            
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
    
    cover_pad = max(6, int(box_w * 0.025))
    cover_size = box_w + cover_pad * 2
    icon_final = make_rounded_icon_cover(icon_src, cover_size)
    canvas.paste(icon_final, (x_min - cover_pad, y_min - cover_pad), icon_final)
    
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
    output_width,
    template_choice,
    bold_font_path,
    regular_font_path,
    main_title,
    sub_title,
    tag_text,
    colors_items,
    auto_template2_color,
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

    colors = get_template2_auto_colors(raw_rgb) if auto_template2_color and "模板2" in template_choice else dict(colors_items)
    bg_config = {
        "bg_source": bg_source,
        "bg_type": bg_type,
        "bg_image_bytes": bg_image_bytes,
        "bg_seed": bg_seed
    }
    canvas, img_width, img_height = create_background_canvas(bg_config, idx, icon_hue)

    render_function = TEMPLATE_REGISTRY[template_choice]
    if "模板2" in template_choice:
        canvas = render_template_2(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors, tag_text)
    else:
        canvas = render_function(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors)

    if output_width and output_width < canvas.size[0]:
        output_height = int(canvas.size[1] * output_width / canvas.size[0])
        canvas = canvas.resize((output_width, output_height), Image.Resampling.LANCZOS)

    img_buffer = io.BytesIO()
    compress_level = 1 if output_width and output_width < 1280 else 6
    canvas.save(img_buffer, format="PNG", compress_level=compress_level)
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
    selected_templates = st.multiselect(
        "排版方案（最多选择 4 个）：",
        list(TEMPLATE_REGISTRY.keys()),
        default=st.session_state.selected_templates or ["模板1：质感大icon"]
    )
    if len(selected_templates) > 4:
        st.warning("最多同时选择 4 个模板，已自动保留前 4 个。")
        selected_templates = selected_templates[:4]
    if not selected_templates:
        selected_templates = ["模板1：质感大icon"]
        st.warning("请至少选择 1 个模板，已默认使用模板1。")
    st.session_state.selected_templates = selected_templates
    template_choice = selected_templates[0]
        
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

    st.session_state.fast_preview_mode = st.toggle(
        "快速预览模式",
        value=st.session_state.fast_preview_mode,
        help="开启后预览图使用较低画质，页面响应更快；导出前再准备高清图。"
    )

    # 📍 [UI名称修改点] 步骤三：背景画布设置
    st.header("3. 背景画布设置")
    st.markdown('<div class="step-hint">模板2使用背景图库随机匹配，模板4使用智能图库背景，模板1/3使用下面的批量背景设置。</div>', unsafe_allow_html=True)
    st.session_state.lock_background = st.toggle("锁定当前背景", value=st.session_state.lock_background)
    
    uploaded_bg = None
    bg_source = "纯白背景"
    bg_type = "同色清爽渐变"

    fixed_bg_templates = []
    if any("模板2" in t for t in selected_templates):
        fixed_bg_templates.append("模板2：背景图库随机匹配")
    if any("模板4" in t for t in selected_templates):
        fixed_bg_templates.append("模板4：智能图库匹配")
    if fixed_bg_templates:
        st.info("；".join(fixed_bg_templates))
    bg_source = st.radio("模板1/3背景来源：", ["纯白背景", "AI智能渐变生成", "上传背景图"])

    if bg_source == "AI智能渐变生成":
        bg_type = st.selectbox("选择渐变美学风格：", ["同色清爽渐变", "多色梦幻渐变"])
    elif bg_source == "上传背景图":  # 🛠️ 修复：与单选框定义的字符串保持完全一致
        uploaded_bg = st.file_uploader("上传自定义背景大图：", type=["png", "jpg", "jpeg"], key="bg_uploader")

    global_background_config = make_background_config(bg_source, bg_type, uploaded_bg)

    # 📍 [UI名称修改点] 步骤四：批量文案与颜色设置
    st.header("4. 批量文案与颜色设置")
    st.markdown('<div class="step-hint">游戏名全局共用；每个模板有自己的批量文案和颜色设置。</div>', unsafe_allow_html=True)
    st.session_state.lock_copywriting = st.toggle("锁定当前文字文案", value=st.session_state.lock_copywriting)
    
    global_game_name = st.text_input("游戏名：", value=st.session_state.batch_game_name)
    st.session_state.batch_game_name = global_game_name
    st.session_state.custom_tag_text = global_game_name

    template_copy_runtime = {}
    copywriting_modes = ["单组文案应用该模板全部图片", "智能批量宣传语"]
    copy_tabs = st.tabs([get_template_label(t) for t in selected_templates])
    for tab, template_name in zip(copy_tabs, selected_templates):
        with tab:
            template_cfg = ensure_template_copy_config(template_name)
            line_count = get_template_promo_line_count(template_name)
            st.markdown(f"**{template_name}**")
            template_cfg["mode"] = st.radio(
                "文案应用方式：",
                copywriting_modes,
                index=copywriting_modes.index(template_cfg["mode"]) if template_cfg["mode"] in copywriting_modes else 0,
                horizontal=True,
                key=f"copy_mode_{template_name}"
            )

            if template_cfg["mode"] == "智能批量宣传语":
                hint = "当前模板按每张 1 行宣传语解析。" if line_count == 1 else "当前模板按每张 2 行宣传语解析。"
                st.caption(hint)
                template_cfg["promo_text"] = st.text_area(
                    "批量宣传语：",
                    value=template_cfg["promo_text"],
                    height=160,
                    key=f"promo_text_{template_name}"
                )
                promo_groups = parse_promo_groups(template_cfg["promo_text"], line_count)
                if uploaded_icons:
                    st.caption(f"已解析 {len(promo_groups)} 组，将按上传顺序匹配 {len(uploaded_icons)} 张 Icon。")
            else:
                if "模板4" in template_name:
                    template_cfg["main_title"] = st.text_input("上方宣传语：", value=template_cfg["main_title"], key=f"main_title_{template_name}")
                    template_cfg["sub_title"] = global_game_name
                else:
                    template_cfg["main_title"] = st.text_input("宣传语第一行：", value=template_cfg["main_title"], key=f"main_title_{template_name}")
                    template_cfg["sub_title"] = st.text_input("宣传语第二行：", value=template_cfg["sub_title"], key=f"sub_title_{template_name}")
                promo_groups = []

            if "模板2" in template_name:
                template_cfg["auto_color"] = st.checkbox("自动适配邻近文字色", value=template_cfg.get("auto_color", True), key=f"auto_color_{template_name}")
                with st.expander("文字配色管理", expanded=not template_cfg["auto_color"]):
                    c1, c2, c3 = st.columns(3)
                    template_cfg["colors"]["tag"] = c1.color_picker("游戏名颜色", template_cfg["colors"].get("tag", "#000000"), key=f"color_tag_{template_name}")
                    template_cfg["colors"]["main"] = c2.color_picker("宣传语第一行", template_cfg["colors"].get("main", "#000000"), key=f"color_main_{template_name}")
                    template_cfg["colors"]["sub"] = c3.color_picker("宣传语第二行", template_cfg["colors"].get("sub", "#000000"), key=f"color_sub_{template_name}")
            elif "模板4" in template_name:
                with st.expander("文字配色管理", expanded=True):
                    c1, c2 = st.columns(2)
                    template_cfg["colors"]["main"] = c1.color_picker("上方宣传语", template_cfg["colors"].get("main", "#FFFFFF"), key=f"color_main_{template_name}")
                    template_cfg["colors"]["sub"] = c2.color_picker("游戏名", template_cfg["colors"].get("sub", "#FFFFFF"), key=f"color_sub_{template_name}")
                    template_cfg["colors"]["tag"] = template_cfg["colors"]["sub"]
            else:
                with st.expander("文字配色管理", expanded=True):
                    c1, c2 = st.columns(2)
                    template_cfg["colors"]["main"] = c1.color_picker("宣传语第一行", template_cfg["colors"].get("main", "#000000"), key=f"color_main_{template_name}")
                    template_cfg["colors"]["sub"] = c2.color_picker("宣传语第二行", template_cfg["colors"].get("sub", "#000000"), key=f"color_sub_{template_name}")
                    template_cfg["colors"]["tag"] = "#000000"

            template_copy_runtime[template_name] = {
                "config": template_cfg,
                "promo_groups": promo_groups
            }

current_render_signature = (
    tuple(selected_templates),
    style_choice,
    st.session_state.fast_preview_mode,
    st.session_state.batch_game_name,
    tuple(
        (
            template_name,
            cfg["mode"],
            cfg["main_title"],
            cfg["sub_title"],
            cfg["promo_text"],
            cfg.get("auto_color", False),
            tuple(sorted(cfg["colors"].items()))
        )
        for template_name, cfg in sorted(st.session_state.template_copy_configs.items())
        if template_name in selected_templates
    ),
    global_background_config.get("bg_source"),
    global_background_config.get("bg_type"),
    len(global_background_config.get("bg_image_bytes") or b""),
    tuple((file.name, getattr(file, "size", 0)) for file in uploaded_icons)
)
if st.session_state.last_render_signature is not None and current_render_signature != st.session_state.last_render_signature:
    st.session_state.prepare_hd_downloads = False
st.session_state.last_render_signature = current_render_signature


# ====================================================================
# ⚙️ 4. 后端中央核心逻辑与渲染处理（保持逻辑完好不变）
# ====================================================================
generated_canvases = []  
generated_by_template = {}
hd_image_bytes_map = {}

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

    for template_name in selected_templates:
        generated_by_template[template_name] = []
        template_runtime = template_copy_runtime[template_name]
        copy_cfg = template_runtime["config"]
        promo_groups = template_runtime["promo_groups"]

        for idx, single_icon in enumerate(uploaded_icons):
            card_id = get_card_id(template_name, idx)
            card_copy = get_copywriting_for_card(
                idx,
                template_name,
                copy_cfg["mode"],
                st.session_state.batch_game_name,
                copy_cfg["main_title"],
                copy_cfg["sub_title"],
                promo_groups
            )

            if "模板4" in template_name:
                template_bg_config = make_background_config("模板4智能库")
            elif "模板2" in template_name:
                template_bg_config = make_background_config("背景文件夹库随机匹配")
            else:
                template_bg_config = global_background_config.copy()
            default_card_config = {
                "main_title": card_copy["main_title"],
                "sub_title": card_copy["sub_title"],
                "tag_text": card_copy["tag_text"],
                "colors": copy_cfg["colors"].copy(),
                "auto_color": copy_cfg.get("auto_color", False),
                "background": template_bg_config
            }
            default_card_config["background"]["bg_seed"] = st.session_state.random_seed + idx

            if card_id not in st.session_state.individual_configs:
                st.session_state.individual_configs[card_id] = default_card_config
            elif card_id not in st.session_state.forked_cards:
                st.session_state.individual_configs[card_id] = default_card_config
                st.session_state.individual_configs[card_id]["background"]["bg_seed"] = st.session_state.random_seed + idx
            
            cfg = st.session_state.individual_configs[card_id]
            if "background" not in cfg:
                cfg["background"] = template_bg_config
                cfg["background"]["bg_seed"] = st.session_state.random_seed + idx
            elif card_id not in st.session_state.forked_cards and "模板2" in template_name:
                cfg["background"] = template_bg_config
                cfg["background"]["bg_seed"] = st.session_state.random_seed + idx
            if "auto_color" not in cfg:
                cfg["auto_color"] = copy_cfg.get("auto_color", False)

            icon_bytes = single_icon.getvalue()
            bg_cfg = cfg.get("background", template_bg_config)
            card_seed = bg_cfg.get("bg_seed", st.session_state.random_seed + idx)
            render_args = (
                icon_bytes,
                idx,
                card_seed,
                template_name,
                chosen_bold_path,
                chosen_regular_path,
                cfg["main_title"],
                cfg["sub_title"],
                cfg["tag_text"],
                tuple(sorted(cfg["colors"].items())),
                cfg.get("auto_color", False),
                bg_cfg.get("bg_source", "纯白背景"),
                bg_cfg.get("bg_type", "同色清爽渐变"),
                bg_cfg.get("bg_image_bytes"),
                card_seed
            )
            preview_width = 520 if st.session_state.fast_preview_mode else 1280
            rendered_png = render_card_png_bytes(
                icon_bytes,
                idx,
                card_seed,
                preview_width,
                template_name,
                chosen_bold_path,
                chosen_regular_path,
                cfg["main_title"],
                cfg["sub_title"],
                cfg["tag_text"],
                tuple(sorted(cfg["colors"].items())),
                cfg.get("auto_color", False),
                bg_cfg.get("bg_source", "纯白背景"),
                bg_cfg.get("bg_type", "同色清爽渐变"),
                bg_cfg.get("bg_image_bytes"),
                card_seed
            )
            canvas = Image.open(io.BytesIO(rendered_png)).convert("RGB").copy()

            item = {
                "template": template_name,
                "icon_idx": idx,
                "card_id": card_id,
                "name": single_icon.name,
                "canvas": canvas,
                "render_args": render_args
            }
            generated_canvases.append(item)
            generated_by_template[template_name].append(item)

            if st.session_state.prepare_hd_downloads:
                hd_png = render_card_png_bytes(*render_args[:3], 1280, *render_args[3:])
                hd_image_bytes_map[card_id] = hd_png


# ==================== 5. 右侧渲染结果展示（2K 弹性工作区） ====================
with col_right:
    st.markdown("### 效果预览图")
    
    if uploaded_icons and generated_canvases:
        st.header("生成结果控制")

        st.markdown(
            f"""
            <div class="result-toolbar">
                <div class="result-toolbar-title">已生成 {len(generated_canvases)} 张图片</div>
                <div class="result-toolbar-desc">已选择 {len(selected_templates)} 个模板。默认显示快速预览，需要导出时再准备高清下载文件。</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        control_col1, control_col2, control_col3 = st.columns([3, 3, 3])
        with control_col1:
            preview_status = "快速预览中" if st.session_state.fast_preview_mode else "高清预览中"
            st.caption(preview_status)
        with control_col2:
            if st.button("准备高清下载", use_container_width=True):
                st.session_state.prepare_hd_downloads = True
                st.rerun()
        with control_col3:
            if st.session_state.prepare_hd_downloads:
                if st.button("回到快速预览", use_container_width=True):
                    st.session_state.prepare_hd_downloads = False
                    st.rerun()
            else:
                st.caption("高清下载未准备")

        if st.session_state.prepare_hd_downloads and hd_image_bytes_map:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for template_name in selected_templates:
                    safe_template_name = sanitize_filename(template_name)
                    for item in generated_by_template.get(template_name, []):
                        card_id = item["card_id"]
                        if card_id in hd_image_bytes_map:
                            file_name = f"{safe_template_name}/{item['icon_idx'] + 1:02d}_{safe_template_name}.png"
                            zip_file.writestr(file_name, hd_image_bytes_map[card_id])

            st.download_button(
                label="一键下载全部图片 ZIP",
                data=zip_buffer.getvalue(),
                file_name="全部模板_全部图片.zip",
                mime="application/zip",
                use_container_width=True,
                key="download_all_zip"
            )
            st.caption("压缩包会按模板分文件夹。")
        else:
            st.info("当前为快速预览。需要导出原尺寸图片时，请先点击“准备高清下载”。")
        
        st.markdown("---")

        grid_cols_count = 4
        for template_name in selected_templates:
            template_items = generated_by_template.get(template_name, [])
            if not template_items:
                continue
            st.markdown(f"#### {template_name}")
            st.caption(f"{len(template_items)} 张预览")

            for i in range(0, len(template_items), grid_cols_count):
                chunk = template_items[i:i+grid_cols_count]
                columns = st.columns(grid_cols_count)
                for col_idx, item in enumerate(chunk):
                    with columns[col_idx]:
                        current_canvas = item["canvas"]
                        card_id = item["card_id"]
                        icon_idx = item["icon_idx"]
                        img_buffer = io.BytesIO()
                        current_canvas.save(img_buffer, format="PNG", compress_level=1)
                        img_bytes = img_buffer.getvalue()

                        status_label = "已锁定" if card_id in st.session_state.forked_cards else "全局同步"
                        st.image(img_buffer, caption=f"卡片 {icon_idx+1} · {status_label}", use_container_width=True)

                        dl_col, lock_col = st.columns([5, 1])
                        with dl_col:
                            download_ready = st.session_state.prepare_hd_downloads and card_id in hd_image_bytes_map
                            safe_template_name = sanitize_filename(template_name)
                            st.download_button(
                                label=f"下载卡片 {icon_idx+1}" if download_ready else "先准备高清",
                                data=hd_image_bytes_map[card_id] if download_ready else b"",
                                file_name=f"{icon_idx + 1:02d}_{safe_template_name}.png",
                                mime="image/png",
                                key=f"dl_grid_btn_{card_id}",
                                use_container_width=True,
                                disabled=not download_ready
                            )
                        with lock_col:
                            lock_label = "🔒" if card_id in st.session_state.forked_cards else "🔓"
                            if st.button(lock_label, key=f"grid_lock_{card_id}", help="锁定后不再受左侧批量设置影响", use_container_width=True):
                                st.session_state.prepare_hd_downloads = False
                                if card_id in st.session_state.forked_cards:
                                    st.session_state.forked_cards.remove(card_id)
                                    reset_individual_controls(card_id)
                                else:
                                    st.session_state.forked_cards.add(card_id)
                                st.rerun()

        # ----------------- 底部中央全剧重置按钮区 -----------------
        st.markdown("---")
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col2:
            def do_change_seed():
                st.session_state.prepare_hd_downloads = False
                if not st.session_state.lock_background:
                    st.session_state.random_seed = random.randint(0, 99999)
                
                if not st.session_state.lock_copywriting:
                    for template_name, cfg in st.session_state.template_copy_configs.items():
                        if template_name in selected_templates and cfg.get("mode") == "智能批量宣传语" and "模板4" not in template_name:
                            default_main = random.choice(list(MAIN_SUB_COPYWRITING_POOL.keys()))
                            cfg["main_title"] = default_main
                            cfg["sub_title"] = MAIN_SUB_COPYWRITING_POOL[default_main]
                
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
