# # main.py
# import streamlit as st
# from config import APP_TITLE, APP_ICON, APP_SUBTITLE, XGBOOST_PARAMS

# from services.database_service    import DatabaseService
# # from services.xgboost_service     import XGBoostService
# # from services.feature_engineering import FeatureEngineer
# # from services.stok_optimizer     import StockOptimizer
# # from services.model_registry      import ModelRegistry
# from services.report_service      import ReportService

# from app.login              import LoginPage
# from app.dashboard          import DashboardPage
# from app.data_buku          import DataBukuPage
# # from app.data_penjualan     import DataPenjualanPage
# # from app.prediksi           import PrediksiPage
# # from app.model_optimasi      import OptimasisStokPage
# # from app.model_managemen   import ModelManagementPage
# from app.laporan            import LaporanPage


# # ── Konfigurasi halaman ───────────────────────────────────────────────
# st.set_page_config(
#     page_title=APP_TITLE,
#     page_icon=APP_ICON,
#     layout="wide",
#     initial_sidebar_state="expanded",
# )


# # ── Inisialisasi services (singleton via session_state) ───────────────
# @st.cache_resource
# def init_services():
#     """
#     Inisialisasi semua service satu kali.
#     @cache_resource memastikan tidak diinisialisasi ulang tiap rerun.
#     """
#     db      = DatabaseService()
#     # fe      = FeatureEngineer()
#     # xgb     = XGBoostService(fe, db, XGBOOST_PARAMS)
#     # reg     = ModelRegistry(db)
#     # opt_cls = StockOptimizer
#     rep     = ReportService(db)
#     # retrn db, xgb, reg, opt_cls, rep
#     return db, rep

# # db, xgb, reg, opt_cls, rep = init_services()
# db, rep = init_services()   # sementara fokus ke database dan laporan dulu



# # ── Guard: cek login ──────────────────────────────────────────────────
# if not st.session_state.get("logged_in"):
#     LoginPage().render()
#     st.stop()   # ← kunci keamanan: halaman lain tidak ikut render


# # ── Sidebar navigasi ──────────────────────────────────────────────────
# with st.sidebar:
#     st.image("assets/logo.svg", width=40)
#     st.markdown(f"### {APP_TITLE}")
#     st.caption(APP_SUBTITLE)
#     st.divider()

#     MENU = {
#         "Dashboard":          "📊",
#         "Data buku":          "📚",
#         "Data penjualan":     "🛒",
#         "Prediksi":           "🤖",
#         "Optimasi stok":      "📦",
#         "Model management":   "⚙️",
#         "Laporan & ekspor":   "📄",
#     }

#     halaman = st.selectbox(
#         "Navigasi",
#         list(MENU.keys()),
#         format_func=lambda x: f"{MENU[x]}  {x}",
#         label_visibility="collapsed",
#     )

#     st.divider()
#     st.caption(f"Login sebagai: **{st.session_state.get('username','—')}**")
#     if st.button("Keluar", use_container_width=True):
#         st.session_state.clear()
#         st.rerun()


# # ── Routing ke halaman ────────────────────────────────────────────────
# match halaman:
#     case "Dashboard":
#         DashboardPage(db).render()

#     case "Data buku":
#         DataBukuPage(db).render()

#     # case "Data penjualan":
#     #     DataPenjualanPage(db).render()

#     # case "Prediksi":
#     #     PrediksiPage(xgb, db).render()

#     # case "Optimasi stok":
#     #     OptimasisStokPage(db, opt_cls).render()

#     # case "Model management":
#     #     ModelManagementPage(reg, xgb).render()

#     # case "Laporan & ekspor":
#     #     LaporanPage(rep, db).render()

# main.py
import streamlit as st
from config import APP_TITLE, APP_ICON, APP_SUBTITLE

from services.database_service import DatabaseService
from services.feature_engineering import FeatureEngineer
from services.xgboost_service import XGBoostService
from app.prediksi import PrediksiPage
from services.model_registry import ModelRegistry
from services.stok_optimizer import StockOptimizer
from app.model_optimasi import OptimasisStokPage
from app.model_managemen import ModelManagementPage
from services.report_service import ReportService

from app.login import LoginPage
from app.dashboard import DashboardPage
from app.data_buku import DataBukuPage
from app.laporan import LaporanPage


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================
# LOAD CSS
# =====================================================
def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css("css/style.css")


# =====================================================
# SERVICES
# =====================================================
@st.cache_resource
def init_services():
    db = DatabaseService()
    rep = ReportService(db)
    fe = FeatureEngineer()
    xgb = XGBoostService(fe)

    registry = ModelRegistry(db)

    return db, rep, xgb, registry

db, rep, xgb, registry = init_services()


# =====================================================
# LOGIN GUARD
# =====================================================
if not st.session_state.get("logged_in"):
    LoginPage().render()
    st.stop()


# =====================================================
# DEFAULT PAGE
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# =====================================================
# MENU BUTTON
# =====================================================
def menu_button(label, icon):
    current = st.session_state.page

    if current == label:
        st.markdown(
            f"""
            <div class="active-menu">
                <span>{icon}</span>
                <span>{label}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        if st.button(f"{icon}  {label}", key=label, use_container_width=True):
            st.session_state.page = label
            st.rerun()


# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    # LOGO
    st.image("assets/logo.svg", width=70)

    st.markdown(
        f"""
        <div class="sidebar-title">{APP_TITLE}</div>
        <div class="sidebar-subtitle">{APP_SUBTITLE}</div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    menu_button("Dashboard", "📊")
    menu_button("Data buku", "📚")
    menu_button("Data penjualan", "🛒")
    menu_button("Prediksi", "🤖")
    menu_button("Optimasi stok", "📦")
    menu_button("Model management", "⚙️")
    menu_button("Laporan & ekspor", "📄")

    st.divider()

    username = st.session_state.get("username", "User")

    st.markdown(
        f"""
        <div class="user-box">
            👤 Login sebagai <b>{username}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    if st.button("🚪 Keluar", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# =====================================================
# ROUTING
# =====================================================
halaman = st.session_state.page

match halaman:

    case "Dashboard":
        DashboardPage(db).render()

    case "Data buku":
        DataBukuPage(db).render()

    case "Prediksi":
        PrediksiPage(xgb, db).render()

    case "Optimasi stok":
        OptimasisStokPage(db, StockOptimizer).render()

    case "Model management":
        ModelManagementPage(registry, xgb, db).render()

    case "Laporan & ekspor":
        LaporanPage(rep, db).render()

    case _:
        st.title(halaman)
        st.info("Halaman sedang dikembangkan.")