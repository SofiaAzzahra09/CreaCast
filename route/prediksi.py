# route/prediksi.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

import plotly.graph_objects as go
import plotly

from services.database_service import DatabaseService
from services.xgboost_service import XGBoostService
from services.model_registry import ModelRegistry
from services.pipeline_service import PipelineService
import pandas as pd

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
    chart_json = None
    versi_model = None
    forecast_label = None

    # =====================================================
    # POST -> TRAIN & FORECAST BARU
    # =====================================================

    if request.method == "POST":

        try:

            n_weeks = int(
                request.form.get("n_weeks", 4)
            )

            hist = int(
                request.form.get("hist", 26)
            )

            # =============================================
            # LABEL TABEL
            # =============================================

            if n_weeks == 1:

                forecast_label = (
                    "Prediksi Stok 1 Minggu ke Depan"
                )

            else:

                forecast_label = (
                    f"Prediksi Stok {n_weeks} Minggu ke Depan"
                )

            # session["forecast_weeks"] = n_weeks

            # =============================================
            # LOAD DATA HISTORIS
            # =============================================

            df = db.get_weekly_sales(
                weeks=hist
            )

            if df.empty:

                flash(
                    "Data mingguan belum tersedia.",
                    "warning"
                )

                return redirect(
                    url_for("prediksi.index")
                )

            # =============================================
            # TRAIN MODEL
            # =============================================

            # metrics_res, params = xgb.train(df)
            metrics_res, params, eval_chart = xgb.train(df)

            # =============================================
            # SIMPAN MODEL BARU
            # =============================================

            versi = registry.save(
                xgb.model,
                metrics_res,
                params,
                f"Auto forecast {n_weeks} minggu"
            )

            db.execute("""
                UPDATE model_registry
                SET chart_json = ?,
                    forecast_weeks = ?
                WHERE versi = ?
            """, (
                eval_chart,
                n_weeks,
                versi
            ))

            # =============================================
            # AKTIFKAN MODEL TERBARU
            # =============================================

            registry.activate(versi)

            # =============================================
            # GENERATE FORECAST
            # =============================================

            sukses, hasil_forecast = (
                generate_forecast_pipeline(
                    versi_model=versi,
                    n_weeks=n_weeks,
                    hist=hist
                )
            )

            if not sukses:

                flash(
                    hasil_forecast,
                    "danger"
                )

                return redirect(
                    url_for("prediksi.index")
                )

            flash(
                f"Model baru berhasil dilatih ({versi}) dan prediksi telah diperbarui!",
                "success"
            )

            return redirect(
                url_for("prediksi.index")
            )

        except Exception as e:

            flash(
                f"Error model: {str(e)}",
                "danger"
            )

            return redirect(
                url_for("prediksi.index")
            )

    # =====================================================
    # LOAD MODEL AKTIF
    # =====================================================

    model_aktif = db.fetchone("""
        SELECT *
        FROM model_registry
        WHERE LOWER(status) = 'aktif'
        ORDER BY tanggal_training DESC
        LIMIT 1
    """)

    # =====================================================
    # JIKA ADA MODEL AKTIF
    # =====================================================

    if model_aktif:

        versi_model = model_aktif["versi"]

        metrics = {

            "mse": round(
                model_aktif["mse"],
                2
            ),

            "rmse": round(
                model_aktif["rmse"],
                2
            ),

            "mae": round(
                model_aktif["mae"],
                2
            ),

            "r2": round(
                model_aktif["r2"],
                3
            ),
        }

        # =============================================
        # LOAD FORECAST TERBARU
        # =============================================

        rows = db.fetchdf("""
            SELECT 
                b.judul AS nama_variasi,
                SUM(p.prediksi) AS forecast
            FROM prediksi p
            JOIN buku b
                ON p.id_buku = b.id
            WHERE p.model_versi = ?
            GROUP BY b.judul
            ORDER BY b.judul ASC
        """, (versi_model,))

        if not rows.empty:

            forecast_data = rows.to_dict(
                orient="records"
            )

            # =========================================
            # CHART FORECAST
            # =========================================

            chart_json = model_aktif["chart_json"]

    # =====================================================
    # SELECTED WEEKS
    # =====================================================

    selected_weeks = 4

    if model_aktif:

        selected_weeks = (
            model_aktif["forecast_weeks"] or 4
        )

    # =====================================================
    # LABEL DEFAULT
    # =====================================================

    saved_weeks = selected_weeks

    if not forecast_label:

        if saved_weeks == 1:

            forecast_label = (
                "Prediksi Stok 1 Minggu ke Depan"
            )

        else:

            forecast_label = (
                f"Prediksi Stok {saved_weeks} Minggu ke Depan"
            )

    # =====================================================
    # RENDER
    # =====================================================

        # =====================================================
    # TABLE CONFIG
    # =====================================================

    table_config = {

        "headers": [

            {
                "title": "Nama Variasi",
                "style": "min-width:250px;"
            },

            {
                "title": forecast_label,
                "style": "width:250px;"
            }

        ],

        "columns": [

            {
                "key": "nama_variasi"
            },

            {
                "key": "forecast_display"
            }

        ],

        "show_action": False
    }

    # =====================================================
    # FORMAT DATA TABLE
    # =====================================================

    for item in forecast_data:

        item["forecast_display"] = (
            f"{int(round(item['forecast']))} eksemplar"
        )

    return render_template(

        "prediksi/index.html",

        metrics=metrics,

        data=forecast_data,

        chart_json=chart_json,

        versi_model=versi_model,

        forecast_label=forecast_label,

        table_config=table_config,

        selected_weeks=selected_weeks,
    )


