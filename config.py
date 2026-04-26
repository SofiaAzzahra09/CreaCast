# config.py
# CREDENTIALS = {
#     "username": "creatroka",
#     "password": "admin123"  # bisa disimpan di .env pakai python-dotenv
# }

# config.py
import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

CREDENTIALS = {
    "username": os.getenv("APP_USERNAME", "creatroka"),
    "password": os.getenv("APP_PASSWORD", "admin123"),
}

DATABASE_PATH = "database/creatroka.db"
MODEL_DIR     = "model/"
ASSETS_DIR    = "assets/"

APP_TITLE    = "Creatroka"
APP_SUBTITLE = "Sistem Prediksi Permintaan Buku & Optimasi Stok"
APP_ICON     = "assets/logo.svg"

# Parameter default optimasi stok
DEFAULT_LEAD_TIME     = 7   # hari
DEFAULT_SERVICE_LEVEL = 95  # persen
STOK_KRITIS_THRESHOLD = 5
STOK_MENIPIS_THRESHOLD = 15

# Parameter default XGBoost
XGBOOST_PARAMS = {
    "n_estimators":     200,
    "learning_rate":    0.1,
    "max_depth":        6,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "random_state":     42,
    "early_stopping_rounds": 20,
}