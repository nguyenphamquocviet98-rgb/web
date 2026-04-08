import time
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import ee
import folium
from folium.plugins import SideBySideLayers, MeasureControl, MousePosition
import geemap.foliumap as geemap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium


# =========================================================
# 1. CẤU HÌNH TRANG CHÍNH
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="VệTinh Pro – Phân Tích Không Gian",
    page_icon="🛰️",
    initial_sidebar_state="collapsed"
)

# =========================================================
# 2. CẤU HÌNH CHUNG & MAPPING 34 TỈNH THÀNH (TỐI ƯU 2025-2026)
# =========================================================
CONFIG = {
    "project_id":   "web-gis-key", 
    "admin_l1":     "FAO/GAUL/2015/level1",   
    "admin_l2":     "FAO/GAUL/2015/level2",   
    "scale":        250, 
    "years":        [str(y) for y in range(2018, 2027)], 
    "months":       [f"{i:02d}" for i in range(1, 13)],
    "vis": {
        "NDVI": {"min": 1, "max": 4, "palette": ["#e74c3c","#f1c40f","#2ecc71","#27ae60"]},
        "NDBI": {"min": 1, "max": 4, "palette": ["#27ae60","#f1c40f","#e67e22","#c0392b"]},
        "LST":  {"min": 1, "max": 4, "palette": ["#3498db","#f1c40f","#e67e22","#e74c3c"]},
    },
    "class_labels": {
        "NDVI": ["Nước/Đất trống","Đất thưa","Thực vật bụi","Rừng rậm"],
        "NDBI": ["Rừng/Nước","Đất trống","Đô thị thưa","Đô thị nén"],
        "LST":  ["Mát (<24°C)","Bình thường (24-29°C)","Nóng (29-34°C)","Rất nóng (>34°C)"],
    },
}
LAYER_COLORS = {"NDVI": "#10b981", "NDBI": "#6366f1", "LST": "#ef4444"}
SPATIAL_TOOLS = [
    "🔥 Bản đồ Điểm Nóng (Heatmap)",
    "📍 Dấu Vết Biến Động (Change Detection)",
    "🗺️ Phân Vùng Không Gian (Zonal Stats)",
    "📐 Phân Tích Gradient (Edge / Boundary)",
    "🌊 Lan Toa Đô Thị (Urban Sprawl Index)",
]

# TỐI ƯU MAPPING: Sáp nhập 63 tỉnh cũ thành 34 tỉnh mới của Việt Nam
VN_34_MAPPING = {
    "TP Hà Nội": ["Ha Noi"], "TP Huế": ["Thua Thien - Hue", "Thua Thien Hue"], "Quảng Ninh": ["Quang Ninh"],
    "Cao Bằng": ["Cao Bang"], "Lạng Sơn": ["Lang Son"], "Lai Châu": ["Lai Chau"], "Điện Biên": ["Dien Bien"],
    "Sơn La": ["Son La"], "Thanh Hóa": ["Thanh Hoa"], "Nghệ An": ["Nghe An"], "Hà Tĩnh": ["Ha Tinh"],
    "Tuyên Quang": ["Tuyen Quang", "Ha Giang"], "Lào Cai": ["Lao Cai", "Yen Bai"], "Thái Nguyên": ["Thai Nguyen", "Bac Kan"],
    "Phú Thọ": ["Phu Tho", "Hoa Binh", "Vinh Phuc"], "Bắc Ninh": ["Bac Ninh", "Bac Giang"], "Hưng Yên": ["Hung Yen", "Thai Binh"],
    "TP Hải Phòng": ["Hai Phong", "Hai Duong"], "Ninh Bình": ["Ninh Binh", "Ha Nam", "Nam Dinh"], "Quảng Trị": ["Quang Tri", "Quang Binh"],
    "TP Đà Nẵng": ["Da Nang", "Quang Nam"], "Quảng Ngãi": ["Quang Ngai", "Kon Tum"], "Gia Lai": ["Gia Lai", "Binh Dinh"],
    "Khánh Hòa": ["Khanh Hoa", "Ninh Thuan"], "Lâm Đồng": ["Lam Dong", "Dak Nong", "Binh Thuan"], "Đắk Lắk": ["Dak Lak", "Phu Yen"],
    "TP Hồ Chí Minh": ["Ho Chi Minh", "Ho Chi Minh city", "Ba Ria - Vung Tau", "Binh Duong"], "Đồng Nai": ["Dong Nai", "Binh Phuoc"],
    "Tây Ninh": ["Tay Ninh", "Long An"], "TP Cần Thơ": ["Can Tho", "Soc Trang", "Hau Giang"], "Vĩnh Long": ["Vinh Long", "Ben Tre", "Tra Vinh"],
    "Đồng Tháp": ["Dong Thap", "Tien Giang"], "Cà Mau": ["Ca Mau", "Bac Lieu"], "An Giang": ["An Giang", "Kien Giang"]
}


# =========================================================
# 3. CSS — LIGHT THEME TỐI ƯU GIAO DIỆN 3 CỘT
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800;900&display=swap');

:root {
    --primary:    #2563eb; --accent:     #7c3aed; --success:    #059669; --danger:     #dc2626; --secondary:  #d97706; 
    --bg:         #f8fafc; --surface:    #ffffff; --surface2:   #f1f5f9; --border:     #e2e8f0; --text:       #0f172a; 
    --muted:      #475569; --radius:     12px;    
}

html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif !important; }
body, html { background: var(--bg) !important; color: var(--text) !important; font-size: 15px; }

div.block-container { padding: 1.5rem 2rem 2.5rem; max-width: 100%; }
section[data-testid="stSidebar"] { display: none !important; }
p, li, span, label { color: var(--text) !important; }

div[data-testid="stButton"] button {
    height: 3.2rem !important; font-size: 15px !important; font-weight: 700 !important; 
    border-radius: 8px !important; letter-spacing: 0.5px; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    background: var(--surface); color: var(--text) !important; border: 1px solid var(--border);
}
div[data-testid="stButton"] button:hover {
    transform: translateY(-2px); border-color: var(--primary);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1) !important; color: var(--primary) !important;
}
div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), var(--accent)) !important; border: none !important; color: white !important;
}

.stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label { font-size: 14px !important; font-weight: 700 !important; color: var(--text) !important; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.stSelectbox > div > div, .stMultiSelect > div > div { background: var(--surface) !important; border: 1.5px solid var(--border) !important; border-radius: 8px !important; color: var(--text) !important; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02); }
.stSelectbox > div > div:hover, .stMultiSelect > div > div:hover { border-color: var(--primary) !important; }
.stSelectbox [data-baseweb="select"] > div, .stMultiSelect [data-baseweb="select"] > div { color: var(--text) !important; background: transparent !important; font-weight: 600; }
.stSelectbox input, .stMultiSelect input { color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; }
div[role="listbox"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important; padding: 4px !important; }
div[role="option"] { background: transparent !important; color: var(--text) !important; font-size: 14px !important; font-weight: 500 !important; border-radius: 6px !important; margin-bottom: 2px; transition: all 0.2s; }
div[role="option"]:hover { background: var(--surface2) !important; color: var(--primary) !important; }
div[role="option"][aria-selected="true"] { background: rgba(37, 99, 235, 0.1) !important; color: var(--primary) !important; border-left: 3px solid var(--primary) !important; }
span[data-baseweb="tag"] { background: var(--surface2) !important; color: var(--text) !important; border-radius: 4px !important; border: 1px solid var(--border); font-weight: 600 !important; }

