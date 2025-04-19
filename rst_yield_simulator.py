import streamlit as st
import requests
import numpy as np
import pandas as pd
import plotly.express as px
import time

# Streamlit Configurations
st.set_page_config(page_title="RST 质押收益模拟器", layout="centered")

# === Preferences ===
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'zh'
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'

lang = st.session_state['lang']
theme = st.session_state['theme']

# === Language and Theme Toggle ===
col_lang, col_theme = st.columns([1, 1])
with col_lang:
    if st.button("Switch to English" if lang == 'zh' else "切换为中文"):
        st.session_state['lang'] = 'en' if lang == 'zh' else 'zh'
        st.rerun()
with col_theme:
    if st.button("🌙 夜间模式" if theme == 'light' else "☀️ 日间模式"):
        st.session_state['theme'] = 'dark' if theme == 'light' else 'light'
        st.rerun()

# === Style based on theme ===
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {'#ffffff' if theme == 'light' else '#0e1117'};
        color: {'#000000' if theme == 'light' else '#f0f0f0'};
    }}
    </style>
""", unsafe_allow_html=True)

# === Translation Helper ===
def T(zh, en):
    return zh if lang == 'zh' else en

st.title(T("📊 RST 质押收益模拟器", "📊 RST Yield Simulator"))

# === Constants ===
RST_PRICE = 50
FIXED_APY = 8.01 / 100
TOKEN_DECIMALS = 10 ** 18
TOTAL_RST = 6386

# === Config ===
API_KEY = 'XPM3YSMFXYPZRWJMHWNKD2XNU5699U3MTY'
TOKEN_CONTRACT = '0xDbf9F254C365ABe4294884d1249c7a2388f70911'
INVENTORY_ADDRESS = '0x3B51273c79B68E7cc09bc69605A7e7C650A94943'
STAKE_ADDRESS = '0x1E604c5d206c98B5dbC5b41e37b56451acD26578'

# === Helper Functions ===
@st.cache_data(ttl=60)  # Cache data for 60 seconds
def get_rst_balance(address):
    url = "https://api.basescan.org/api"
    params = {
        'module': 'account', 'action': 'tokenbalance',
        'contractaddress': TOKEN_CONTRACT, 'address': address,
        'tag': 'latest', 'apikey': API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        balance = int(result['result']) / TOKEN_DECIMALS
        return round(balance, 4)
    except Exception as e:
        st.warning(f"❌ {T('获取余额失败', 'Failed to fetch balance')}: {e}")
        return None

# === Fetch Data Section ===
st.subheader(T("📡 实时获取库存和质押数量", "📡 Fetch Real-Time Inventory & Stake"))

cooldown = 5
now = time.time()

if 'last_fetch' not in st.session_state:
    st.session_state['last_fetch'] = 0

if st.button(T("🔄 获取实时数据", "🔄 Get Real-Time Data")):
    if now - st.session_state['last_fetch'] >= cooldown:
        inventory = get_rst_balance(INVENTORY_ADDRESS)
        stake = get_rst_balance(STAKE_ADDRESS)
        st.session_state['inventory'] = inventory
        st.session_state['stake'] = stake
        st.session_state['last_fetch'] = now

remaining = int(cooldown - (now - st.session_state['last_fetch']))
if remaining > 0:
    st.info(f"⏳ {T('距离下次可刷新还有', 'Next refresh in')} {remaining} {T('秒', 's')}")

# === Inputs ===
col1, col2 = st.columns(2)
with col1:
    inventory = st.number_input(T("📦 库存 RST 数量", "📦 RST Inventory"), value=st.session_state.get('inventory', 5321.54), step=1.0)
    stake_max = max(int(TOTAL_RST - inventory), 50)
with col2:
    staked_now = st.number_input(T("📥 总质押 RST 数量", "📥 Total Staked RST"), value=int(st.session_state.get('stake', 60)), step=1)

stake_range = st.slider(
    T("📊 曲线模拟质押范围（横轴）", "📊 Simulation Range (X Axis)"),
    min_value=1, max_value=stake_max,
    value=(20, min(stake_max, 150)), step=5
)

# === Calculation ===
stake_values = np.linspace(stake_range[0], stake_range[1], num=100)
daily_pool = inventory * RST_PRICE * FIXED_APY / 365

curve_daily = daily_pool / stake_values
curve_apy = (curve_daily / RST_PRICE) * 365 * 100

safe_staked_now = max(staked_now, 1e-6)
dot_daily = daily_pool / safe_staked_now
dot_apy = (dot_daily / RST_PRICE) * 365 * 100

view_option = st.radio(T("📈 图表内容显示", "📈 Chart Mode"), [
    T("单RST每日收益（USDC）", "Daily Reward per RST (USDC)"),
    T("质押年化收益率（%）", "Annual Yield (%)")
])

# === Plot ===
df = pd.DataFrame({
    T("质押总量（RST）", "Total Staked RST"): stake_values,
    T("每日收益（USDC）", "Daily Reward (USDC)"): curve_daily,
    T("年化收益率（%）", "Annualized Yield (%)"): curve_apy
})

if view_option.startswith("单") or view_option.startswith("Daily"):
    fig = px.line(df, x=T("质押总量（RST）", "Total Staked RST"), y=T("每日收益（USDC）", "Daily Reward (USDC)"),
                  title=T("RST 收益模拟曲线", "RST Yield Curve"))
else:
    fig = px.line(df, x=T("质押总量（RST）", "Total Staked RST"), y=T("年化收益率（%）", "Annualized Yield (%)"),
                  title=T("RST 收益模拟曲线", "RST Yield Curve"))

st.plotly_chart(fig)

st.markdown(f"**📌 {T('每日总奖池', 'Total Daily Pool')}:** {daily_pool:.4f} USDC")
st.markdown(f"**📌 {T('当前质押', 'Current Staked')}:** {staked_now:.0f} RST")
st.markdown(f"**📌 {T('当前单RST每日收益', 'Daily per RST')}:** {dot_daily:.4f} USDC")
st.markdown(f"**📌 {T('当前年化收益率', 'Current APY')}:** {dot_apy:.2f}%")
