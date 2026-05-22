# route/data_preparation.py
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session
)
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
from services.database_service import DatabaseService
from services.pipeline_service import PipelineService
from services.feature_engineering import FeatureEngineer

data_preparation_bp = Blueprint(
    "data_preparation",
    __name__,
    url_prefix="/data-preparation"
)

db = DatabaseService()
pipeline = PipelineService()
fe = FeatureEngineer()

ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}

def allowed_file(filename):
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

@data_preparation_bp.route("/", methods=["GET"])
def index():
    df_weekly = db.get_weekly_sales()
    df_raw_check = db.get_raw_transactions()
    has_raw_data = not df_raw_check.empty
    
    return render_template(
        "data_preparation/index.html",
        df_weekly=df_weekly,
        has_raw_data=has_raw_data
    )

@data_preparation_bp.route("/upload", methods=["POST"])
def upload_raw():
    files = request.files.getlist("files")
    
    if not files or files[0].filename == '':
        flash("File belum dipilih!", "warning")
        return redirect(url_for("data_preparation.index"))

    all_df = []
    combined_filename_logs = []

    try:
        for file in files:
            filename = secure_filename(file.filename)
            
            if not allowed_file(filename):
                flash(f"Format file tidak valid untuk {filename}. Hanya menerima CSV atau Excel.", "danger")
                return redirect(url_for("data_preparation.index"))

            if filename.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            df_mapped_check = fe.map_columns(df)
            if "jumlah" not in df_mapped_check.columns:
                flash(f"File {filename} ditolak! Kolom kuantitas/jumlah penjualan tidak dikenali.", "danger")
                return redirect(url_for("data_preparation.index"))

            all_df.append(df)
            combined_filename_logs.append(filename)

        df_combined = pd.concat(all_df, ignore_index=True)
        
        required_columns = ["jumlah"]
        normalized_cols = [c.lower().strip().replace(" ", "_") for c in df_combined.columns]
        missing_cols = [col for col in required_columns if col not in normalized_cols]

        if missing_cols:
            flash(f"Kolom wajib tidak ditemukan: {missing_cols}", "danger")
            return redirect(url_for("data_preparation.index"))

        meta_filenames = ", ".join(combined_filename_logs)
        meta_row_count = len(df_combined)

        result = db.insert_raw_transactions(df_combined, meta_filenames, meta_row_count)
        flash(f"Upload berhasil. {result['inserted']} data baru ditambahkan, {result['skipped']} data duplikat dilewati.", "success")

    except Exception as e:
        flash(f"Gagal memproses file upload: {str(e)}", "danger")

    return redirect(url_for("data_preparation.index"))


@data_preparation_bp.route("/run-pipeline", methods=["POST"])
def run_pipeline():

    try:

        df_raw = db.get_raw_transactions()

        if df_raw.empty:
            flash(
                "Data transaksi mentah (RAW) masih kosong.",
                "warning"
            )
            return redirect(url_for("data_preparation.index"))

        # ==========================================
        # CLEANING
        # ==========================================
        df_cleaned = fe.clean_data(df_raw)

        # ==========================================
        # DETEKSI MISSING
        # ==========================================
        missing = fe.detect_missing_critical(df_cleaned)

        print("\n========================")
        print("HASIL DETEKSI MISSING")
        print("========================")
        print("JUMLAH MISSING:", len(missing))

        # ==========================================
        # AUTO HANDLE jika missing terlalu banyak
        # ==========================================
        if not missing.empty:

            print("Menjalankan auto imputasi...")

            df_cleaned = fe.handle_missing_values(df_cleaned)

            flash(
                f"Ditemukan {len(missing)} missing value. Sistem melakukan imputasi otomatis.",
                "warning"
            )

        # ==========================================
        # LANJUTKAN PIPELINE
        # ==========================================
        df = fe.compute_features(df_cleaned)

        df = fe.add_time_features(df)

        df = fe.add_ramadhan_features(df)

        df = fe.encode_variasi(df)

        df = fe.add_product_age(df)

        result = fe.create_features(df)

        print("\n========================")
        print("HASIL PIPELINE")
        print("========================")
        print("JUMLAH :", len(result))
        print("KOLOM  :", result.columns.tolist())

        if not result.empty:
            print(result.head())

        # ==========================================
        # SAVE DB
        # ==========================================
        db.save_weekly_sales(result)

        flash(
            f"Pipeline berhasil diproses ({len(result)} data weekly).",
            "success"
        )

    except Exception as e:

        import traceback

        traceback.print_exc()

        flash(
            f"Error Pipeline: {str(e)}",
            "danger"
        )

    return redirect(url_for("data_preparation.index"))