.main-title { display:flex; align-items:center; justify-content:space-between; background: var(--surface); padding: 20px 30px; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: 1px solid var(--border); }
.main-title h1 { font-size: 26px !important; font-weight: 900 !important; color: var(--text) !important; margin:0 !important; letter-spacing: 0.5px; }
.main-title p  { font-size: 15px !important; color: var(--muted) !important; margin:8px 0 0 !important; font-weight: 500;}
.section-title { font-size: 16px !important; font-weight: 800 !important; color: var(--text) !important; display: flex; align-items: center; margin: 20px 0 12px !important; letter-spacing: 0.5px; }
.section-title::before { content: ''; display: inline-block; width: 4px; height: 18px; background: linear-gradient(to bottom, var(--primary), var(--accent)); border-radius: 4px; margin-right: 10px; }

.kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-align: center; transition: all 0.3s; margin-bottom: 12px; position: relative; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.kpi-card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: var(--primary); }
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 8px 16px rgba(0,0,0,0.06); border-color: var(--primary); }
.kpi-title { font-size: 12px !important; color: var(--muted) !important; text-transform: uppercase; font-weight: 800 !important; letter-spacing: 1px; margin-bottom: 6px; }
.kpi-value { font-size: 24px !important; font-weight: 900 !important; color: var(--text) !important; }

