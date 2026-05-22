# from flask import (
#     Blueprint,
#     render_template,
#     request,
#     redirect,
#     url_for,
#     flash
# )
# import json

# from services.database_service import DatabaseService
# from services.model_registry import ModelRegistry
# from services.xgboost_service import XGBoostService

# model_management_bp = Blueprint(
#     "model_management",
#     __name__,
#     url_prefix="/model-management"
# )

# # =====================================================
# # SERVICES
# # =====================================================

# db = DatabaseService()

# xgb = XGBoostService(
#     "model/model_xgb1.pkl"
# )

# registry = ModelRegistry(db)

# # =====================================================
# # INDEX
# # =====================================================

# @model_management_bp.route("/")
# def index():
#     active_tab = request.args.get(
#         "tab",
#         "models"
#     )

#     df = registry.get_all()
#     data = df.to_dict(
#         orient="records"
#     )

#     model_aktif = []
#     if not df.empty:
#         model_aktif = df[
#             df["status"].str.lower() == "aktif"
#         ]["versi"].tolist()

#     return render_template(
#         "model_management/index.html",
#         data=data,
#         active_tab=active_tab,
#         model_aktif=model_aktif
#     )

# # =====================================================
# # AKTIFKAN MODEL
# # =====================================================

# @model_management_bp.route(
#     "/activate/<versi>",
#     methods=["POST"]
# )
# def activate_model(versi):
#     try:
#         registry.activate(versi)
#         flash(
#             f"Model {versi} berhasil diaktifkan",
#             "success"
#         )
#     except Exception as e:
#         flash(str(e), "danger")

#     return redirect(
#         url_for(
#             "model_management.index",
#             tab="models"
#         )
#     )

# # =====================================================
# # NONAKTIFKAN MODEL
# # =====================================================

# @model_management_bp.route(
#     "/deactivate/<versi>",
#     methods=["POST"]
# )
# def deactivate_model(versi):
#     try:
#         db.execute("UPDATE model_registry SET status = 'nonaktif' WHERE versi = ?", (versi,))
#         flash(
#             f"Model {versi} berhasil dinonaktifkan",
#             "success"
#         )
#     except Exception as e:
#         flash(str(e), "danger")

#     return redirect(
#         url_for(
#             "model_management.index",
#             tab="models"
#         )
#     )

# # =====================================================
# # HAPUS MODEL (DENGAN PROTEKSI MODEL AKTIF)
# # =====================================================

# @model_management_bp.route(
#     "/delete/<versi>",
#     methods=["POST"]
# )
# def delete_model(versi):
#     try:
#         # 1. Cek status model langsung ke DB sebelum memanggil service registry
#         model_data = db.fetchone("SELECT status FROM model_registry WHERE versi = ?", (versi,))
        
#         if model_data and model_data["status"].lower() == "aktif":
#             flash(f"Gagal menghapus! Model {versi} sedang aktif. Nonaktifkan terlebih dahulu.", "danger")
#             return redirect(url_for("model_management.index", tab="models"))

#         # 2. Jika tidak aktif, jalankan fungsi delete dari registry service
#         registry.delete(versi)
#         flash(
#             f"Model {versi} berhasil dihapus",
#             "success"
#         )

#     except Exception as e:
#         flash(f"Gagal menghapus model: {str(e)}", "danger")

#     return redirect(
#         url_for(
#             "model_management.index",
#             tab="models"
#         )
#     )

# # =====================================================
# # RETRAIN MODEL (DENGAN ENHANCED METADATA & FLOW)
# # =====================================================

# @model_management_bp.route(
#     "/retrain",
#     methods=["POST"]
# )
# def retrain_model():
#     model_ref = request.form.get(
#         "model_ref"
#     )
#     catatan = request.form.get(
#         "catatan",
#         ""
#     )

#     try:
#         df = db.get_weekly_sales()

#         if df.empty:
#             flash(
#                 "Data transaksi mingguan kosong! Jalankan pipeline data preparation terlebih dahulu.",
#                 "warning"
#             )
#             return redirect(
#                 url_for(
#                     "model_management.index",
#                     tab="retrain"
#                 )
#             )

#         # 1. Jalankan proses training XGBoost
#         metrics, params = xgb.train(df)

#         # 2. Tambahkan enriched metadata untuk skripsi kamu ke dalam object metrics/params
#         # Cek apakah dataframe memiliki kolom fitur yang biasa dipakai XGBoost di skripsimu
#         feature_columns = [col for col in df.columns if col not in ["nama_variasi", "created_at"]]
        
#         # Kita injeksikan metadata training ekstra ke dalam params/metrics sebelum di-save oleh registry
#         metrics["features_used"] = json.dumps(feature_columns)
#         metrics["train_test_split_ratio"] = "80:20"  # Sesuaikan dengan config splitting di XGBoostService mu
#         metrics["jumlah_data"] = len(df)

