import os
import zipfile
from collections import deque

# 检查如果只有压缩包，没有解压后的字体，就自动在云端解压它
if os.path.exists("fonts/general_bold.zip") and not os.path.exists("fonts/general_bold.ttf"):
    with zipfile.ZipFile("fonts/general_bold.zip", 'r') as zip_ref:
        zip_ref.extractall("fonts/")
import streamlit as st
import random
import os
import colorsys
import io
import base64
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance, ImageOps
from colorthief import ColorThief
from streamlit_sortables import sort_items

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
        .uploadedFile,
        .stFileUploaderFile,
        [data-testid="stFileUploaderFile"],
        [data-testid="stFileUploaderFileName"],
        [data-testid="stFileUploaderDeleteBtn"],
        [data-testid="stFileUploaderFileCard"],
        [data-testid="stFileUploaderFileCard"] *,
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] [data-testid="stFileUploaderFile"],
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] ~ div,
        [data-testid="stFileUploader"] ul,
        [data-testid="stFileUploader"] li,
        [data-testid="stFileUploader"] small,
        [data-testid="stFileUploaderPagination"] {
            display: none !important;
        }
        div[data-testid="stFileUploader"] > div:not([data-testid="stFileUploaderDropzone"]),
        div[data-testid="stFileUploader"] > div:not([data-testid="stFileUploaderDropzone"]) *,
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] ~ *,
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] ~ * * {
            display: none !important;
        }
        [data-testid="stFileUploader"] [data-testid*="stFileUploaderFile"] ,
        [data-testid="stFileUploader"] [data-testid*="stFileUploaderFile"] * ,
        [data-testid="stFileUploader"] [data-testid*="FileCard"] ,
        [data-testid="stFileUploader"] [data-testid*="FileCard"] * ,
        [data-testid="stFileUploader"] [data-testid*="FileName"] ,
        [data-testid="stFileUploader"] [data-testid*="FileName"] * {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# 自动创建模板4所需的图库文件夹
T4_DIR = "template4_cards"
if not os.path.exists(T4_DIR):
    os.makedirs(T4_DIR)

DECORATION_DIR = os.path.join("decorations", "twemoji")

TEMPLATE1_COMMON_DECORATION_NAMES = {
    "sparkles", "star", "glowing_star", "fire", "rocket", "crown", "gem",
    "trophy", "gift", "lightning", "collision", "two_hearts",
    "sparkling_heart", "bullseye"
}

TEMPLATE1_DECORATION_KEYWORDS = {
    "battle": ["战斗", "打怪", "冒险", "挑战", "闯关", "爆", "火", "热血", "武器", "对决", "攻击"],
    "cute": ["可爱", "萌", "爱心", "甜", "恋爱", "猫", "狗", "治愈"],
    "puzzle": ["解谜", "拼图", "动脑", "脑洞", "策略", "益智", "关卡", "烧脑"],
    "reward": ["奖励", "金币", "宝石", "奖杯", "礼物", "福利", "抽奖", "宝藏"],
    "magic": ["魔法", "奇幻", "神秘", "梦幻", "彩虹", "许愿", "精灵"],
    "nature": ["自然", "花园", "种田", "田园", "森林", "植物", "低精力", "放松"],
    "royal": ["皇冠", "城堡", "王国", "公主", "国王", "贵族"],
    "speed": ["快", "速度", "赛车", "冲刺", "飞行", "火箭", "加速"],
    "music": ["音乐", "节奏", "唱歌", "歌曲", "麦克风", "乐器"],
    "time": ["时间", "等待", "时钟", "倒计时", "分钟", "小时", "休闲"]
}


@st.cache_data(show_spinner=False)
def load_decoration_asset_paths():
    paths = []
    if os.path.exists(DECORATION_DIR):
        for root, _, files in os.walk(DECORATION_DIR):
            for file_name in files:
                if file_name.lower().endswith(".png") and file_name.lower() != "twemoji_preview.png":
                    paths.append(os.path.join(root, file_name))
    return sorted(paths)


@st.cache_data(show_spinner=False, max_entries=128)
def load_decoration_asset(path):
    return Image.open(path).convert("RGBA")


def get_decoration_name(path):
    name = os.path.splitext(os.path.basename(path))[0]
    category = os.path.basename(os.path.dirname(path))
    prefix = category + "_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    return name


def choose_template1_decoration(raw_rgb, text=""):
    paths = load_decoration_asset_paths()
    if not paths:
        return None

    common_paths = [path for path in paths if get_decoration_name(path) in TEMPLATE1_COMMON_DECORATION_NAMES]
    matched_paths = []
    for category, keywords in TEMPLATE1_DECORATION_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched_paths.extend([path for path in paths if os.path.basename(os.path.dirname(path)) == category])

    if matched_paths:
        weighted_paths = matched_paths * 7 + common_paths * 3 + paths
    elif common_paths:
        weighted_paths = common_paths * 8 + paths
    else:
        weighted_paths = paths

    stable_key = int(raw_rgb[0]) * 3 + int(raw_rgb[1]) * 5 + int(raw_rgb[2]) * 7
    stable_key += sum((index + 1) * ord(char) for index, char in enumerate(text))
    rng = random.Random(stable_key)
    return rng.choice(weighted_paths)


def paste_template1_decoration(canvas, draw, text, font, center_x, center_y, raw_rgb, decoration_hint_text=""):
    decoration_path = choose_template1_decoration(raw_rgb, decoration_hint_text or text)
    if not decoration_path or not text:
        return

    bbox = draw.textbbox((center_x, center_y), text, font=font, anchor="mm")
    text_left, text_top, text_right, text_bottom = bbox
    text_h = max(1, text_bottom - text_top)
    icon_size = int(text_h * 0.92)
    gap = max(18, int(icon_size * 0.38))
    side_pad = 18
    max_left_x = text_left - gap - icon_size
    min_right_x = text_right + gap + icon_size
    if max_left_x < side_pad or min_right_x > canvas.size[0] - side_pad:
        icon_size = max(26, min(icon_size, int((canvas.size[0] - (text_right - text_left) - side_pad * 2 - gap * 2) / 2)))
        gap = max(12, int(icon_size * 0.32))

    if icon_size < 24:
        return

    icon = load_decoration_asset(decoration_path).resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    y = int(center_y - icon_size / 2)
    left_x = int(text_left - gap - icon_size)
    right_x = int(text_right + gap)
    canvas.paste(icon, (left_x, y), icon)
    canvas.paste(icon, (right_x, y), icon)


def fit_cover(image, size):
    target_w, target_h = size
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((int(src_w * scale), int(src_h * scale)), Image.Resampling.LANCZOS)
    left = max(0, (resized.size[0] - target_w) // 2)
    top = max(0, (resized.size[1] - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def weaken_template5_background(image, size, allow_upscale):
    target_w, target_h = size
    image = image.convert("RGB")
    if allow_upscale:
        prepared = fit_cover(image, (target_w, target_h))
    else:
        prepared = fit_cover(image, (target_w, target_h))

    avg_rgb = tuple(int(v) for v in np.array(prepared).reshape(-1, 3).mean(axis=0))
    h, _, s = colorsys.rgb_to_hls(avg_rgb[0] / 255.0, avg_rgb[1] / 255.0, avg_rgb[2] / 255.0)
    tint_rgb = tuple(int(v * 255) for v in colorsys.hls_to_rgb(h, 0.66, max(0.24, min(0.48, s + 0.12))))

    prepared = ImageEnhance.Color(prepared).enhance(0.62)
    prepared = ImageEnhance.Contrast(prepared).enhance(0.82)
    prepared = ImageEnhance.Brightness(prepared).enhance(1.03)
    prepared = prepared.filter(ImageFilter.GaussianBlur(9))
    tint_layer = Image.new("RGB", (target_w, target_h), tint_rgb)
    prepared = Image.blend(prepared, tint_layer, 0.22)
    mist = Image.new("RGB", (target_w, target_h), (255, 255, 255))
    return Image.blend(prepared, mist, 0.08)


def fit_font_to_width(font, text, start_size, max_width, min_size=48, stroke_width=0):
    for font_size in range(start_size, min_size - 1, -4):
        try:
            candidate = font.font_variant(size=font_size)
        except:
            candidate = font
        bbox = ImageDraw.Draw(Image.new("RGB", (10, 10))).textbbox((0, 0), text, font=candidate, stroke_width=stroke_width)
        if bbox[2] - bbox[0] <= max_width:
            return candidate
    return candidate


def make_stroke_text_layer(text, font, fill, stroke_fill, stroke_width):
    scratch = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    scratch_draw = ImageDraw.Draw(scratch)
    bbox = scratch_draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    layer_w = max(1, bbox[2] - bbox[0])
    layer_h = max(1, bbox[3] - bbox[1])
    layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.text(
        (-bbox[0], -bbox[1]),
        text,
        fill=fill,
        font=font,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill
    )
    alpha_bbox = layer.getchannel("A").getbbox()
    if alpha_bbox:
        layer = layer.crop(alpha_bbox)
    return layer


def paste_centered_stroke_text(canvas, center_xy, text, font, fill, stroke_fill, stroke_width):
    center_x, center_y = center_xy
    layer = make_stroke_text_layer(text, font, fill, stroke_fill, stroke_width)
    x = int(round(center_x - layer.size[0] / 2))
    y = int(round(center_y - layer.size[1] / 2))
    canvas.paste(layer, (x, y), layer)
    return (x, y, x + layer.size[0], y + layer.size[1])


def paste_shadowed_stroke_text(canvas, center_xy, text, font, fill, stroke_fill, stroke_width, shadow_offset=(0, 12), shadow_blur=12, shadow_alpha=70):
    center_x, center_y = center_xy
    layer = make_stroke_text_layer(text, font, fill, stroke_fill, stroke_width)
    alpha = layer.getchannel("A")
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow_alpha_mask = alpha.point(lambda a: int(a * shadow_alpha / 255))
    shadow.putalpha(shadow_alpha_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
    shadow_x = int(round(center_x - layer.size[0] / 2 + shadow_offset[0]))
    shadow_y = int(round(center_y - layer.size[1] / 2 + shadow_offset[1]))
    layer_x = int(round(center_x - layer.size[0] / 2))
    layer_y = int(round(center_y - layer.size[1] / 2))
    canvas.paste(shadow, (shadow_x, shadow_y), shadow)
    canvas.paste(layer, (layer_x, layer_y), layer)
    return (layer_x, layer_y, layer_x + layer.size[0], layer_y + layer.size[1])


def transform_italic_layer(layer, shear_x=-0.18):
    if layer.size[0] <= 1 or layer.size[1] <= 1:
        return layer
    shear_pad = int(abs(shear_x) * layer.size[1]) + 8
    new_width = layer.size[0] + shear_pad
    if shear_x < 0:
        matrix = (1, shear_x, shear_pad, 0, 1, 0)
    else:
        matrix = (1, shear_x, 0, 0, 1, 0)
    return layer.transform(
        (new_width, layer.size[1]),
        Image.AFFINE,
        matrix,
        resample=Image.Resampling.BICUBIC
    )


def paste_text_layer(canvas, center_xy, text, font, fill, stroke_fill=(0, 0, 0, 0), stroke_width=0, opacity=255, italic=False):
    layer = make_stroke_text_layer(text, font, fill, stroke_fill, stroke_width)
    if italic:
        layer = transform_italic_layer(layer)
    if opacity < 255:
        alpha = layer.getchannel("A").point(lambda a: int(a * opacity / 255))
        layer.putalpha(alpha)
    center_x, center_y = center_xy
    x = int(round(center_x - layer.size[0] / 2))
    y = int(round(center_y - layer.size[1] / 2))
    canvas.paste(layer, (x, y), layer)
    return (x, y, x + layer.size[0], y + layer.size[1])


def make_outlined_icon_card(icon_src, icon_size, border_px, radius_ratio=0.18, shadow_alpha=0, shadow_blur=0, shadow_offset=(0, 0), inner_shadow_alpha=0):
    card_size = icon_size + border_px * 2
    layer = Image.new("RGBA", (card_size, card_size), (0, 0, 0, 0))
    outline_mask = Image.new("L", (card_size, card_size), 0)
    outline_draw = ImageDraw.Draw(outline_mask)
    outline_draw.rounded_rectangle(
        (0, 0, card_size - 1, card_size - 1),
        radius=int(card_size * radius_ratio),
        fill=255
    )

    if shadow_alpha > 0:
        shadow_layer = Image.new("RGBA", (card_size, card_size), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(
            (border_px + shadow_offset[0], border_px + shadow_offset[1], card_size - border_px + shadow_offset[0], card_size - border_px + shadow_offset[1]),
            radius=int(icon_size * radius_ratio),
            fill=(0, 0, 0, shadow_alpha)
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
        layer = Image.alpha_composite(layer, shadow_layer)

    frame = Image.new("RGBA", (card_size, card_size), (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame)
    frame_draw.rounded_rectangle(
        (0, 0, card_size - 1, card_size - 1),
        radius=int(card_size * radius_ratio),
        fill=(255, 255, 255, 255)
    )

    if inner_shadow_alpha > 0:
        inner = Image.new("RGBA", (card_size, card_size), (0, 0, 0, 0))
        inner_draw = ImageDraw.Draw(inner)
        inner_draw.rounded_rectangle(
            (border_px // 2, border_px // 2, card_size - border_px // 2 - 1, card_size - border_px // 2 - 1),
            radius=max(1, int(card_size * radius_ratio) - border_px // 2),
            fill=(0, 0, 0, inner_shadow_alpha)
        )
        inner = inner.filter(ImageFilter.GaussianBlur(max(2, border_px // 2)))
        frame = Image.alpha_composite(frame, inner)

    icon_layer = fit_cover(icon_src, (icon_size, icon_size)).convert("RGBA")
    icon_mask = Image.new("L", (icon_size, icon_size), 0)
    icon_mask_draw = ImageDraw.Draw(icon_mask)
    icon_mask_draw.rounded_rectangle(
        (0, 0, icon_size - 1, icon_size - 1),
        radius=int(icon_size * radius_ratio),
        fill=255
    )
    icon_rounded = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    icon_rounded.paste(icon_layer, (0, 0), icon_mask)
    frame.paste(icon_rounded, (border_px, border_px), icon_rounded)
    layer = Image.alpha_composite(layer, frame)
    return layer


def group_icons_with_fill(uploaded_files, group_size=4):
    files = list(uploaded_files or [])
    if not files:
        return []

    groups = []
    for start in range(0, len(files), group_size):
        chunk = files[start:start + group_size]
        if len(chunk) < group_size:
            chunk = chunk + [chunk[-1]] * (group_size - len(chunk))
        groups.append(chunk)
    return groups


class StoredUpload:
    def __init__(self, name, data, uid=None):
        self.name = name
        self._data = data
        self.size = len(data)
        self.uid = uid or uuid.uuid4().hex

    def getvalue(self):
        return self._data


def make_stored_uploads(uploaded_files):
    return [StoredUpload(file.name, file.getvalue()) for file in uploaded_files or []]


def uploads_signature(uploaded_files):
    return tuple((file.name, getattr(file, "size", 0)) for file in uploaded_files or [])


def reorder_uploads_by_names(uploaded_files, ordered_names):
    buckets = {}
    for file in uploaded_files or []:
        buckets.setdefault(file.name, deque()).append(file)

    reordered = []
    for name in ordered_names or []:
        queue = buckets.get(name)
        if queue:
            reordered.append(queue.popleft())

    leftovers = []
    for file in uploaded_files or []:
        queue = buckets.get(file.name)
        if queue and file in queue:
            queue.remove(file)
            leftovers.append(file)
    return reordered + leftovers


def build_thumbnail_data_uri(uploaded_file, max_size=(120, 120)):
    try:
        image = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGBA")
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
    except:
        return ""


def render_icon_preview_grid(uploaded_files, columns=4, key_prefix="icon_preview"):
    files = list(uploaded_files or [])
    if not files:
        return

    cols = st.columns(min(columns, max(1, len(files))))
    for idx, file in enumerate(files):
        with cols[idx % len(cols)]:
            try:
                thumb = Image.open(io.BytesIO(file.getvalue())).convert("RGBA")
                thumb.thumbnail((52, 52), Image.Resampling.LANCZOS)
                st.image(thumb, clamp=True)
            except:
                st.write("预览失败")
            st.caption(file.name)


def build_sortable_custom_style(uploaded_files, prefix):
    cards = list(uploaded_files or [])
    if not cards:
        return ""

    css = [
        """
        .sortable-component {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: flex-start;
            width: 100%;
        }
        .sortable-component.vertical {
            display: flex;
            flex-wrap: nowrap;
        }
        .sortable-container {
            width: 100%;
            padding: 0;
        }
        .sortable-container-body {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: flex-start;
            padding-top: 2px;
            counter-reset: upload-card;
        }
        .sortable-item {
            width: 82px;
            min-height: 84px;
            border-radius: 10px;
            border: 1px solid #d1d5db;
            background-color: #ffffff;
            background-repeat: no-repeat;
            background-position: center 10px;
            background-size: 30px 30px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
            padding: 46px 6px 8px 6px;
            font-size: 0;
            line-height: 1.1;
            text-align: center;
            color: transparent;
            word-break: break-all;
            cursor: grab;
        }
        .sortable-item::after {
            counter-increment: upload-card;
            content: counter(upload-card);
            display: block;
            font-size: 10px;
            line-height: 1;
            color: #111827;
        }
        .sortable-item:hover {
            border-color: #9ca3af;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.10);
        }
        .sortable-item.dragging {
            opacity: 0.88;
        }
        """
    ]
    for idx, file in enumerate(cards, start=1):
        thumb = build_thumbnail_data_uri(file)
        if thumb:
            css.append(
                f"""
                .sortable-component .sortable-container-body > .sortable-item:nth-child({idx}) {{
                    background-image: url("{thumb}");
                }}
                """
            )
    return "\n".join(css)


def render_sortable_upload_cards(uploaded_files, state_key):
    files = list(uploaded_files or [])
    if not files:
        return files

    item_labels = [getattr(file, "uid", str(index)) for index, file in enumerate(files, start=1)]
    custom_style = build_sortable_custom_style(files, state_key)
    sorted_labels = sort_items(
        item_labels,
        header=None,
        direction="horizontal",
        custom_style=custom_style,
        key=f"{state_key}_sortable"
    )
    if sorted_labels != item_labels:
        try:
            file_by_uid = {getattr(file, "uid", None): file for file in files}
            reordered = [file_by_uid[label] for label in sorted_labels if label in file_by_uid]
        except Exception:
            reordered = files
        if state_key == "general":
            st.session_state.general_uploaded_icons = reordered
            st.session_state.general_uploaded_source_signature = uploads_signature(reordered)
        else:
            st.session_state.template6_uploaded_icons = reordered
            st.session_state.template6_uploaded_source_signature = uploads_signature(reordered)
        trigger_rerun()
    return files


def move_item_in_list(items, index, direction):
    target = index + direction
    if index < 0 or index >= len(items) or target < 0 or target >= len(items):
        return items
    items = list(items)
    items[index], items[target] = items[target], items[index]
    return items


def trigger_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

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
if 'template_multiselect_value' not in st.session_state:
    st.session_state.template_multiselect_value = st.session_state.selected_templates or ["模板1：质感大icon"]
if 'template_copy_configs' not in st.session_state:
    st.session_state.template_copy_configs = {}
if 'template6_icon_mode' not in st.session_state:
    st.session_state.template6_icon_mode = "通用 Icon"
if 'general_uploaded_icons' not in st.session_state:
    st.session_state.general_uploaded_icons = []
if 'general_uploaded_source_signature' not in st.session_state:
    st.session_state.general_uploaded_source_signature = None
if 'icon_uploader_nonce' not in st.session_state:
    st.session_state.icon_uploader_nonce = 0
if 'template6_uploaded_icons' not in st.session_state:
    st.session_state.template6_uploaded_icons = []
if 'template6_uploaded_source_signature' not in st.session_state:
    st.session_state.template6_uploaded_source_signature = None
if 'template6_icon_uploader_nonce' not in st.session_state:
    st.session_state.template6_icon_uploader_nonce = 0


# ==================== 2. 全局独立辅助工具 ====================
def mask_rounded_rectangle(img, radius):
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + img.size, radius=radius, fill=255)
    img.putalpha(mask)
    return img

def make_rounded_icon_cover(icon_src, size, radius_ratio=0.155):
    icon_rgba = icon_src.convert("RGBA")
    if icon_rgba.getchannel("A").getbbox():
        rgb = icon_rgba.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
        alpha = icon_rgba.getchannel("A").resize((size, size), Image.Resampling.LANCZOS)
        matte = Image.new("RGB", (size, size), (255, 255, 255))
        matte.paste(rgb, (0, 0))
        icon_scaled = matte.convert("RGBA")
        icon_scaled.putalpha(alpha)
    else:
        icon_scaled = icon_rgba.resize((size, size), Image.Resampling.LANCZOS)
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
    icon_final.paste(icon_scaled, (0, 0), icon_scaled)
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
    },
    "模板5：双层图标风": {
        "mode": "智能批量宣传语",
        "main_title": "太平凡？换个人生！",
        "sub_title": "国王人生模拟器来啦",
        "promo_text": "太平凡？换个人生！\n国王人生模拟器来啦",
        "colors": {"tag": "#000000", "main": "#FFFFFF", "sub": "#000000"},
        "auto_color": False
    },
    "模板6：四宫格图标风": {
        "mode": "单组文案应用该模板全部图片",
        "main_title": "IOS游戏推荐",
        "sub_title": "",
        "promo_text": "IOS游戏推荐",
        "colors": {"tag": "#000000", "main": "#000000", "sub": "#000000"},
        "auto_color": False
    },
    "模板7：上头解压风": {
        "mode": "智能批量宣传语",
        "main_title": "超上头的解压小游戏",
        "sub_title": "解压休闲/打发时间/免费畅玩。",
        "promo_text": "超上头的解压小游戏\n解压休闲/打发时间/免费畅玩。",
        "colors": {"tag": "#FFFFFF", "main": "#2F1812", "sub": "#2F1812"},
        "auto_color": False
    },
    "模板8：方形强视觉": {
        "mode": "智能批量宣传语",
        "main_title": "不用下载不占内存",
        "sub_title": "好玩上头小游戏",
        "promo_text": "不用下载不占内存\n好玩上头小游戏",
        "colors": {"tag": "#FFFFFF", "main": "#1F1F1F", "sub": "#1F1F1F"},
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
    if "模板4" in template_choice or "模板6" in template_choice:
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

    if "模板6" in template_choice:
        return {
            "main_title": promo_line_1,
            "sub_title": "",
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
    paste_template1_decoration(canvas, draw, sub_title, sub_font_large, img_width // 2, sub_title_y, raw_rgb, f"{main_title} {sub_title}")
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

TEMPLATE5_MAIN_FONT_START = 200
TEMPLATE5_SUB_FONT_START = 90
TEMPLATE5_MAIN_Y_RATIO = 0.67
TEMPLATE5_SUB_Y_RATIO = 0.800
TEMPLATE6_TITLE_FONT_START = 180
TEMPLATE6_TITLE_Y_RATIO = 0.16
TEMPLATE6_GRID_TOP_RATIO = 0.34
TEMPLATE6_GRID_MARGIN_X_RATIO = 0.11
TEMPLATE6_GRID_GAP_X_RATIO = 0.075
TEMPLATE6_GRID_GAP_Y_RATIO = 0.085


def get_template_render_cache_key(template_choice):
    if "模板5" in template_choice:
        return (
            "template5",
            TEMPLATE5_MAIN_FONT_START,
            TEMPLATE5_SUB_FONT_START,
            TEMPLATE5_MAIN_Y_RATIO,
            TEMPLATE5_SUB_Y_RATIO
        )
    if "模板6" in template_choice:
        return (
            "template6",
            TEMPLATE6_TITLE_FONT_START,
            TEMPLATE6_TITLE_Y_RATIO,
            TEMPLATE6_GRID_TOP_RATIO,
            TEMPLATE6_GRID_MARGIN_X_RATIO,
            TEMPLATE6_GRID_GAP_X_RATIO,
            TEMPLATE6_GRID_GAP_Y_RATIO
        )
    return ("default",)


def render_template_5(icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, bg_source, bg_image_bytes):
    img_width, img_height = 1280, 1706

    if bg_source == "template5_uploaded_blur" and bg_image_bytes:
        bg_img = Image.open(io.BytesIO(bg_image_bytes)).convert("RGB")
        canvas = weaken_template5_background(bg_img, (img_width, img_height), allow_upscale=False).convert("RGBA")
    else:
        canvas = weaken_template5_background(icon_src, (img_width, img_height), allow_upscale=True).convert("RGBA")

    icon_size = int(img_width * 0.64)
    border = int(icon_size * 0.026)
    radius = int(icon_size * 0.17)
    icon_x = (img_width - icon_size) // 2
    icon_y = int(img_height * 0.075)

    shadow_pad = 78
    layer_size = icon_size + border * 2 + shadow_pad * 2
    shadow_layer = Image.new("RGBA", (layer_size, layer_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rounded_rectangle(
        (
            shadow_pad,
            shadow_pad + 18,
            shadow_pad + icon_size + border * 2,
            shadow_pad + icon_size + border * 2 + 18
        ),
        radius=radius + border,
        fill=(0, 0, 0, 88)
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(26))

    icon_card = Image.new("RGBA", (icon_size + border * 2, icon_size + border * 2), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(icon_card)
    card_draw.rounded_rectangle(
        (0, 0, icon_size + border * 2, icon_size + border * 2),
        radius=radius + border,
        fill=(255, 255, 255, 255)
    )

    icon_scaled = fit_cover(icon_src, (icon_size, icon_size)).convert("RGBA")
    icon_mask = Image.new("L", (icon_size, icon_size), 0)
    mask_draw = ImageDraw.Draw(icon_mask)
    mask_draw.rounded_rectangle((0, 0, icon_size, icon_size), radius=radius, fill=255)
    icon_rounded = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    icon_rounded.paste(icon_scaled, (0, 0), icon_mask)
    icon_card.paste(icon_rounded, (border, border), icon_rounded)

    icon_layer = Image.new("RGBA", (layer_size, layer_size), (0, 0, 0, 0))
    icon_layer = Image.alpha_composite(icon_layer, shadow_layer)
    icon_layer.paste(icon_card, (shadow_pad, shadow_pad), icon_card)
    canvas.paste(icon_layer, (icon_x - border - shadow_pad, icon_y - border - shadow_pad), icon_layer)

    draw = ImageDraw.Draw(canvas)
    main_stroke = 13
    sub_stroke = 9
    main_font = fit_font_to_width(font_main, main_title, TEMPLATE5_MAIN_FONT_START, int(img_width * 0.985), min_size=84, stroke_width=main_stroke)
    sub_font_large = fit_font_to_width(font_main, sub_title, TEMPLATE5_SUB_FONT_START, int(img_width * 0.86), min_size=66, stroke_width=sub_stroke)

    main_y = int(img_height * TEMPLATE5_MAIN_Y_RATIO)
    sub_y = int(img_height * TEMPLATE5_SUB_Y_RATIO)
    paste_centered_stroke_text(
        canvas,
        (img_width // 2, main_y),
        main_title,
        main_font,
        (255, 255, 255, 255),
        (0, 0, 0, 255),
        main_stroke
    )
    paste_template1_decoration(canvas, draw, sub_title, sub_font_large, img_width // 2, sub_y, raw_rgb, f"{main_title} {sub_title}")
    paste_centered_stroke_text(
        canvas,
        (img_width // 2, sub_y),
        sub_title,
        sub_font_large,
        (0, 0, 0, 255),
        (255, 255, 255, 255),
        sub_stroke
    )
    return canvas.convert("RGB")


TEMPLATE_REGISTRY["模板5：双层图标风"] = render_template_5


def render_template_6(canvas, icon_src_group, main_title, font_main, colors):
    img_width, img_height = canvas.size

    title_stroke = 14
    title_font = fit_font_to_width(font_main, main_title, TEMPLATE6_TITLE_FONT_START, int(img_width * 0.92), min_size=86, stroke_width=title_stroke)
    title_y = int(img_height * TEMPLATE6_TITLE_Y_RATIO)
    paste_shadowed_stroke_text(
        canvas,
        (img_width // 2, title_y),
        main_title,
        title_font,
        (0, 0, 0, 255),
        (255, 255, 255, 255),
        title_stroke,
        shadow_offset=(0, 6),
        shadow_blur=6,
        shadow_alpha=78
    )

    gap_x = int(img_width * TEMPLATE6_GRID_GAP_X_RATIO)
    gap_y = int(img_height * TEMPLATE6_GRID_GAP_Y_RATIO)
    margin_x = int(img_width * TEMPLATE6_GRID_MARGIN_X_RATIO)
    first_row_y = int(img_height * TEMPLATE6_GRID_TOP_RATIO)
    tile_w = int((img_width - margin_x * 2 - gap_x) / 2)
    tile_h = tile_w
    second_row_y = first_row_y + tile_h + gap_y

    positions = [
        (margin_x, first_row_y),
        (margin_x + tile_w + gap_x, first_row_y),
        (margin_x, second_row_y),
        (margin_x + tile_w + gap_x, second_row_y)
    ]

    for idx, (icon_src, (x, y)) in enumerate(zip(icon_src_group, positions)):
        icon_size = tile_w
        icon = make_rounded_icon_cover(icon_src, icon_size, radius_ratio=0.18).convert("RGBA")
        icon_shadow = Image.new("RGBA", (icon_size + 96, icon_size + 96), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(icon_shadow)
        shadow_draw.rounded_rectangle(
            (24, 28, 24 + icon_size, 28 + icon_size),
            radius=int(icon_size * 0.18),
            fill=(0, 0, 0, 100)
        )
        icon_shadow = icon_shadow.filter(ImageFilter.GaussianBlur(4))
        canvas.paste(icon_shadow, (x - 24, y - 18), icon_shadow)
        canvas.paste(icon, (x, y), icon)

    return canvas


def render_template_7(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors):
    img_width, img_height = canvas.size
    draw = ImageDraw.Draw(canvas)

    icon_size = int(img_width * 0.56)
    icon_border = int(icon_size * 0.028)
    icon_x = (img_width - (icon_size + icon_border * 2)) // 2
    icon_y = int(img_height * 0.14)

    icon_card = make_outlined_icon_card(
        icon_src,
        icon_size=icon_size,
        border_px=icon_border,
        radius_ratio=0.19,
        shadow_alpha=0,
        shadow_blur=0,
        inner_shadow_alpha=72
    )
    canvas.paste(icon_card, (icon_x, icon_y), icon_card)

    main_font = fit_font_to_width(font_main, main_title, int(img_width * 0.106), int(img_width * 0.88), min_size=90)
    sub_font_main = fit_font_to_width(sub_font, sub_title, int(img_width * 0.065), int(img_width * 0.84), min_size=58, stroke_width=4)

    main_y = int(img_height * 0.71)
    sub_y = int(img_height * 0.842)

    draw.text((img_width // 2, main_y), main_title, fill=colors["main"], font=main_font, anchor="mm")

    sub_shadow_font = sub_font_main
    shadow_layer = make_stroke_text_layer(sub_title, sub_shadow_font, (255, 255, 255, 255), (255, 255, 255, 255), 2)
    shadow_layer = transform_italic_layer(shadow_layer, shear_x=-0.16)
    shadow_alpha = shadow_layer.getchannel("A").point(lambda a: int(a * 120 / 255))
    shadow_layer.putalpha(shadow_alpha)
    shadow_x = int(round(img_width / 2 - shadow_layer.size[0] / 2 + 5))
    shadow_y = int(round(sub_y - shadow_layer.size[1] / 2 + 5))
    canvas.paste(shadow_layer, (shadow_x, shadow_y), shadow_layer)

    paste_text_layer(
        canvas,
        (img_width // 2, sub_y),
        sub_title,
        sub_font_main,
        colors["sub"],
        stroke_fill=colors["sub"],
        stroke_width=2,
        italic=True
    )
    return canvas


def render_template_8(canvas, icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, colors):
    img_width, img_height = canvas.size
    draw = ImageDraw.Draw(canvas)

    icon_size = int(img_width * 0.50)
    icon_border = int(icon_size * 0.030)
    icon_x = (img_width - (icon_size + icon_border * 2)) // 2
    icon_y = int(img_height * 0.17)

    icon_card = make_outlined_icon_card(
        icon_src,
        icon_size=icon_size,
        border_px=icon_border,
        radius_ratio=0.18,
        shadow_alpha=0,
        shadow_blur=0,
        inner_shadow_alpha=0
    )
    canvas.paste(icon_card, (icon_x, icon_y), icon_card)

    main_font = fit_font_to_width(font_main, main_title, int(img_width * 0.102), int(img_width * 0.88), min_size=86)
    sub_font_main = fit_font_to_width(font_main, sub_title, int(img_width * 0.102), int(img_width * 0.88), min_size=86)

    main_y = int(img_height * 0.75)
    sub_y = int(img_height * 0.875)

    draw.text((img_width // 2, main_y), main_title, fill=colors["main"], font=main_font, anchor="mm")
    draw.text((img_width // 2, sub_y), sub_title, fill=colors["sub"], font=sub_font_main, anchor="mm")
    return canvas


TEMPLATE_REGISTRY["模板6：四宫格图标风"] = render_template_6
TEMPLATE_REGISTRY["模板7：上头解压风"] = render_template_7
TEMPLATE_REGISTRY["模板8：方形强视觉"] = render_template_8


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
    icon_src = None
    icon_src_group = None
    if "模板6" in template_choice:
        icon_src_group = [Image.open(io.BytesIO(one_icon_bytes)).convert("RGBA") for one_icon_bytes in icon_bytes]
    else:
        icon_src = Image.open(io.BytesIO(icon_bytes)).convert("RGBA")

    try:
        color_source_bytes = icon_bytes[0] if "模板6" in template_choice else icon_bytes
        color_thief = ColorThief(io.BytesIO(color_source_bytes))
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
    if "模板5" in template_choice:
        canvas = render_template_5(icon_src, main_title, sub_title, font_main, sub_font, raw_rgb, bg_source, bg_image_bytes)
    elif "模板6" in template_choice:
        canvas, img_width, img_height = create_background_canvas(bg_config, idx, icon_hue)
        canvas = render_template_6(canvas, icon_src_group, main_title, font_main, colors)
    else:
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
    template_options = list(TEMPLATE_REGISTRY.keys())
    st.session_state.template_multiselect_value = [
        template_name for template_name in st.session_state.template_multiselect_value
        if template_name in template_options
    ] or ["模板1：质感大icon"]
    selected_templates = st.multiselect(
        "排版方案（最多选择 4 个）：",
        template_options,
        key="template_multiselect_value"
    )
    if len(selected_templates) > 4:
        st.warning("最多同时选择 4 个模板，已自动保留前 4 个。")
        selected_templates = selected_templates[:4]
        st.session_state.template_multiselect_value = selected_templates
    if not selected_templates:
        selected_templates = ["模板1：质感大icon"]
        st.warning("请至少选择 1 个模板，已默认使用模板1。")
        st.session_state.template_multiselect_value = selected_templates
    st.session_state.selected_templates = selected_templates
    template_choice = selected_templates[0]
        
    # 📍 [UI名称修改点] 视觉风格选项
    style_choice = st.selectbox("视觉风格", ["通用高端风", "可爱休闲风", "硬核竞技风"])

    # 📍 [UI名称修改点] 步骤二：上传 Icon
    st.header("2. 上传游戏 Icon")
    st.markdown('<div class="step-hint">支持 PNG、JPG；通用 Icon 最多 9 张，模板6 可切换专属素材池并按 4 张自动成组。</div>', unsafe_allow_html=True)
    template6_icon_mode = st.session_state.template6_icon_mode
    if any("模板6" in t for t in selected_templates):
        template6_icon_mode = st.radio(
            "模板6 Icon 来源：",
            ["通用 Icon", "模板6专属"],
            horizontal=True,
            key="template6_icon_mode"
        )
    uploaded_icons = list(st.session_state.general_uploaded_icons)
    if not uploaded_icons:
        uploaded_icons_raw = st.file_uploader(
            "选择 Icon 图像",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"icon_uploader_{st.session_state.icon_uploader_nonce}"
        )
        if uploaded_icons_raw:
            general_signature = uploads_signature(uploaded_icons_raw)
            st.session_state.general_uploaded_source_signature = general_signature
            st.session_state.general_uploaded_icons = make_stored_uploads(uploaded_icons_raw)
            trigger_rerun()

    if uploaded_icons and len(uploaded_icons) > 9:
        st.error("最多支持处理 9 张 Icon，超出部分将被自动截断。")
        st.session_state.general_uploaded_icons = uploaded_icons[:9]
        st.session_state.general_uploaded_source_signature = uploads_signature(st.session_state.general_uploaded_icons)
        trigger_rerun()
    
    uploaded_icons = uploaded_icons[:9]
    if uploaded_icons:
        clear_general_icon_col, general_icon_status_col = st.columns([1, 4])
        with clear_general_icon_col:
            if st.button("清空通用 Icon", use_container_width=True):
                st.session_state.general_uploaded_icons = []
                st.session_state.general_uploaded_source_signature = None
                st.session_state.icon_uploader_nonce += 1
                trigger_rerun()
        with general_icon_status_col:
            st.success(f"已载入 {len(uploaded_icons)} 张 Icon")
        render_sortable_upload_cards(uploaded_icons, "general")

    uploaded_icons_template6 = list(st.session_state.template6_uploaded_icons)
    if any("模板6" in t for t in selected_templates) and template6_icon_mode == "模板6专属":
        if not uploaded_icons_template6:
            template6_uploaded_raw = st.file_uploader(
                "选择模板6专属 Icon 图像",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"icon_uploader_template6_{st.session_state.template6_icon_uploader_nonce}"
            )
            if template6_uploaded_raw:
                raw_signature = uploads_signature(template6_uploaded_raw)
                st.session_state.template6_uploaded_source_signature = raw_signature
                st.session_state.template6_uploaded_icons = make_stored_uploads(template6_uploaded_raw)
                trigger_rerun()

        if uploaded_icons_template6:
            clear_col, count_col = st.columns([1, 4])
            with clear_col:
                if st.button("清空模板6专属", use_container_width=True):
                    st.session_state.template6_uploaded_icons = []
                    st.session_state.template6_uploaded_source_signature = None
                    st.session_state.template6_icon_uploader_nonce += 1
                    trigger_rerun()
            with count_col:
                st.success(f"模板6专属素材已载入 {len(uploaded_icons_template6)} 张 Icon，将按 4 张自动分组。")
            render_sortable_upload_cards(uploaded_icons_template6, "template6")

    st.session_state.fast_preview_mode = st.toggle(
        "快速预览模式",
        value=st.session_state.fast_preview_mode,
        help="开启后预览图使用较低画质，页面响应更快；导出前再准备高清图。"
    )

    # 📍 [UI名称修改点] 步骤三：背景画布设置
    st.header("3. 背景画布设置")
    st.markdown('<div class="step-hint">模板2使用背景图库随机匹配，模板4使用智能图库背景，模板1/3/7/8使用下面的批量背景设置。</div>', unsafe_allow_html=True)
    st.session_state.lock_background = st.toggle("锁定当前背景", value=st.session_state.lock_background)
    
    uploaded_bg = None
    bg_source = "纯白背景"
    bg_type = "同色清爽渐变"

    fixed_bg_templates = []
    if any("模板2" in t for t in selected_templates):
        fixed_bg_templates.append("模板2：背景图库随机匹配")
    if any("模板4" in t for t in selected_templates):
        fixed_bg_templates.append("模板4：智能图库匹配")
    if any("模板5" in t for t in selected_templates):
        fixed_bg_templates.append("模板5：双层图标背景")
    if fixed_bg_templates:
        st.info("；".join(fixed_bg_templates))
    bg_source = st.radio("模板1/3/7/8背景来源：", ["纯白背景", "AI智能渐变生成", "上传背景图"])

    if bg_source == "AI智能渐变生成":
        bg_type = st.selectbox("选择渐变美学风格：", ["同色清爽渐变", "多色梦幻渐变"])
    elif bg_source == "上传背景图":  # 🛠️ 修复：与单选框定义的字符串保持完全一致
        uploaded_bg = st.file_uploader("上传自定义背景大图：", type=["png", "jpg", "jpeg"], key="bg_uploader")

    global_background_config = make_background_config(bg_source, bg_type, uploaded_bg)

    template5_uploaded_bg = None
    template5_background_config = make_background_config("template5_icon_blur")
    if any("模板5" in t for t in selected_templates):
        st.markdown("**模板5专属背景**")
        template5_mode = st.radio(
            "模板5背景模式：",
            ["默认icon放大背景", "手动上传新背景"],
            horizontal=True,
            key="template5_bg_mode"
        )
        if template5_mode == "手动上传新背景":
            template5_uploaded_bg = st.file_uploader(
                "上传模板5专用背景图：",
                type=["png", "jpg", "jpeg"],
                key="template5_bg_uploader"
            )
            template5_background_config = make_background_config("template5_uploaded_blur", uploaded_file=template5_uploaded_bg)
        else:
            template5_background_config = make_background_config("template5_icon_blur")

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
                effective_icon_count = len(uploaded_icons_template6) if ("模板6" in template_name and template6_icon_mode == "模板6专属" and uploaded_icons_template6) else len(uploaded_icons)
                if effective_icon_count:
                    st.caption(f"已解析 {len(promo_groups)} 组，将按上传顺序匹配 {effective_icon_count} 张 Icon。")
            else:
                if "模板4" in template_name:
                    template_cfg["main_title"] = st.text_input("上方宣传语：", value=template_cfg["main_title"], key=f"main_title_{template_name}")
                    template_cfg["sub_title"] = global_game_name
                elif "模板6" in template_name:
                    template_cfg["main_title"] = st.text_input("宣传语：", value=template_cfg["main_title"], key=f"main_title_{template_name}")
                    template_cfg["sub_title"] = ""
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
            elif "模板6" in template_name:
                with st.expander("文字配色管理", expanded=True):
                    c1 = st.columns(1)[0]
                    template_cfg["colors"]["main"] = c1.color_picker("标题颜色", template_cfg["colors"].get("main", "#000000"), key=f"color_main_{template_name}")
                    template_cfg["colors"]["sub"] = template_cfg["colors"]["main"]
                    template_cfg["colors"]["tag"] = template_cfg["colors"]["main"]
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
    template5_background_config.get("bg_source"),
    len(template5_background_config.get("bg_image_bytes") or b""),
    get_template_render_cache_key(template_choice),
    tuple((file.name, getattr(file, "size", 0)) for file in uploaded_icons),
    st.session_state.template6_icon_mode if any("模板6" in t for t in selected_templates) else None,
    tuple((file.name, getattr(file, "size", 0)) for file in (uploaded_icons_template6 or []))
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

has_any_icons = bool(uploaded_icons) or (any("模板6" in t for t in selected_templates) and bool(uploaded_icons_template6))

if has_any_icons:
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
        if "模板6" in template_name:
            template6_files = uploaded_icons_template6 if (st.session_state.template6_icon_mode == "模板6专属" and uploaded_icons_template6) else uploaded_icons
            template6_groups = group_icons_with_fill(template6_files, 4)
            if not template6_groups and uploaded_icons:
                template6_groups = group_icons_with_fill(uploaded_icons, 4)

            for group_idx, group_files in enumerate(template6_groups):
                card_id = get_card_id(template_name, group_idx)
                card_copy = get_copywriting_for_card(
                    group_idx,
                    template_name,
                    copy_cfg["mode"],
                    st.session_state.batch_game_name,
                    copy_cfg["main_title"],
                    copy_cfg["sub_title"],
                    promo_groups
                )

                template_bg_config = global_background_config.copy()
                default_card_config = {
                    "main_title": card_copy["main_title"],
                    "sub_title": card_copy["sub_title"],
                    "tag_text": card_copy["tag_text"],
                    "colors": copy_cfg["colors"].copy(),
                    "auto_color": copy_cfg.get("auto_color", False),
                    "background": template_bg_config
                }
                default_card_config["background"]["bg_seed"] = st.session_state.random_seed + group_idx

                if card_id not in st.session_state.individual_configs:
                    st.session_state.individual_configs[card_id] = default_card_config
                elif card_id not in st.session_state.forked_cards:
                    st.session_state.individual_configs[card_id] = default_card_config
                    st.session_state.individual_configs[card_id]["background"]["bg_seed"] = st.session_state.random_seed + group_idx

                cfg = st.session_state.individual_configs[card_id]
                if "background" not in cfg:
                    cfg["background"] = template_bg_config
                    cfg["background"]["bg_seed"] = st.session_state.random_seed + group_idx
                if "auto_color" not in cfg:
                    cfg["auto_color"] = copy_cfg.get("auto_color", False)

                icon_bytes_group = tuple(one_file.getvalue() for one_file in group_files)
                first_icon_src = Image.open(io.BytesIO(icon_bytes_group[0])).convert("RGBA")
                try:
                    color_thief = ColorThief(io.BytesIO(icon_bytes_group[0]))
                    raw_rgb = color_thief.get_color(quality=1)
                    icon_hue, _, _ = colorsys.rgb_to_hls(raw_rgb[0]/255.0, raw_rgb[1]/255.0, raw_rgb[2]/255.0)
                except:
                    raw_rgb = (230, 45, 45)
                    icon_hue = 0.0

                bg_cfg = cfg.get("background", template_bg_config)
                card_seed = bg_cfg.get("bg_seed", st.session_state.random_seed + group_idx)
                render_args = (
                    icon_bytes_group,
                    group_idx,
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
                    icon_bytes_group,
                    group_idx,
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
                    "icon_idx": group_idx,
                    "card_id": card_id,
                    "name": f"group_{group_idx + 1}",
                    "canvas": canvas,
                    "render_args": render_args
                }
                generated_canvases.append(item)
                generated_by_template[template_name].append(item)

                if st.session_state.prepare_hd_downloads:
                    hd_png = render_card_png_bytes(*render_args[:3], 1280, *render_args[3:])
                    hd_image_bytes_map[card_id] = hd_png
        else:
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
                elif "模板5" in template_name:
                    template_bg_config = template5_background_config.copy()
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
    
    if generated_canvases:
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