# =========================================================
# FORECAST PIPELINE
# =========================================================

def generate_forecast_pipeline(
    versi_model,
    n_weeks=4,
    hist=26
):

    import json
    import os

    from services.database_service import DatabaseService
    from services.xgboost_service import XGBoostService

    db_service = DatabaseService()

    df = db_service.get_weekly_sales(
        weeks=hist
    )

    if df.empty:

        return (
            False,
            "Data mingguan kosong."
        )

    # =====================================================
    # LOAD VARIASI MAP
    # =====================================================

    map_path = "data/variasi_map.json"

    if not os.path.exists(map_path):

        return (
            False,
            f"File mapping {map_path} tidak ditemukan."
        )

    with open(
        map_path,
        "r",
        encoding="utf-8"
    ) as f:

        variasi_map = json.load(f)

    inverse_variasi_map = {
        v: k for k, v in variasi_map.items()
    }

    # =====================================================
    # LOAD MODEL
    # =====================================================

    row_model = db_service.fetchone("""
        SELECT file_path
        FROM model_registry
        WHERE versi = ?
    """, (versi_model,))

    if not row_model:

        return (
            False,
            f"Model {versi_model} tidak ditemukan."
        )

    xgb_service = XGBoostService(
        row_model["file_path"]
    )

    if hasattr(xgb_service, "load_model"):

        xgb_service.load_model()

    else:

        import pickle

        with open(
            row_model["file_path"],
            "rb"
        ) as f:

            xgb_service.model = pickle.load(f)

    if xgb_service.model is None:

        return (
            False,
            f"Gagal load model {versi_model}."
        )

    # =====================================================
    # HAPUS PREDIKSI LAMA MODEL INI
    # =====================================================

    db_service.execute("""
        DELETE FROM prediksi
        WHERE model_versi = ?
    """, (versi_model,))

    all_forecasts = []

    # =====================================================
    # LOOPING FORECAST
    # =====================================================

    for variasi in df["variasi_encoded"].unique():

        # skip invalid
        if int(variasi) == 229:
            continue

        df_var = df[
            df["variasi_encoded"] == variasi
        ].copy()

        if len(df_var) < 4:
            continue

        forecast = xgb_service.forecast(
            df_var,
            n_weeks
        )

        nama_variasi = df_var.iloc[0][
            "nama_variasi"
        ]

        last_week = int(
            df_var.iloc[-1]["minggu_ke"]
        )

        last_year = int(
            df_var.iloc[-1]["tahun"]
        )

        # =============================================
        # TAMPILKAN TOTAL FORECAST
        # =============================================

        total_forecast = round(
            float(sum(forecast))
        )

        all_forecasts.append({

            "nama_variasi": nama_variasi,

            "forecast": total_forecast

        })

        # =============================================
        # MAP KE ID ASLI BUKU
        # =============================================

        nama_buku_asli = inverse_variasi_map.get(
            int(variasi),
            None
        )

        id_buku_asli = None

        if nama_buku_asli:

            id_buku_asli = (
                db_service.get_buku_id_by_judul(
                    nama_buku_asli
                )
            )

        print("================================")
        print("VARIASI ENCODED :", variasi)
        print("NAMA ASLI       :", nama_buku_asli)
        print("ID BUKU         :", id_buku_asli)
        print("================================")

        if id_buku_asli is None:

            print(
                f"Buku '{nama_buku_asli}' belum ada di tabel buku."
            )

            continue

        # =============================================
        # SIMPAN KE DATABASE
        # =============================================

        db_service.save_prediction(

            forecast=forecast,

            start_week=last_week + 1,

            start_year=last_year,

            model_versi=versi_model,

            id_buku=id_buku_asli

        )

    # =====================================================
    # SORT
    # =====================================================

    all_forecasts = sorted(

        all_forecasts,

        key=lambda x: x["nama_variasi"]

    )

    return True, all_forecasts