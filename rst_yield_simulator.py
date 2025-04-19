import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time
import matplotlib
import os

# 加载本地 SimHei 字体用于中文显示
font_path = os.path.join(os.path.dirname(__file__), "SimHei.ttf")
matplotlib.font_manager.fontManager.addfont(font_path)
plt.rcParams["font.family"] = "SimHei"
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="RST 质押收益模拟器", layout="centered")

# === 用户偏好 ===
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'zh'
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'

lang = st.session_state['lang']
theme = st.session_state['theme']

# === 中英文切换 + 主题切换按钮 ===
col_lang, col_theme = st.columns([1, 1])
with col_lang:
    if st.button("Switch to English" if lang == 'zh' else "切换为中文"):
        st.session_state['lang'] = 'en' if lang == 'zh' else 'zh'
        st.rerun()
with col_theme:
    if st.button("🌙 夜间模式" if theme == 'light' else "☀️ 日间模式"):
        st.session_state['theme'] = 'dark' if theme == 'light' else 'light'
        st.rerun()

# === 页面样式自定义 ===
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {'#ffffff' if theme == 'light' else '#0e1117'};
        color: {'#000000' if theme == 'light' else '#f0f0f0'};
    }}
    .stButton>button {{
        background-color: {'#f0f0f0' if theme == 'light' else '#2e2e2e'};
        color: {'#000000' if theme == 'light' else '#ffffff'};
    }}
    .stNumberInput input, .stSlider {{
        background-color: {'#ffffff' if theme == 'light' else '#1c1c1c'};
        color: {'#000000' if theme == 'light' else '#f0f0f0'};
    }}
    </style>
""", unsafe_allow_html=True)

# === 翻译函数 ===
def T(zh, en):
    return zh if lang == 'zh' else en

st.title(T("📊 RST 质押收益模拟器", "📊 RST Yield Simulator"))

sst.markdown(T("""**📢 邀请说明：** [点击此处注册并支持我](https://realtyx.co/invite/3Jv6Nt)（老用户手动填写邀请码：3Jv6Nt）

为促进 RST 销量，我愿意将顶级代理人佣金（5%）全部返还给受邀人。  
请通过 Telegram 或微信联系我登记邮箱和钱包地址：  
TG：[@sanqing_web3](https://t.me/sanqing_web3) / 微信号：`sanqing_web3`""",
"""**📢 Invitation Info:** [Click here to register and support me](https://realtyx.co/invite/3Jv6Nt) (If you're an existing user, please manually enter the invitation code: **3Jv6Nt**)

To boost RST adoption, I’m happy to **refund the full 5% top-level agent commission** to everyone who signs up through my link.  
Please contact me via **Telegram or WeChat** to register your email and wallet address:  
TG: [@sanqing_web3](https://t.me/sanqing_web3) / WeChat ID: `sanqing_web3`"""))


# === 常量定义 ===
RST_PRICE = 50
FIXED_APY = 8.01 / 100
TOKEN_DECIMALS = 10 ** 18
TOTAL_RST = 6386

# === 读取实时数据 ===
API_KEY = 'XPM3YSMFXYPZRWJMHWNKD2XNU5699U3MTY'
TOKEN_CONTRACT = '0xDbf9F254C365ABe4294884d1249c7a2388f70911'
INVENTORY_ADDRESS = '0x3B51273c79B68E7cc09bc69605A7e7C650A94943'
STAKE_ADDRESS = '0x1E604c5d206c98B5dbC5b41e37b56451acD26578'

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

# === 实时获取按钮 ===
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
    st.toast(f"⏳ {T('距离下次可刷新还有', 'Next refresh in')} {remaining} {T('秒', 's')}", icon="⏳")
    time.sleep(1)
    st.rerun()

# === 输入区块 ===
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

stake_values = np.arange(stake_range[0], stake_range[1] + 1, 1)
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

# === 绘图 ===
fig, ax = plt.subplots()
if view_option.startswith("单") or view_option.startswith("Daily"):
    ax.plot(stake_values, curve_daily, label=T("模拟每日收益", "Simulated Daily"), color='skyblue')
    ax.scatter([staked_now], [dot_daily], color='blue', label=T('当前质押', 'Current Stake'))
    ax.axvline(x=staked_now, color='gray', linestyle='dashed')
    ax.axhline(y=dot_daily, color='gray', linestyle='dashed')
    ax.text(staked_now, ax.get_ylim()[0], f"{staked_now:.0f} RST", ha='center', va='bottom', fontsize=9)
    ax.text(ax.get_xlim()[0], dot_daily, f"{dot_daily:.4f} USDC", va='center', ha='left', fontsize=9)
    ax.set_ylabel(T("每日收益（USDC）", "Daily Reward (USDC)"))
else:
    ax.plot(stake_values, curve_apy, label=T("模拟年化收益率", "Simulated APY"), color='orange')
    ax.scatter([staked_now], [dot_apy], color='red', label=T('当前质押', 'Current Stake'))
    ax.axvline(x=staked_now, color='gray', linestyle='dashed')
    ax.axhline(y=dot_apy, color='gray', linestyle='dashed')
    ax.text(staked_now, ax.get_ylim()[0], f"{staked_now:.0f} RST", ha='center', va='bottom', fontsize=9)
    ax.text(ax.get_xlim()[0], dot_apy, f"{dot_apy:.2f}%", va='center', ha='left', fontsize=9)
    ax.set_ylabel(T("年化收益率（%）", "Annualized Yield (%)"))

ax.set_xlabel(T("质押总量（RST）", "Total Staked RST"))
ax.set_title(T("RST 收益模拟曲线", "RST Yield Curve"))
ax.legend()
ax.grid(True)
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
st.pyplot(fig)

# === 当前收益展示 ===
st.markdown(f"**📌 {T('每日总奖池', 'Total Daily Pool')}:** {daily_pool:.4f} USDC")
st.markdown(f"**📌 {T('当前质押', 'Current Staked')}:** {staked_now:.0f} RST")
st.markdown(f"**📌 {T('当前单RST每日收益', 'Daily per RST')}:** {dot_daily:.4f} USDC")
st.markdown(f"**📌 {T('当前年化收益率', 'Current APY')}:** {dot_apy:.2f}%")

# === 合约信息 ===
st.subheader(T("📄 合约与地址说明", "📄 Contract Info"))
st.markdown(f"""
- **RST {T('合约地址', 'Token Contract')}**：`{TOKEN_CONTRACT}`
- **{T('库存地址', 'Inventory Address')}**：`{INVENTORY_ADDRESS}`
- **{T('质押地址', 'Staking Address')}**：`{STAKE_ADDRESS}`
- ⚠️ {T('实时数据获取受限于 Basescan 免费 API，如遇失败请重试。', 'Real-time data via free Basescan API, retry if fails.')}
""")
