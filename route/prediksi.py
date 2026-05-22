# route/prediksi.py
# route/prediksi.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

import pandas as pd
import plotly.graph_objects as go
import plotly

from services.database_service import DatabaseService
from services.xgboost_service import XGBoostService
from services.model_registry import ModelRegistry
from services.pipeline_service import PipelineService

import json


prediksi_bp = Blueprint(
    "prediksi",
    __name__,
    url_prefix="/prediksi"
)

db = DatabaseService()
xgb = XGBoostService("model/model_xgb1.pkl")
registry = ModelRegistry(db)
pipeline = PipelineService()


@prediksi_bp.route("/", methods=["GET", "POST"])
def index():
    metrics = {}
    forecast_data = []
    # chart_json = None
    chart_json = session.get("last_chart")
    metrics = session.get("last_metrics", {})
    forecast_data = session.get("last_forecast", [])
    versi_model = session.get("last_model")
    # versi_model = None

    if request.method == "POST":
        try:
            n_weeks = int(request.form.get("n_weeks", 4))
            hist = int(request.form.get("hist", 26))

            df = db.get_weekly_sales(weeks=hist)

            if df.empty:
                flash("Data mingguan belum tersedia.", "warning")
                return redirect(url_for("prediksi.index"))

            # 1. Melatih Model Baru lewat tombol di halaman prediksi
            metrics_res, params = xgb.train(df)

            # 2. Simpan ke Registry (otomatis jadi v1, v2, dst)
            versi = registry.save(
                xgb.model,
                metrics_res,
                params,
                f"Auto forecast {n_weeks} minggu"
            )

            # 3. Aktifkan model baru tersebut
            registry.activate(versi)

            # 4. PANGGIL PIPELINE FORECAST UTAMANYA
            sukses, hasil_forecast = generate_forecast_pipeline(versi_model=versi, n_weeks=n_weeks, hist=hist)
            
            if not sukses:
                flash(hasil_forecast, "danger") # hasil_forecast berisi pesan error jika gagal
                return redirect(url_for("prediksi.index"))

            # 5. Siapkan Chart Visualisasi
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=metrics_res["y_test"], name="Aktual"))
            fig.add_trace(go.Scatter(y=metrics_res["y_pred"], name="Prediksi"))
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=20, b=0))

            chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            # SIMPAN KE SESSION
            session["last_chart"] = chart_json

            session["last_metrics"] = {
                "mse": round(metrics_res["mse"], 2),
                "rmse": round(metrics_res["rmse"], 2),
                "mae": round(metrics_res["mae"], 2),
                "r2": round(metrics_res["r2"], 3),
            }

            session["last_forecast"] = hasil_forecast
            session["last_model"] = versi

            # metrics = {
            #     "mse": round(metrics_res["mse"], 2),
            #     "rmse": round(metrics_res["rmse"], 2),
            #     "mae": round(metrics_res["mae"], 2),
            #     "r2": round(metrics_res["r2"], 3),
            # }

            # forecast_data = hasil_forecast
            # versi_model = versi

            flash(f"Model baru berhasil dilatih ({versi}) dan prediksi telah diperbarui!", "success")

        except Exception as e:
            flash(f"Error model: {str(e)}", "danger")

    return render_template(
        "prediksi/index.html",
        metrics=metrics,
        forecast_data=forecast_data,
        chart_json=chart_json,
        versi_model=versi_model
    )

def generate_forecast_pipeline(versi_model, n_weeks=4, hist=26):
    """
    Fungsi global untuk menjalankan forecast ke seluruh variasi produk
    menggunakan versi model tertentu dan langsung menyimpannya ke DB.
    """
    import json
    import os
    from services.database_service import DatabaseService
    from services.xgboost_service import XGBoostService
    
    db_service = DatabaseService()
    df = db_service.get_weekly_sales(weeks=hist)
    
    if df.empty:
        return False, "Data mingguan (weekly sales) kosong."
        
    # 1. Load Inverse Variasi Map untuk translate angka encoded -> teks nama buku
    map_path = "data/variasi_map.json"
    if not os.path.exists(map_path):
        return False, f"File mapping {map_path} tidak ditemukan."
        
    with open(map_path, "r", encoding="utf-8") as f:
        variasi_map = json.load(f)
    
    # Balik map: {0: "guru", 1: "koki", ...}
    inverse_variasi_map = {v: k for k, v in variasi_map.items()}
        
    row_model = db_service.fetchone(
        "SELECT file_path FROM model_registry WHERE versi = ?", (versi_model,)
    )
    if not row_model:
        return False, f"File untuk model versi {versi_model} tidak ditemukan."
        
    xgb_service = XGBoostService(row_model['file_path'])
    
    if hasattr(xgb_service, 'load_model'):
        xgb_service.load_model() 
    else:
        import pickle
        with open(row_model['file_path'], 'rb') as f:
            xgb_service.model = pickle.load(f)

    if xgb_service.model is None:
        return False, f"Gagal memuat file binary model untuk versi {versi_model}."
        
    all_forecasts = []
    
    # Looping forecast per variasi produk
    for variasi in df["variasi_encoded"].unique():
        # FILTER KEAMANAN: Skip encoding 229 (NaN) karena bukan produk nyata
        if int(variasi) == 229:
            continue

        df_var = df[df["variasi_encoded"] == variasi].copy()

        if len(df_var) < 4:
            continue

        # Jalankan forecast multi-step (fitur waktu sudah dinamis di perbaikan sebelumnya)
        forecast = xgb_service.forecast(df_var, n_weeks)
        nama_variasi = df_var.iloc[0]["nama_variasi"]
        last_week = df_var.iloc[-1]["minggu_ke"]
        last_year = df_var.iloc[-1]["tahun"]

        nama_variasi_clean = str(nama_variasi).strip().title()
        all_forecasts.append({
            "nama_variasi": nama_variasi,
            "forecast": float(forecast[0])
        })

        # ====================================================================
        # SINKRONISASI ID: Terjemahkan variasi_encoded ke id asli tabel buku
        # ====================================================================
        nama_buku_asli = inverse_variasi_map.get(int(variasi), None)
        id_buku_asli = None
        
        if nama_buku_asli:
            id_buku_asli = db_service.get_buku_id_by_judul(nama_buku_asli)
        
        # Fallback Khusus: Jika buku belum diinput ke master buku, 
        # jangan simpan prediksinya dulu daripada merusak integritas Foreign Key DB
        if id_buku_asli is None:
            print(f"Peringatan: Buku '{nama_buku_asli}' (Encoded: {variasi}) belum ada di tabel master 'buku'. Prediksi dilewati.")
            continue

        # Simpan hasil prediksi menggunakan ID asli yang valid dengan Foreign Key
        db_service.save_prediction(
            forecast,
            start_week=last_week + 1,
            start_year=last_year,
            model_versi=versi_model,
            id_buku=id_buku_asli  # <-- SEKARANG SUDAH AMAN
        )
    all_forecasts = sorted(all_forecasts, key=lambda x: x["nama_variasi"])
        
    return True, all_forecasts