@data_preparation_bp.route("/missing-validation", methods=["GET", "POST"])
def missing_validation():
    missing_data = session.get("missing_data", [])

    if not missing_data:
        flash("Tidak ada data missing yang perlu divalidasi.", "info")
        return redirect(url_for("data_preparation.index"))

    if request.method == "POST":
        action = request.form.get("action")
        df_raw = db.get_raw_transactions()
        df = fe.clean_data(df_raw)

        if action == "auto":
            # Memanggil fungsi class FeatureEngineer yang sudah dibersihkan
            df = fe.handle_missing_values(df)
        elif action == "manual":
            rows = []
            total_rows = int(request.form.get("total_rows", 0))
            for i in range(total_rows):
                row = {}
                for key in missing_data[i].keys():
                    form_val = request.form.get(f"{key}_{i}")
                    row[key] = form_val if form_val != "" else None
                rows.append(row)
            
            edited_df = pd.DataFrame(rows)
            df.update(edited_df)
            df = fe.handle_missing_values(df)

        try:
            # Melanjutkan sisa pipeline pasca imputasi
            df = fe.compute_features(df)
            df = fe.add_time_features(df)
            df = fe.add_ramadhan_features(df)
            df = fe.encode_variasi(df)
            df = fe.add_product_age(df)
            result = fe.create_features(df)

            db.save_weekly_sales(result)
            session.pop("missing_data", None)
            session.pop("has_missing", None)

            flash(f"Imputasi berhasil! Pipeline tuntas diproses ({len(result)} baris data mingguan diperbarui).", "success")
            return redirect(url_for("data_preparation.index"))
            
        except Exception as e:
            flash(f"Gagal memproses kelanjutan pipeline pasca-imputasi: {str(e)}", "danger")
            return redirect(url_for("data_preparation.missing_validation"))

    # PERBAIKAN UTAMA: Mengarah ke file html yang benar (missing_value.html)
    return render_template(
        "data_preparation/missing_value.html",
        missing_data=missing_data
    )

# from flask import (
#     Blueprint,
#     render_template,
#     request,
#     redirect,
#     url_for,
#     flash,
#     session
# )

# import pandas as pd
# import numpy as np

# from werkzeug.utils import secure_filename

# from services.database_service import DatabaseService
# from services.pipeline_service import PipelineService
# from services.feature_engineering import FeatureEngineer

# data_preparation_bp = Blueprint(
#     "data_preparation",
#     __name__,
#     url_prefix="/data-preparation"
# )

# db = DatabaseService()
# pipeline = PipelineService()
# fe = FeatureEngineer()


# @data_preparation_bp.route("/", methods=["GET", "POST"])
# def index():

#     df_weekly = db.get_weekly_sales()

#     if request.method == "POST":

#         action = request.form.get("action")

#         try:

#             # =====================================================
#             # UPLOAD RAW
#             # =====================================================

#             if action == "upload":

#                 files = request.files.getlist("files")

#                 if not files:

#                     flash(
#                         "File belum dipilih",
#                         "warning"
#                     )

#                     return redirect(
#                         url_for("data_preparation.index")
#                     )

#                 all_df = []

#                 for file in files:

#                     filename = secure_filename(file.filename)

#                     if filename.endswith(".csv"):
#                         df = pd.read_csv(file)

#                     else:
#                         df = pd.read_excel(file)

#                     all_df.append(df)