#         # 3. Simpan model via registry
#         catatan_final = catatan if catatan else f"Retrain otomatis berbasis data dari model {model_ref}"
#         versi_baru = registry.save(
#             xgb.model,
#             metrics,
#             params,
#             catatan_final
#         )

#         flash(
#             f"Model baru berhasil dilatih dan disimpan: {versi_baru}",
#             "success"
#         )

#     except Exception as e:
#         flash(
#             f"Gagal memproses retraining XGBoost: {str(e)}",
#             "danger"
#         )

#     return redirect(
#         url_for(
#             "model_management.index",
#             tab="retrain"
#         )
#     )

# route.model_management.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from services.database_service import DatabaseService
from services.model_registry import ModelRegistry
from services.xgboost_service import XGBoostService

model_management_bp = Blueprint(
    "model_management",
    __name__,
    url_prefix="/model-management"
)

# =====================================================
# SERVICES
# =====================================================

db = DatabaseService()

xgb = XGBoostService(
    "model/model_xgb1.pkl"
)

registry = ModelRegistry(db)

# =====================================================
# INDEX
# =====================================================

@model_management_bp.route("/")
def index():

    active_tab = request.args.get(
        "tab",
        "models"
    )

    df = registry.get_all()

    data = df.to_dict(
        orient="records"
    )

    model_aktif = []

    if not df.empty:

        model_aktif = df[
            df["status"].str.lower() == "aktif"
        ]["versi"].tolist()

    return render_template(
        "model_management/index.html",
        data=data,
        active_tab=active_tab,
        model_aktif=model_aktif
    )

# =====================================================
# AKTIFKAN MODEL
# =====================================================

@model_management_bp.route("/activate/<versi>", methods=["POST"])
def activate_model(versi):
    try:
        # 1. Tukar status aktif di DB registry
        registry.activate(versi)

        # 2. PERBAIKAN: Hitung ulang semua prediksi menggunakan model baru yang diaktifkan ini
        from route.prediksi import generate_forecast_pipeline
        sukses, pesan = generate_forecast_pipeline(versi_model=versi, n_weeks=4, hist=26)
        
        if sukses:
            flash(f"Model {versi} berhasil diaktifkan. Halaman Prediksi & Optimasi Stok telah diperbarui!", "success")
        else:
            flash(f"Model aktif diganti ke {versi}, tetapi gagal generate prediksi: {pesan}", "warning")

    except Exception as e:
        flash(str(e), "danger")

    return redirect(url_for("model_management.index", tab="models"))


# =====================================================
# NONAKTIFKAN MODEL
# =====================================================

@model_management_bp.route(
    "/deactivate/<versi>",
    methods=["POST"]
)
def deactivate_model(versi):

    try:
        db.execute("UPDATE model_registry SET status = 'nonaktif' WHERE versi = ?", (versi,))

        flash(
            f"Model {versi} berhasil dinonaktifkan",
            "success"
        )

    except Exception as e:

        flash(str(e), "danger")

    return redirect(
        url_for(
            "model_management.index",
            tab="models"
        )
    )

# =====================================================
# HAPUS MODEL
# =====================================================

@model_management_bp.route(
    "/delete/<versi>",
    methods=["POST"]
)
def delete_model(versi):

    try:

        registry.delete(versi)

        flash(
            f"Model {versi} berhasil dihapus",
            "success"
        )

    except Exception as e:

        flash(str(e), "danger")

    return redirect(
        url_for(
            "model_management.index",
            tab="models"
        )
    )

# =====================================================
# RETRAIN MODEL
# =====================================================

@model_management_bp.route("/retrain", methods=["POST"])
def retrain_model():
    model_ref = request.form.get("model_ref")
    catatan = request.form.get("catatan", "")

    try:
        df = db.get_weekly_sales()

        if df.empty:
            flash("Data transaksi tidak ditemukan", "warning")
            return redirect(url_for("model_management.index", tab="retrain"))

        # 1. Latih ulang model
        metrics, params = xgb.train(df)

        # 2. Simpan model baru ke registry (status bawaannya 'nonaktif')
        versi_baru = registry.save(
            xgb.model,
            metrics,
            params,
            catatan if catatan else f"Retrain dari {model_ref}"
        )

        # 3. PERBAIKAN OPTIONAL: Jika kamu mau model hasil retrain langsung otomatis aktif
        registry.activate(versi_baru)
        from route.prediksi import generate_forecast_pipeline
        generate_forecast_pipeline(versi_model=versi_baru, n_weeks=4, hist=26)

        flash(f"Model baru {versi_baru} berhasil dibuat, diaktifkan, dan prediksi diperbarui!", "success")

    except Exception as e:
        flash(f"Gagal retrain: {str(e)}", "danger")

    return redirect(url_for("model_management.index", tab="retrain"))