# config.py
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

# =====================================================
# APP
# =====================================================

APP_TITLE = "Creatroka"

APP_SUBTITLE = (
    "Sistem Prediksi Permintaan Buku & Optimasi Stok"
)

APP_ICON = "assets/logo.svg"

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "creatroka-secret-key"
)

# =====================================================
# LOGIN
# =====================================================

CREDENTIALS = {
    "username": os.getenv(
        "APP_USERNAME",
        "creatroka"
    ),

    "password": os.getenv(
        "APP_PASSWORD",
        "admin123"
    ),
}

# =====================================================
# PATH
# =====================================================

DATABASE_PATH = "database/creatroka.db"

MODEL_DIR = "model/"

ASSETS_DIR = "static/assets/"

# =====================================================
# STOK
# =====================================================

DEFAULT_LEAD_TIME = 7

DEFAULT_SERVICE_LEVEL = 95

STOK_KRITIS_THRESHOLD = 5

STOK_MENIPIS_THRESHOLD = 15

# =====================================================
# XGBOOST
# =====================================================

XGBOOST_PARAMS = {

    "n_estimators": 200,

    "learning_rate": 0.1,

    "max_depth": 6,

    "subsample": 0.8,

    "colsample_bytree": 0.8,

    "random_state": 42,

    "early_stopping_rounds": 20,
}