#                 df_combined = pd.concat(
#                     all_df,
#                     ignore_index=True
#                 )

#                 db.execute(
#                     "DELETE FROM raw_transactions"
#                 )

#                 db.execute(
#                     "DELETE FROM weekly_sales"
#                 )

#                 db.insert_raw_transactions(
#                     df_combined
#                 )

#                 flash(
#                     f"{len(files)} file berhasil disimpan "
#                     f"({len(df_combined)} baris)",
#                     "success"
#                 )

#                 return redirect(
#                     url_for("data_preparation.index")
#                 )

#             # =====================================================
#             # PIPELINE
#             # =====================================================

#             elif action == "pipeline":

#                 df_raw = db.get_raw_transactions()

#                 if df_raw.empty:

#                     flash(
#                         "Data RAW kosong",
#                         "warning"
#                     )

#                     return redirect(
#                         url_for("data_preparation.index")
#                     )

#                 # CLEANING
#                 df = fe.clean_data(df_raw)

#                 df = fe.handle_missing_values(df)

#                 # DETEKSI MISSING
#                 missing = fe.detect_missing_critical(df)

#                 # ADA MISSING
#                 if not missing.empty:

#                     session["has_missing"] = True

#                     missing_json = (
#                         missing
#                         .replace({np.nan: None})
#                         .to_dict(orient="records")
#                     )

#                     session["missing_data"] = missing_json

#                     flash(
#                         f"Ditemukan {len(missing)} data missing",
#                         "warning"
#                     )

#                     return redirect(
#                         url_for(
#                             "data_preparation.missing_validation"
#                         )
#                     )

#                 # LANJUT PIPELINE
#                 db.execute(
#                     "DELETE FROM weekly_sales"
#                 )

#                 result = pipeline.run(
#                     df,
#                     is_cleaned=True
#                 )

#                 db.save_weekly_sales(result)

#                 flash(
#                     f"Pipeline berhasil ({len(result)} row)",
#                     "success"
#                 )

#                 return redirect(
#                     url_for("data_preparation.index")
#                 )

#         except Exception as e:

#             flash(
#                 f"Error: {str(e)}",
#                 "danger"
#             )

#             return redirect(
#                 url_for("data_preparation.index")
#             )

#     return render_template(
#         "data_preparation/index.html",
#         df_weekly=df_weekly
#     )


# # =====================================================
# # VALIDASI MISSING
# # =====================================================

# @data_preparation_bp.route(
#     "/missing-validation",
#     methods=["GET", "POST"]
# )
# def missing_validation():

#     missing_data = session.get(
#         "missing_data",
#         []
#     )

#     if request.method == "POST":

#         action = request.form.get("action")

#         df_raw = db.get_raw_transactions()

#         df = fe.clean_data(df_raw)

#         df = fe.handle_missing_values(df)

#         # =====================================================
#         # AUTO FILL
#         # =====================================================

#         if action == "auto":

#             df = fe.auto_impute_variasi(df)

#         # =====================================================
#         # MANUAL
#         # =====================================================

#         elif action == "manual":

#             rows = []

#             total_rows = int(
#                 request.form.get("total_rows")
#             )

#             for i in range(total_rows):

#                 row = {}

#                 for key in missing_data[i].keys():

#                     row[key] = request.form.get(
#                         f"{key}_{i}"
#                     )

#                 rows.append(row)

#             edited_df = pd.DataFrame(rows)

#             df.update(edited_df)

#         # =====================================================
#         # RUN PIPELINE
#         # =====================================================

#         db.execute(
#             "DELETE FROM weekly_sales"
#         )

#         result = pipeline.run(
#             df,
#             is_cleaned=True
#         )

#         db.save_weekly_sales(result)

#         session.pop("missing_data", None)

#         flash(
#             f"Pipeline berhasil ({len(result)} row)",
#             "success"
#         )

#         return redirect(
#             url_for("data_preparation.index")
#         )

#     return render_template(
#         "data_preparation/missing_validation.html",
#         missing_data=missing_data
#     )