def generateforecastpipeline(versi_model, n_weeks=4, hist=26):
    """
    Fungsi global untuk menjalankan forecast ke seluruh variasi produk
    menggunakan versi model tertentu dan langsung menyimpannya ke DB.
    """
    from services.database_service import DatabaseService
    from services.xgboost_service import XGBoostService
    import pickle # <-- Tambahkan ini jika dibutuhkan
    
    db_service = DatabaseService()
    df = db_service.get_weekly_sales(weeks=hist)
    
    if df.empty:
        return False, "Data mingguan (weekly sales) kosong."
        
    # Memuat model spesifik berdasarkan file path di registry
    row_model = db_service.fetchone(
        "SELECT file_path FROM model_registry WHERE versi = ?", (versi_model,)
    )
    if not row_model:
        return False, f"File untuk model versi {versi_model} tidak ditemukan."
        
    # Inisialisasi XGBoostService (Sistem kamu sudah tahu path-nya dari sini)
    xgb_service = XGBoostService(row_model['file_path'])
    
    # ====================================================================
    # PERBAIKAN: Sesuaikan pemanggilan load_model tanpa melempar parameter path
    # ====================================================================
    if hasattr(xgb_service, 'load_model'):
        # Karena fungsi kamu hanya menerima 1 argumen (self), panggil TANPA isi kurung:
        xgb_service.load_model() 
    elif hasattr(xgb_service, 'load'):
        xgb_service.load()
    else:
        # Jika cara di atas masih gagal, bypass langsung menggunakan pickle bawaan Python
        import pickle
        with open(row_model['file_path'], 'rb') as f:
            xgb_service.model = pickle.load(f)
    # ====================================================================

    # Pastikan sekali lagi model tidak None sebelum masuk looping
    if xgb_service.model is None:
        return False, f"Gagal memuat file binary model untuk versi {versi_model}."
        
    all_forecasts = []
    
    # Lakukan looping forecast per variasi produk
    # Lakukan looping forecast per variasi produk
    for variasi in df["variasi_encoded"].unique():
        df_var = df[df["variasi_encoded"] == variasi].copy()

        if len(df_var) < 4:
            continue

        # Jalankan forecast (sekarang sudah menggunakan fungsi baru yang aman)
        forecast = xgb_service.forecast(df_var, n_weeks)
        nama_variasi = df_var.iloc[0]["nama_variasi"]
        last_week = df_var.iloc[-1]["minggu_ke"]
        last_year = df_var.iloc[-1]["tahun"]

        all_forecasts.append({
            "nama_variasi": nama_variasi,
            "forecast": float(forecast[0])
        })

        # ====================================================================
        # CATATAN ID_BUKU: 
        # Jika 'variasi' di sini adalah index encoding (0, 1, 2...), pastikan 
        # tabel 'buku' kamu juga menggunakan index yang sama. Jika tabel 'buku' 
        # menggunakan ID asli SQLite (1, 2, 3...), kamu perlu memetakan 
        # kembali 'variasi' ke ID buku asli sebelum disimpan ke database.
        # ====================================================================
        db_service.save_prediction(
            forecast,
            start_week=last_week + 1,
            start_year=last_year,
            model_versi=versi_model,
            id_buku=int(variasi) 
        )
    # for variasi in df["variasi_encoded"].unique():
    #     df_var = df[df["variasi_encoded"] == variasi].copy()

    #     if len(df_var) < 4:
    #         continue

    #     # Jalankan forecast
    #     forecast = xgb_service.forecast(df_var, n_weeks)
    #     nama_variasi = df_var.iloc[0]["nama_variasi"]
    #     last_week = df_var.iloc[-1]["minggu_ke"]
    #     last_year = df_var.iloc[-1]["tahun"]

    #     all_forecasts.append({
    #         "nama_variasi": nama_variasi,
    #         "forecast": float(forecast[0])
    #     })

    #     # Simpan hasil prediksi ke DB
    #     db_service.save_prediction(
    #         forecast,
    #         start_week=last_week + 1,
    #         start_year=last_year,
    #         model_versi=versi_model,
    #         id_buku=variasi
    #     )
        
    # return True, all_forecasts