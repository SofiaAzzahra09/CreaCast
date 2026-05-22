#main.py
from flask import Flask, render_template, redirect, url_for, session

from config import APP_TITLE

from app.login import login

from services.database_service import DatabaseService
from services.report_service import ReportService
from services.feature_engineering import FeatureEngineer
from services.xgboost_service import XGBoostService
from services.model_registry import ModelRegistry
from services.pipeline_service import PipelineService

from route.dashboard import dashboard_bp
from route.data_buku import data_buku_bp
from route.data_preparation import data_preparation_bp
from route.prediksi import prediksi_bp
from route.optimasi_stok import optimasi_stok_bp
from route.model_management import model_management_bp
from route.profile import profile_bp


app = Flask(__name__)
app.secret_key = "secret-key"

# =====================================================
# SERVICES
# =====================================================

db = DatabaseService()
rep = ReportService(db)
fe = FeatureEngineer()
xgb = XGBoostService("model/model_xgb1.pkl")
registry = ModelRegistry(db)
pipeline = PipelineService()

# =====================================================
# LOGIN GUARD
# =====================================================

def login_required():
    return session.get("logged_in")


# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def home():

    if not login_required():
        return redirect(url_for("login"))

    return redirect(url_for("dashboard.dashboard"))


# =====================================================
# LOGIN
# =====================================================

app.add_url_rule(
    "/login",
    view_func=login,
    methods=["GET", "POST"]
)

# =====================================================
# DASHBOARD
# =====================================================
app.register_blueprint(dashboard_bp)

# =====================================================
# DATA BUKU
# =====================================================
app.register_blueprint(data_buku_bp)

# =====================================================
# DATA PREPARATION
# =====================================================
app.register_blueprint(data_preparation_bp)

# =====================================================
# PREDIKSI
# =====================================================
app.register_blueprint(prediksi_bp)

# =====================================================
# OPTIMASI STOK
# =====================================================
app.register_blueprint(optimasi_stok_bp)

# =====================================================
# MODEL MANAGEMENT
# =====================================================
app.register_blueprint(model_management_bp)

# =====================================================
# PROFILE
# =====================================================
app.register_blueprint(profile_bp)

# =====================================================
# LOGOUT
# =====================================================
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)