.chart-box { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 20px; }
.chart-title { font-size: 16px !important; font-weight: 800 !important; color: var(--text) !important; margin-bottom:4px !important; }
.chart-sub   { font-size: 13px !important; color: var(--muted) !important; margin-bottom:12px !important; border-bottom:1px solid var(--border); padding-bottom:10px; }
.report-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; position: relative; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.02);}
.report-card::after { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background: var(--primary); }
.banner { padding:14px 20px; border-radius:12px; font-size:16px !important; font-weight:700 !important; text-align:center; margin-bottom:16px; letter-spacing:0.5px; border: 1px solid var(--border);}
.banner-blue   { background: #eff6ff; color: #1e3a8a; border-color: #bfdbfe; }
.banner-purple { background: #f5f3ff; color: #4c1d95; border-color: #ddd6fe; }
.banner-red    { background: #fef2f2; color: #7f1d1d; border-color: #fecaca; }
.banner-teal   { background: #f0fdfa; color: #134e4a; border-color: #a7f3d0; }
.danger-title { font-size: 20px !important; font-weight: 900 !important; color: var(--text) !important; border-bottom: 2px dashed var(--border); padding-bottom: 12px; margin-bottom: 20px !important; text-transform: uppercase; letter-spacing: 1px; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
button[data-baseweb="tab"] { font-size: 15px !important; font-weight: 700 !important; color: var(--muted) !important; padding: 12px 16px !important;}
button[data-baseweb="tab"][aria-selected="true"] { color: var(--primary) !important; border-bottom: 3px solid var(--primary) !important; }
.stDataFrame { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 4. DATA MODEL & SESSION STATE
# =========================================================
@dataclass
class AnalysisParams:
    country:     str
    province:    str
    districts:   List[str]
    layer:       str
    year_base:   str
    month:       str
    years_multi: List[str]
    specific_id: Optional[str] = None

def init_session_state():
    defaults = {
        "image_options":       {"Ghép quý liền mạch (Mặc định)": None},
        "analyzed":            False,
        "params":              None,
        "result":              None,
        "display_year":        None,
        "map_mode":            "🎬 Tua lịch sử theo năm",
        "compare_left_year":   None,
        "compare_right_year":  None,
        "timeline_index":      0,
        "play_animation":      False,
        "play_speed":          1.0,
        "map_click_value":     None,
        "spatial_tool":        SPATIAL_TOOLS[0],
        "spatial_radius":      1500,
        "spatial_threshold":   0.2,
        "district_data":       None,   
        "district_year":       None,   
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()


# =========================================================
# 5. KHỞI TẠO GOOGLE EARTH ENGINE (BẢN CHUẨN ĐỂ UP WEB)
# =========================================================
def init_gee():
    try:
        # Kiểm tra xem có thông tin cấu hình Secrets trên Streamlit Cloud hay không
        if "GEE_EMAIL" in st.secrets and "GEE_KEY" in st.secrets:
            # Sử dụng Service Account để xác thực tự động trên Server
            credentials = ee.ServiceAccountCredentials(
                st.secrets["GEE_EMAIL"],
                st.secrets["GEE_KEY"]
            )
            ee.Initialize(credentials, project=CONFIG["project_id"])
        else:
            # Nếu chạy local ở máy tính cá nhân (dùng trình duyệt xác thực)
            ee.Initialize(project=CONFIG["project_id"])
    except Exception as e:
        st.error(f"❌ Lỗi khởi tạo GEE: {e}")
        st.stop()

# =========================================================
# 6. GEE CORE FUNCTIONS (ĐƯỢC TỐI ƯU CACHE & TILESCALE)
# =========================================================
def is_lst(layer): return layer == "LST"
def get_collection_name(layer): return "LANDSAT/LC08/C02/T1_L2" if is_lst(layer) else "COPERNICUS/S2_SR_HARMONIZED"
def get_thresholds(layer):
    if layer == "NDVI": return [0, 0.2, 0.5]
    if layer == "NDBI": return [-0.1, 0, 0.2]
    return [24, 29, 34]

def mask_s2(img):
    scl  = img.select("SCL")
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return img.updateMask(mask).divide(10000).copyProperties(img, img.propertyNames())

def mask_l8(img):
    qa   = img.select("QA_PIXEL")
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
    return img.updateMask(mask).copyProperties(img, img.propertyNames())

@st.cache_data(ttl=86400)
def get_countries():
    try: return sorted(ee.FeatureCollection(CONFIG["admin_l1"]).aggregate_array("ADM0_NAME").distinct().sort().getInfo() or [])
    except: return []

@st.cache_data(ttl=86400)
def get_provinces(country_name):
    if country_name == "Viet Nam": return list(VN_34_MAPPING.keys())
    try: return sorted(ee.FeatureCollection(CONFIG["admin_l1"]).filter(ee.Filter.eq("ADM0_NAME", country_name)).aggregate_array("ADM1_NAME").distinct().sort().getInfo() or [])
    except: return []

@st.cache_data(ttl=86400)
def get_districts(country_name, province_name):
    try:
        fc = ee.FeatureCollection(CONFIG["admin_l2"]).filter(ee.Filter.eq("ADM0_NAME", country_name))
        if country_name == "Viet Nam":
            fc = fc.filter(ee.Filter.inList("ADM1_NAME", VN_34_MAPPING.get(province_name, [province_name])))
        else:
            fc = fc.filter(ee.Filter.eq("ADM1_NAME", province_name))
        return sorted(fc.aggregate_array("ADM2_NAME").distinct().sort().getInfo() or [])
    except: return []

def get_roi_l1(country, province):
    if country == "Viet Nam":
        return ee.FeatureCollection(CONFIG["admin_l1"]).filter(ee.Filter.eq("ADM0_NAME", country)).filter(ee.Filter.inList("ADM1_NAME", VN_34_MAPPING.get(province, [province])))
    return ee.FeatureCollection(CONFIG["admin_l1"]).filter(ee.Filter.eq("ADM0_NAME", country)).filter(ee.Filter.eq("ADM1_NAME", province))

def get_roi_l2(country, province):
    if country == "Viet Nam":
        return ee.FeatureCollection(CONFIG["admin_l2"]).filter(ee.Filter.eq("ADM0_NAME", country)).filter(ee.Filter.inList("ADM1_NAME", VN_34_MAPPING.get(province, [province])))
    return ee.FeatureCollection(CONFIG["admin_l2"]).filter(ee.Filter.eq("ADM0_NAME", country)).filter(ee.Filter.eq("ADM1_NAME", province))

def get_dynamic_roi(country, province, districts):
    """Tính năng Phễu Lọc: Trả về ranh giới Tỉnh nếu không chọn huyện, hoặc ranh giới Huyện nếu có chọn."""
    if not districts: return get_roi_l1(country, province)
    return get_roi_l2(country, province).filter(ee.Filter.inList("ADM2_NAME", districts))

def get_image(geom, year, month, layer, specific_id=None):
    lst_mode = is_lst(layer)
    if specific_id:
        img = ee.Image(specific_id)
        img = mask_l8(img) if lst_mode else mask_s2(img)
    else:
        start = ee.Date.fromYMD(int(year), int(month), 1)
        col   = ee.ImageCollection(get_collection_name(layer)).filterBounds(geom).filterDate(start, start.advance(3, "month"))
        img   = col.map(mask_l8 if lst_mode else mask_s2).median()
    img = ee.Image(img)
    if lst_mode:
        return img.addBands(img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST")).clip(geom)
    return img.addBands([img.normalizedDifference(["B8","B4"]).rename("NDVI"), img.normalizedDifference(["B11","B8"]).rename("NDBI")]).clip(geom)

def classify(img, layer):
    band = img.select(layer); t = get_thresholds(layer)
    return ee.Image(1).where(band.gte(t[0]).And(band.lt(t[1])), 2).where(band.gte(t[1]).And(band.lt(t[2])), 3).where(band.gte(t[2]), 4).updateMask(band.mask()).rename("CLASS").toInt()

@st.cache_data(ttl=3600, show_spinner=False)
def search_best_images(country, province, districts, year, month, layer):
    try:
        roi = get_dynamic_roi(country, province, districts)
        start_date = ee.Date.fromYMD(int(year), int(month), 1)
        cloud_prop = "CLOUD_COVER" if is_lst(layer) else "CLOUDY_PIXEL_PERCENTAGE"
        col = ee.ImageCollection(get_collection_name(layer)).filterBounds(roi.geometry()).filterDate(start_date.advance(-15,"day"), start_date.advance(15,"day")).sort(cloud_prop).limit(10)
        options = {"Ghép quý liền mạch (Mặc định)": None}
        for f in col.getInfo().get("features", []):
            options[f"{f['id'].split('/')[-1]} ({f['properties'].get(cloud_prop, 0):.1f}% mây)"] = f["id"]
        return options if len(options) > 1 else {"Không tìm thấy ảnh, dùng mặc định": None}
    except: return {"Lỗi tải ảnh - dùng mặc định": None}


# =========================================================
# 7. PHÂN TÍCH KHÔNG GIAN NÂNG CAO
# =========================================================
def spatial_change_detection(img_base, img_target, layer): return img_target.select(layer).subtract(img_base.select(layer)).rename("CHANGE")
def spatial_heatmap(img, layer, radius_meters=1500): return img.select(layer).reduceNeighborhood(reducer=ee.Reducer.mean(), kernel=ee.Kernel.circle(radius=radius_meters, units='meters')).rename("HOTSPOT")
def spatial_gradient(img, layer): return img.select(layer).gradient().pow(2).reduce(ee.Reducer.sum()).sqrt().rename("GRADIENT")
def spatial_binary_mask(img, layer, threshold): return img.select(layer).gte(threshold).selfMask().rename("MASK")
def urban_sprawl_index(img): return img.select("NDBI").subtract(img.select("NDVI")).rename("SPRAWL")


# =========================================================
# 8. THỐNG KÊ & ĐO ĐẠC TOÁN HỌC GEE
# =========================================================
def get_area_groups(classified_img, geom, scale):
    return ee.Image.pixelArea().divide(10000).addBands(classified_img).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1), geometry=geom, scale=scale*2, maxPixels=1e13, tileScale=4, bestEffort=True
    ).getInfo().get("groups", [])

def extract_area(groups, class_num): return next((g["sum"] for g in groups or [] if int(g["group"]) == class_num), 0.0)

def get_stats(img, layer, geom, scale):
    return img.select(layer).reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.min(), sharedInputs=True).combine(ee.Reducer.max(), sharedInputs=True),
        geometry=geom, scale=scale*2, maxPixels=1e13, tileScale=4, bestEffort=True
    ).getInfo()

def get_histogram(img, layer, geom, scale):
    return img.select(layer).reduceRegion(
        reducer=ee.Reducer.histogram(20), geometry=geom, scale=scale*4, maxPixels=1e13, tileScale=4, bestEffort=True
    ).getInfo().get(layer, {})

def get_pixel_value(img, layer, lat, lon, scale=30):
    try: return img.select(layer).reduceRegion(reducer=ee.Reducer.first(), geometry=ee.Geometry.Point([lon, lat]), scale=scale, maxPixels=1e13, bestEffort=True).getInfo().get(layer)
    except: return None

@st.cache_data(ttl=3600, show_spinner=False)
def get_full_history_at_point(lat, lon, layer, month):
    point = ee.Geometry.Point([lon, lat]); history = []
    for y in CONFIG["years"]:
        try:
            val = get_image(point, y, month, layer).select(layer).reduceRegion(
                reducer=ee.Reducer.first(), geometry=point, scale=30 if layer=="LST" else 10, bestEffort=True
            ).getInfo().get(layer)
            history.append({"Năm": y, "Chỉ số": val})
        except: history.append({"Năm": y, "Chỉ số": None})
    return pd.DataFrame(history)

@st.cache_data(ttl=1800, show_spinner=False)
def compute_district_stats(country: str, province: str, layer: str, year: str, month: str) -> pd.DataFrame:
    try:
        districts_fc = get_roi_l2(country, province)
        if not districts_fc.aggregate_array("ADM2_NAME").getInfo(): return pd.DataFrame()

        geom = get_roi_l1(country, province).geometry()
        img  = get_image(geom, year, month, layer)

        reduced = img.select(layer).reduceRegions(
            collection=districts_fc,
            reducer=ee.Reducer.mean().combine(ee.Reducer.min(), sharedInputs=True).combine(ee.Reducer.max(), sharedInputs=True).combine(ee.Reducer.stdDev(), sharedInputs=True).combine(ee.Reducer.count(), sharedInputs=True),
            scale=CONFIG["scale"] * 2, tileScale=4,
        )

        t = get_thresholds(layer)
        area_img = ee.Image.pixelArea().divide(10000).updateMask(img.select(layer).gte(t[-1]))
        area_reduced = area_img.rename("HIGH_AREA").reduceRegions(
            collection=districts_fc, reducer=ee.Reducer.sum(), scale=CONFIG["scale"] * 2, tileScale=4,
        )

        feats   = reduced.getInfo()["features"]
        a_feats = {f["properties"].get("ADM2_NAME"): f["properties"].get("sum", 0) for f in area_reduced.getInfo()["features"]}

        rows = []
        for f in feats:
            p = f["properties"]; name = p.get("ADM2_NAME", "Không rõ")
            rows.append({
                "Huyện": name, "Trung bình": p.get("mean"), "Thấp nhất": p.get("min"), "Cao nhất": p.get("max"),
                "Độ lệch chuẩn": p.get("stdDev"), "Điểm ảnh": int(p.get("count", 0)), "Ha vượt ngưỡng": round(a_feats.get(name, 0), 1),
            })
        df = pd.DataFrame(rows).dropna(subset=["Trung bình"]).sort_values("Trung bình", ascending=False).reset_index(drop=True)
        df["Hạng"] = range(1, len(df) + 1)
        return df
    except Exception as e:
        st.error(f"Lỗi tính thống kê huyện: {e}")
        return pd.DataFrame()

def analyze_region(params: AnalysisParams):
    roi   = get_dynamic_roi(params.country, params.province, params.districts)
    geom  = roi.geometry()
    years = sorted(params.years_multi) if params.years_multi else [params.year_base]

    year_data = {}
    for year in years:
        img = get_image(geom, year, params.month, params.layer, params.specific_id if year == params.year_base else None)
        year_data[year] = {
            "image": img, "class": classify(img, params.layer).clip(geom),
            "mean": img.select(params.layer).reduceRegion(reducer=ee.Reducer.mean(), geometry=geom, scale=CONFIG["scale"]*4, maxPixels=1e13, tileScale=4, bestEffort=True).getInfo().get(params.layer)
        }

    first_y = years[0]; last_y = years[-1]
    area_first = get_area_groups(year_data[first_y]["class"], geom, CONFIG["scale"])
    area_last  = get_area_groups(year_data[last_y]["class"],  geom, CONFIG["scale"])
    stats_last = get_stats(year_data[last_y]["image"], params.layer, geom, CONFIG["scale"])
    hist_last  = get_histogram(year_data[last_y]["image"], params.layer, geom, CONFIG["scale"])

    trend_data = [{"Năm": y, "Trị số": year_data[y]["mean"]} for y in years if year_data[y]["mean"] is not None]
    
    # Biểu đồ so sánh Huyện (nếu có chọn từ 2 đến 4 huyện)
    bar_data = []
    if params.districts and len(params.districts) >= 2:
        for dist in params.districts:
            try:
                p_geom = roi.filter(ee.Filter.eq("ADM2_NAME", dist)).geometry()
                p_mean = year_data[last_y]["image"].select(params.layer).reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=p_geom, scale=CONFIG["scale"]*2, maxPixels=1e13, tileScale=4, bestEffort=True
                ).getInfo().get(params.layer)
                if p_mean is not None: bar_data.append({"Khu vực": dist, "Trị số": p_mean})
            except: continue

    roi_names = " & ".join(params.districts) if params.districts else params.province

    return {
        "roi": roi, "geom": geom, "years": years,
        "first_y": first_y, "last_y": last_y,
        "area_first": area_first, "area_last": area_last,
        "stats_last": stats_last, "hist_last": hist_last,
        "trend_data": trend_data, "bar_data": bar_data,
        "year_data": year_data, "roi_names": roi_names,
    }


# =========================================================
# 9. VẼ BẢN ĐỒ VÀ TOOLTIP
# =========================================================
def add_legend(m, layer):
    labels = CONFIG["class_labels"][layer]; colors = CONFIG["vis"][layer]["palette"]
    html   = f'''<div style="position:fixed;bottom:36px;left:36px;z-index:9999;background:rgba(255,255,255,.92);padding:18px 22px;border-radius:14px;border:1.5px solid #e2e8f0;box-shadow:0 10px 30px rgba(0,0,0,.15);"><div style="color:#000000;font-size:18px;font-weight:900;border-bottom:2px solid #e2e8f0;padding-bottom:8px;margin-bottom:12px;">📌 Chú giải {layer}</div>'''
    for label, color in zip(labels, colors): html += f'''<div style="display:flex;align-items:center;margin-bottom:10px;"><div style="background:{color};width:30px;height:30px;border-radius:7px;margin-right:14px;border:1px solid rgba(0,0,0,.1);flex-shrink:0;"></div><span style="font-size:16px;font-weight:800;color:#000000;">{label}</span></div>'''
    m.get_root().html.add_child(folium.Element(html + '</div>'))

def base_map():
    m = folium.Map(location=[16.0, 106.0], zoom_start=6, control_scale=True, tiles=None)
    folium.TileLayer("OpenStreetMap", name="Bản đồ nền", overlay=False, control=True).add_to(m)
    folium.TileLayer("Esri.WorldImagery", name="Ảnh vệ tinh", overlay=False, control=True, attr="Esri").add_to(m)
    MeasureControl(primary_length_unit='kilometers').add_to(m)
    MousePosition(position='bottomright', separator=' | ', prefix='Tọa độ:').add_to(m)
    return m

def center_map(m, result):
    """Tính năng Zoom tự động vào khung bản đồ"""
    try: 
        bounds = result["geom"].bounds().coordinates().getInfo()[0]
        lons = [pt[0] for pt in bounds]
        lats = [pt[1] for pt in bounds]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
    except: 
        try:
            c = result["geom"].centroid(1).coordinates().getInfo()
            m.location = [c[1], c[0]]; m.zoom_start = 10
        except: pass

def add_boundary(m, roi, color="#ff0000", weight=3):
    geemap.ee_tile_layer(ee.Image().paint(roi, 0, weight), {"palette": [color]}, "Ranh giới phân tích", True, 1.0).add_to(m)

def add_district_boundaries(m, country, province, df_district=None, bar_data=None, layer_name="Chỉ số"):
    try:
        districts_fc = get_roi_l2(country, province)
        geojson_data = districts_fc.getInfo()

        value_map = {}
        if df_district is not None and not df_district.empty:
            for _, row in df_district.iterrows():
                value_map[row["Huyện"]] = row["Trung bình"]
        elif bar_data:
            for item in bar_data:
                value_map[item["Khu vực"]] = item["Trị số"]

        for feature in geojson_data["features"]:
            name = feature["properties"].get("ADM2_NAME", "")
            val = value_map.get(name)
            if val is not None:
                feature["properties"]["CHISO_HIENTHI"] = f"{val:.3f}"
            else:
                feature["properties"]["CHISO_HIENTHI"] = "Chưa đo đạc"

        def style_fn(feature):
            val_str = feature["properties"].get("CHISO_HIENTHI", "")
            try: val = float(val_str)
            except: val = None
            
            if val is not None and len(value_map) > 0:
                mn = min(value_map.values()); mx = max(value_map.values())
                norm = (val - mn) / (mx - mn + 1e-9)
                r = int(norm * 220); g = int((1 - abs(norm - 0.5) * 2) * 180); b = int((1 - norm) * 220)
                return {"color": "#f59e0b", "weight": 2, "fillColor": f"#{r:02x}{g:02x}{b:02x}", "fillOpacity": 0.45}
            return {"color": "#f59e0b", "weight": 2, "fillColor": "#94a3b8", "fillOpacity": 0.15}

        folium.GeoJson(
            geojson_data,
            name="🗺️ Ranh giới Huyện (Hover)",
            style_function=style_fn, 
            highlight_function=lambda x: {"color": "#ffffff", "weight": 3, "fillOpacity": 0.65}, 
            tooltip=folium.GeoJsonTooltip(
                fields=["ADM2_NAME", "CHISO_HIENTHI"], 
                aliases=["📍 Huyện:", f"📈 {layer_name} (Trung bình):"],
                style="font-family:'Be Vietnam Pro',sans-serif;font-size:15px;font-weight:700;background:#ffffff;color:#0f172a;border:1px solid #e2e8f0;border-radius:8px;padding:12px;box-shadow:0 4px 10px rgba(0,0,0,0.1);"
            )
        ).add_to(m)
    except: pass  

def build_single_map(result, layer, display_year, show_districts=False, country=None, province=None, df_district=None):
    m = base_map()
    geemap.ee_tile_layer(result["year_data"][display_year]["class"], CONFIG["vis"][layer], f"Phân loại {layer} ({display_year})", True, 0.9).add_to(m)
    add_boundary(m, result["roi"])
    if show_districts and country and province: 
        add_district_boundaries(m, country, province, df_district, result.get("bar_data"), layer)
    add_legend(m, layer); center_map(m, result); folium.LayerControl(collapsed=False).add_to(m)
    return m

def build_swipe_map(result, layer, left_year, right_year):
    m = base_map()
    l = geemap.ee_tile_layer(result["year_data"][left_year]["class"],  CONFIG["vis"][layer], f"{layer} {left_year}",  True, 1.0)
    r = geemap.ee_tile_layer(result["year_data"][right_year]["class"], CONFIG["vis"][layer], f"{layer} {right_year}", True, 1.0)
    l.add_to(m); r.add_to(m); SideBySideLayers(l, r).add_to(m)
    add_boundary(m, result["roi"]); add_legend(m, layer); center_map(m, result); folium.LayerControl(collapsed=False).add_to(m)
    return m

def build_spatial_map(result, layer, base_year, target_year, spatial_tool, radius, threshold):
    m = base_map()
    img_base = result["year_data"][base_year]["image"]; img_target = result["year_data"][target_year]["image"]
    geemap.ee_tile_layer(result["year_data"][target_year]["class"], CONFIG["vis"][layer], f"Phân loại {layer} ({target_year})", False, 0.7).add_to(m)

    if "Điểm Nóng" in spatial_tool: geemap.ee_tile_layer(spatial_heatmap(img_target, layer, radius), {'min':0,'max': 0.4 if layer!='LST' else 35, 'palette':['#ffffff','#fef0d9','#fdcc8a','#fc8d59','#e34a33','#b30000']}, f"🔥 Heatmap ({target_year})", True, 0.85).add_to(m)
    if "Biến Động" in spatial_tool: geemap.ee_tile_layer(spatial_change_detection(img_base, img_target, layer), {'min':-0.3,'max':0.3,'palette':['#dc2626','#f5f5f5','#1d4ed8' if layer=='NDBI' else '#10b981']}, f"📍 Biến Động", True, 0.9).add_to(m)
    if "Gradient" in spatial_tool: geemap.ee_tile_layer(spatial_gradient(img_target, layer), {'min':0,'max':0.05,'palette':['#000000','#4b5563','#f59e0b','#dc2626']}, f"📐 Gradient", True, 0.9).add_to(m)
    if "Lan Toa" in spatial_tool: geemap.ee_tile_layer(urban_sprawl_index(img_target), {'min':-0.5,'max':0.5,'palette':['#064e3b','#6ee7b7','#fef3c7','#f97316','#7f1d1d']}, f"🌊 Lan Toa", True, 0.85).add_to(m)
    if "Zonal" in spatial_tool or "Phân Vùng" in spatial_tool: geemap.ee_tile_layer(spatial_binary_mask(img_target, layer, threshold), {'min':0,'max':1,'palette':['#00000000','#dc2626']}, f"🗺️ Vùng ≥{threshold:.2f}", True, 0.6).add_to(m)

    add_boundary(m, result["roi"]); center_map(m, result); folium.LayerControl(collapsed=False).add_to(m)
    return m


# =========================================================
# 10. GIAO DIỆN & TRÌNH TRÌNH BÀY DỮ LIỆU
# =========================================================
def get_unit_str(layer): return "°C" if layer=="LST" else "Chỉ số"
def get_layer_name(layer): return {"LST":"Nhiệt độ bề mặt","NDVI":"Mật độ Cây xanh","NDBI":"Độ phủ Bê tông"}.get(layer, layer)
def fmt(layer, v): return "—" if v is None else f"{v:.2f} °C" if layer=="LST" else f"{v:.4f}"
def hex_to_rgba(h, a): h = h.lstrip('#'); return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

st.markdown("""
<div class="main-title">
    <h1>🛰️ HỆ THỐNG PHÂN TÍCH VỆ TINH</h1>
    <p>Xây dựng hệ thống mô phỏng và trực quan hóa
biến động đô thị hóa dựa trên ảnh vệ tinh
</p>
</div>
""", unsafe_allow_html=True)

col_ctrl, col_map, col_report = st.columns([1.25, 2.75, 1.5], gap="large")

# ════════ CỘT 1: BẢNG ĐIỀU KHIỂN ════════
with col_ctrl:
    with st.container(height=1180, border=False):
        with st.container(border=True):
            st.markdown("<div class='section-title'>1️⃣ Khu vực phân tích</div>", unsafe_allow_html=True)
            countries = get_countries()
            country   = st.selectbox("Quốc gia", countries, index=countries.index("Viet Nam") if "Viet Nam" in countries else 0)

            provinces_list = get_provinces(country)
            selected_prov = st.selectbox("Tỉnh / Thành phố", provinces_list, index=provinces_list.index("Bắc Ninh") if "Bắc Ninh" in provinces_list else 0)

            districts_list = get_districts(country, selected_prov)
            selected_districts = st.multiselect("Lọc theo Huyện hoặc tiểu Bang (Max 4)", districts_list, max_selections=4, placeholder="Bỏ trống để xem toàn Tỉnh...")

            if not selected_districts: st.info(f"📍 Đang lấy ranh giới toàn tỉnh **{selected_prov}**.")
            else: st.success(f"✅ Đã Focus ranh giới vào {len(selected_districts)} Huyện.")

        with st.container(border=True):
            st.markdown("<div class='section-title'>2️⃣ Cấu hình vệ tinh</div>", unsafe_allow_html=True)
            layer     = st.selectbox("Chỉ số phân tích", ["NDVI","NDBI","LST"])
            c1, c2    = st.columns(2)
            year_base = c1.selectbox("Năm gốc", CONFIG["years"], index=CONFIG["years"].index("2026"))
            month     = c2.selectbox("Tháng", CONFIG["months"], index=2)

            if st.button("🔎 Quét ảnh sạch mây", use_container_width=True):
                with st.spinner("⏳ Đang quét từ GEE..."):
                    st.session_state["image_options"] = search_best_images(country, selected_prov, selected_districts, year_base, month, layer)
                    st.success("✅ Tìm thấy ảnh.")

            specific_img_id = st.session_state["image_options"][st.selectbox("Chọn ảnh vệ tinh", list(st.session_state["image_options"].keys()))]

        with st.container(border=True):
            st.markdown("<div class='section-title'>3️⃣ Dải thời gian</div>", unsafe_allow_html=True)
            years_multi = st.multiselect("So sánh qua các năm", CONFIG["years"], default=["2022","2024","2026"])

        run_btn = st.button("🚀 XUẤT BẢN ĐỒ & BÁO CÁO", use_container_width=True, type="primary")

        if run_btn:
            params = AnalysisParams(
                country=country, province=selected_prov, districts=selected_districts, layer=layer,
                year_base=year_base, month=month, years_multi=years_multi, specific_id=specific_img_id,
            )
            with st.spinner("⏳ Vệ tinh đang đo đạc. Việc chia nhỏ tỷ lệ TileScale có thể mất vài giây..."):
                try:
                    result = analyze_region(params)
                    st.session_state.update({
                        "params": params, "result": result, "analyzed": True,
                        "display_year": result["last_y"], "timeline_index": result["years"].index(result["last_y"]),
                        "compare_left_year": result["years"][0], "compare_right_year": result["years"][-1],
                        "play_animation": False, "map_click_value": None, "district_data": None, "district_year": None,
                    })
                    st.success("✅ Dữ liệu đã tải xong!")
                except Exception as e:
                    st.session_state["analyzed"] = False; st.error(f"❌ Cảnh báo GEE: {str(e)[:140]}")

        if st.session_state["analyzed"] and st.session_state["result"] is not None:
            result_years = st.session_state["result"]["years"]

            st.markdown("<div class='section-title'>4️⃣ Chế độ bản đồ</div>", unsafe_allow_html=True)
            map_mode = st.radio("Chế độ", ["🎬 Tua lịch sử theo năm", "🪞 So sánh kéo thanh (Swipe)", "🔬 Phân tích Không Gian"], label_visibility="collapsed")
            st.session_state["map_mode"] = map_mode

            show_districts_on_map = st.checkbox("🗺️ Bật Tooltip Huyện (Hover Map)", value=True) if not selected_districts else True

            if map_mode == "🎬 Tua lịch sử theo năm":
                st.markdown("<div class='section-title'>5️⃣ Thanh thời gian</div>", unsafe_allow_html=True)
                cur = st.session_state["timeline_index"]; cp, cn = st.columns(2)
                if cp.button("⏮️ Lùi", use_container_width=True): st.session_state["timeline_index"] = max(0, cur-1); st.session_state["play_animation"] = False
                if cn.button("⏭️ Tiến", use_container_width=True): st.session_state["timeline_index"] = min(len(result_years)-1, cur+1); st.session_state["play_animation"] = False

                st.session_state["timeline_index"] = st.slider("Thanh thời gian", 0, len(result_years)-1, st.session_state["timeline_index"], label_visibility="collapsed")
                st.session_state["display_year"] = result_years[st.session_state["timeline_index"]]
                
                c1b, c2b = st.columns(2)
                if c1b.button("▶️ Tự chạy", use_container_width=True): st.session_state["play_animation"] = True
                if c2b.button("⏹️ Dừng", use_container_width=True): st.session_state["play_animation"] = False
                st.session_state["play_speed"] = st.select_slider("Tốc độ", [0.5,1.0,1.5,2.0], st.session_state["play_speed"])

            else:
                st.markdown("<div class='section-title'>5️⃣ Cài đặt so sánh</div>", unsafe_allow_html=True)
                if st.session_state["compare_left_year"] not in result_years: st.session_state["compare_left_year"] = result_years[0]
                if st.session_state["compare_right_year"] not in result_years: st.session_state["compare_right_year"] = result_years[-1]

                st.session_state["compare_left_year"]  = st.selectbox("📅 Năm cũ (Trái)", result_years, index=result_years.index(st.session_state["compare_left_year"]))
                st.session_state["compare_right_year"] = st.selectbox("📅 Năm mới (Phải)", result_years, index=result_years.index(st.session_state["compare_right_year"]))

                if st.button("🔁 Đổi Trái/Phải", use_container_width=True):
                    l,r = st.session_state["compare_left_year"], st.session_state["compare_right_year"]
                    st.session_state["compare_left_year"] = r; st.session_state["compare_right_year"] = l

                if map_mode == "🔬 Phân tích Không Gian":
                    st.markdown("<div class='section-title'>6️⃣ Công cụ không gian</div>", unsafe_allow_html=True)
                    st.session_state["spatial_tool"]      = st.selectbox("Phương pháp", SPATIAL_TOOLS, label_visibility="collapsed")
                    st.session_state["spatial_radius"]    = st.slider("Bán kính làm mịn (m)", 500, 5000, st.session_state["spatial_radius"], 250)
                    st.session_state["spatial_threshold"] = st.slider("Ngưỡng phân vùng", -0.5, 1.0, st.session_state["spatial_threshold"], 0.05)

            if not selected_districts:
                st.markdown("<div class='section-title'>6️⃣ Thống kê Huyện</div>", unsafe_allow_html=True)
                district_year_sel = st.selectbox("Chọn năm thống kê huyện", result_years, index=result_years.index(st.session_state["result"]["last_y"]), key="district_year_sel")

                if st.button("📊 Tính thống kê Huyện", use_container_width=True):
                    with st.spinner(f"⏳ Đang xử lý cấp Huyện trên toàn Tỉnh..."):
                        df_dist = compute_district_stats(country=st.session_state["params"].country, province=st.session_state["params"].province, layer=st.session_state["params"].layer, year=district_year_sel, month=st.session_state["params"].month)
                        st.session_state["district_data"] = df_dist
                        st.session_state["district_year"] = district_year_sel
                        if not df_dist.empty: st.success(f"✅ Đã tính xong {len(df_dist)} huyện!")
                        else: st.warning("⚠️ Không lấy được dữ liệu.")

# ════════ CỘT 2: BẢN ĐỒ VÀ TƯƠNG TÁC ════════
with col_map:
    if st.session_state["analyzed"] and st.session_state["result"] is not None:
        result = st.session_state["result"]
        params = st.session_state["params"]
        mode   = st.session_state["map_mode"]

        show_dist = st.session_state.get("show_districts_on_map_cb", True) if not params.districts else True
        df_district_for_map = st.session_state.get("district_data")

        if mode == "🎬 Tua lịch sử theo năm":
            m = build_single_map(result, params.layer, st.session_state["display_year"], show_districts=show_dist, country=params.country, province=params.province, df_district=df_district_for_map)
            st.markdown(f"<div class='banner banner-blue'>🎬 {get_layer_name(params.layer).upper()} — NĂM {st.session_state['display_year']}</div>", unsafe_allow_html=True)
        elif mode == "🪞 So sánh kéo thanh (Swipe)":
            m = build_swipe_map(result, params.layer, st.session_state["compare_left_year"], st.session_state["compare_right_year"])
            st.markdown(f"<div class='banner banner-purple'>🪞 {params.layer}: {st.session_state['compare_left_year']} ←→ {st.session_state['compare_right_year']}</div>", unsafe_allow_html=True)
        else:
            m = build_spatial_map(result, params.layer, st.session_state["compare_left_year"], st.session_state["compare_right_year"], st.session_state["spatial_tool"], st.session_state["spatial_radius"], st.session_state["spatial_threshold"])
            st.markdown(f"<div class='banner banner-red'>🔬 {st.session_state['spatial_tool']} ({st.session_state['compare_left_year']} → {st.session_state['compare_right_year']})</div>", unsafe_allow_html=True)

        map_state = st_folium(m, width=None, height=750, returned_objects=["last_clicked","bounds","zoom"], key=f"map_{mode}_{st.session_state.get('display_year')}_{st.session_state.get('compare_left_year')}_{st.session_state.get('compare_right_year')}_{st.session_state.get('spatial_tool')}")

        if map_state and map_state.get("last_clicked"):
            lat, lon = map_state["last_clicked"]["lat"], map_state["last_clicked"]["lng"]
            img_click = result["year_data"][st.session_state.get("display_year") or st.session_state["compare_right_year"]]["image"]
            val = get_pixel_value(img_click, params.layer, lat, lon, scale=30 if params.layer=="LST" else 10)
            st.session_state["map_click_value"] = {"lat": lat, "lon": lon, "value": val}

        if st.session_state["map_click_value"]:
            cv = st.session_state["map_click_value"]
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='kpi-card'><div class='kpi-title'>📍 Vĩ độ</div><div class='kpi-value'>{cv['lat']:.5f}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='kpi-card'><div class='kpi-title'>📍 Kinh độ</div><div class='kpi-value'>{cv['lon']:.5f}</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='kpi-card'><div class='kpi-title'>📈 {params.layer}</div><div class='kpi-value' style='color:#dc2626;'>{fmt(params.layer,cv['value'])}</div></div>", unsafe_allow_html=True)
            
            with st.spinner("⏳ Đang nội suy lịch sử 9 năm cho toạ độ này..."):
                df_hist = get_full_history_at_point(cv["lat"], cv["lon"], params.layer, params.month).dropna()
                if not df_hist.empty:
                    lc = LAYER_COLORS.get(params.layer, "#2563eb")
                    fig_ = px.line(df_hist, x="Năm", y="Chỉ số", markers=True)
                    fig_.update_traces(line_color=lc, line_width=4, marker=dict(size=12, color=lc, line=dict(width=2,color="white")))
                    fig_.update_layout(title=dict(text=f"📈 Lịch sử biến động {params.layer} tại điểm chọn", font_size=18, font_weight="bold"), height=260, margin=dict(l=10,r=10,t=40,b=10), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#000000")
                    fig_.update_xaxes(showgrid=True, gridcolor="#e2e8f0", type="category"); fig_.update_yaxes(showgrid=True, gridcolor="#e2e8f0")
                    st.plotly_chart(fig_, use_container_width=True, config={"displayModeBar":False})

    else:
        empty = folium.Map(location=[16.0,106.0], zoom_start=6, control_scale=True)
        folium.TileLayer("Esri.WorldImagery", name="Ảnh vệ tinh", attr="Esri").add_to(empty)
        st_folium(empty, width=None, height=860, key="empty_map")


# ════════ CỘT 3: BÁO CÁO THỐNG KÊ (BIỂU ĐỒ ĐÃ TỐI ƯU) ════════
with col_report:
    with st.container(height=1180, border=False):
        st.markdown("<div class='danger-title'>📊 KẾT QUẢ PHÂN TÍCH</div>", unsafe_allow_html=True)

        if st.session_state["analyzed"] and st.session_state["result"] is not None:
            params = st.session_state["params"]; result = st.session_state["result"]; stats_last = result["stats_last"]
            main_color = LAYER_COLORS.get(params.layer, "#2563eb"); unit_str = get_unit_str(params.layer); layer_name = get_layer_name(params.layer)
            
            PD = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#000000", font_family="'Be Vietnam Pro', sans-serif", font_size=15)

            first_y=result["first_y"]; last_y=result["last_y"]; l_mean=stats_last.get(f"{params.layer}_mean",0) or 0; l_min=stats_last.get(f"{params.layer}_min", 0) or 0; l_max=stats_last.get(f"{params.layer}_max", 0) or 0
            html = f"<div class='report-card'><strong style='color:#2563eb;font-size:20px;'>📍 {result['roi_names']}</strong><br><br>"
            if first_y == last_y:
                html += f"<strong style='color:#7c3aed;font-size:18px;'>🔹 Tình hình năm {last_y}</strong><br><br>"
                html += f"🎯 <b>{layer_name}</b> trung bình: <b style='color:#dc2626;font-size:22px;'>{fmt(params.layer,l_mean)}</b><br><br>🌡️ Dao động: <b>{fmt(params.layer,l_min)} – {fmt(params.layer,l_max)}</b>" if l_mean != 0 else "<span style='color:#dc2626;'>⚠️ Dữ liệu lỗi hoặc mây 100%.</span>"
            else:
                a_f = extract_area(result["area_first"],3) + extract_area(result["area_first"],4); a_l = extract_area(result["area_last"],3) + extract_area(result["area_last"],4)
                diff = a_l-a_f; pct = (abs(diff)/a_f*100) if a_f>0 else 0
                act, color, icon = ("Mở rộng", "#dc2626", "📈") if diff>0 else ("Thu hẹp", "#059669", "📉")
                if params.layer=="NDVI": color = "#059669" if diff>0 else "#dc2626"
                html += f"<strong style='color:#7c3aed;font-size:18px;'>🔹 Biến động {first_y} → {last_y}</strong><br><br>🗓️ {first_y}: <b style='font-size:18px'>{a_f:,.0f} Ha</b><br>🗓️ {last_y}: <b style='font-size:18px'>{a_l:,.0f} Ha</b><br><br><div style='background:{color}15;border-left:4px solid {color};padding:14px;border-radius:8px;'><span style='color:{color};font-weight:900;font-size:18px;'>{icon} {act} — {abs(diff):,.0f} Ha ({pct:.1f}%)</span></div>"
            st.markdown(html + "</div>", unsafe_allow_html=True)

            k1,k2,k3 = st.columns(3)
            k1.markdown(f"<div class='kpi-card'><div class='kpi-title'>TRUNG BÌNH</div><div class='kpi-value'>{fmt(params.layer,l_mean)}</div></div>", unsafe_allow_html=True)
            k2.markdown(f"<div class='kpi-card'><div class='kpi-title'>THẤP NHẤT</div><div class='kpi-value'>{fmt(params.layer,l_min)}</div></div>", unsafe_allow_html=True)
            k3.markdown(f"<div class='kpi-card'><div class='kpi-title'>CAO NHẤT</div><div class='kpi-value'>{fmt(params.layer,l_max)}</div></div>", unsafe_allow_html=True)

            tab_labels = ["📈 Xu hướng", "📊 Phân bố", "🥧 Cơ cấu"]
            if not params.districts: tab_labels.append("🏘️ Thống kê Tỉnh/Huyện")
            elif len(params.districts) >= 2: tab_labels.append("⚖️ So sánh Huyện")
            
            tabs = st.tabs(tab_labels)
            
            with tabs[0]: 
                if result["trend_data"]:
                    df_t = pd.DataFrame(result["trend_data"])
                    fig1 = px.area(df_t, x="Năm", y="Trị số", markers=True, line_shape="spline")
                    fig1.update_traces(line_color=main_color, fillcolor=hex_to_rgba(main_color, 0.15), marker=dict(size=12, color=main_color, line=dict(width=3,color="white")))
                    fig1.update_layout(height=260, margin=dict(l=10,r=10,t=20,b=10), xaxis_type="category", title=dict(text="Biểu đồ Khuynh hướng", font_size=16), **PD)
                    fig1.update_xaxes(showgrid=True, gridcolor="#e2e8f0"); fig1.update_yaxes(showgrid=True, gridcolor="#e2e8f0")
                    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar":False})
                    
                    if len(df_t) > 1:
                        df_d = df_t.copy(); df_d["Delta"] = df_d["Trị số"].diff(); df_d = df_d.dropna(); df_d["Màu"] = df_d["Delta"].apply(lambda x: "Tăng" if x>=0 else "Giảm")
                        fig_d = px.bar(df_d, x="Năm", y="Delta", color="Màu", text=df_d["Delta"].apply(lambda x: f"{x:+.3f}"), color_discrete_map={"Tăng":"#059669","Giảm":"#dc2626"})
                        fig_d.update_traces(textfont_size=14, textposition="outside", cliponaxis=False)
                        fig_d.update_layout(height=240, margin=dict(l=10,r=10,t=40,b=10), xaxis_type="category", showlegend=False, title=dict(text="Biến động Delta (So với năm trước)", font_size=16), **PD)
                        st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar":False})
                else: st.warning("Chưa đủ số liệu đa thời gian.")

            with tabs[1]:
                hist = result["hist_last"]
                if hist and "histogram" in hist and hist["histogram"]:
                    counts = hist["histogram"]; buckets = [hist["bucketMin"] + i*hist["bucketWidth"] for i in range(len(counts))]
                    cscale = "Greens" if params.layer=="NDVI" else "Reds" if params.layer=="LST" else "Purples"
                    fig2 = px.bar(x=buckets, y=counts, color=counts, color_continuous_scale=cscale)
                    fig2.update_traces(marker_line_width=0.5, marker_line_color="white")
                    fig2.add_vline(x=l_mean, line_dash="dash", line_color="#d97706", annotation_text="Trị số TB", annotation_font_color="#d97706", annotation_font_size=15)
                    fig2.update_layout(height=320, margin=dict(l=10,r=10,t=30,b=10), coloraxis_showscale=False, title=dict(text="Mật độ phân bổ Pixel", font_size=16), **PD)
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
                else: st.warning("Không đủ dữ liệu phân bố.")

            with tabs[2]: 
                pie_data = [{"Lớp": CONFIG["class_labels"][params.layer][i], "Ha": extract_area(result["area_last"], i+1)} for i in range(4) if extract_area(result["area_last"], i+1) > 0]
                if pie_data:
                    fig3 = go.Figure(go.Pie(labels=[d["Lớp"] for d in pie_data], values=[d["Ha"] for d in pie_data], hole=0.5, marker=dict(colors=[CONFIG["vis"][params.layer]["palette"][i] for i in range(4)], line=dict(color="#ffffff",width=3))))
                    fig3.update_traces(textposition='inside', textinfo='percent+label', insidetextfont=dict(color='white', size=14, weight='bold'))
                    fig3.update_layout(height=320, margin=dict(l=10,r=10,t=30,b=10), showlegend=False, title=dict(text="Tỷ trọng diện tích", font_size=16), **PD)
                    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})
                else: st.warning("Không đủ dữ liệu cơ cấu.")

            if len(tabs) > 3: 
                with tabs[3]:
                    if not params.districts: 
                        df_dist = st.session_state.get("district_data")
                        if df_dist is None or df_dist.empty:
                            st.markdown("<div class='report-card' style='text-align:center;padding:30px;'><div style='font-size:50px;'>🏘️</div><div style='font-size:18px;color:#64748b;'>Nhấn <b style='color:#2563eb;'>📊 Tính thống kê Huyện</b> ở cột trái.</div></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='banner banner-teal'>🏘️ THỐNG KÊ {len(df_dist)} HUYỆN</div>", unsafe_allow_html=True)
                            fig_dist = px.bar(df_dist.sort_values("Trung bình", ascending=True), y="Huyện", x="Trung bình", orientation='h', color="Trung bình", text=df_dist.sort_values("Trung bình", ascending=True)["Trung bình"].apply(lambda v: f"{v:.3f}"), color_continuous_scale="RdYlGn" if params.layer=="NDVI" else "YlOrRd")
                            fig_dist.update_traces(textfont_size=14, textposition="outside", cliponaxis=False)
                            fig_dist.update_layout(height=max(350, len(df_dist)*45), margin=dict(l=10,r=30,t=10,b=10), coloraxis_showscale=False, yaxis=dict(type='category', title=""), xaxis=dict(title=""), **PD)
                            st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar":False})
                            
                            df_display = df_dist[["Huyện","Trung bình","Cao nhất","Ha vượt ngưỡng"]].copy()
                            for c in ["Trung bình","Cao nhất"]: df_display[c] = df_display[c].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "—")
                            st.dataframe(df_display, use_container_width=True, height=280, hide_index=True)
                            st.download_button("📥 TẢI BẢNG HUYỆN (CSV)", data=df_dist.to_csv(index=False, encoding="utf-8-sig"), file_name=f"ThongKe_{params.province}_{result['last_y']}.csv", mime="text/csv", use_container_width=True)
                    
                    elif len(params.districts) >= 2: 
                        if result["bar_data"]:
                            df_bar = pd.DataFrame(result["bar_data"])
                            colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b"]
                            fig5 = px.bar(df_bar, x="Khu vực", y="Trị số", color="Khu vực", text=df_bar["Trị số"].apply(lambda v: fmt(params.layer,v)), color_discrete_sequence=colors)
                            fig5.update_traces(textfont_size=18, textposition="outside", cliponaxis=False)
                            fig5.update_layout(height=350, margin=dict(l=10,r=10,t=40,b=10), showlegend=False, title=dict(text="So sánh cán cân", font_size=16), **PD)
                            st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})

        else:
            st.markdown("<div class='report-card' style='text-align:center;padding:40px 20px;'><div style='font-size:60px;'>🛰️</div><div style='font-size:18px;color:#64748b;margin-top:14px;'>Cấu hình cột bên trái và nhấn<br><b style='color:#2563eb;'>🚀 XUẤT BẢN ĐỒ & BÁO CÁO</b></div></div>", unsafe_allow_html=True)

if (st.session_state["analyzed"] and st.session_state["result"] and st.session_state["map_mode"] == "🎬 Tua lịch sử theo năm" and st.session_state.get("play_animation", False)):
    time.sleep(max(0.15, 1.2 - st.session_state.get("play_speed", 1.0)*0.4))
    st.session_state["timeline_index"] = (st.session_state["timeline_index"] + 1) % len(st.session_state["result"]["years"])
    st.session_state["display_year"] = st.session_state["result"]["years"][st.session_state["timeline_index"]]
    st.rerun()
