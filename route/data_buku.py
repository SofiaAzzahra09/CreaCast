# route/data_buku.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file
)

import pandas as pd
import io

data_buku_bp = Blueprint(
    "data_buku",
    __name__
)

# =====================================================
# INDEX
# =====================================================

@data_buku_bp.route("/data-buku")
def index():

    from services.database_service import DatabaseService

    db = DatabaseService()

    df = db.get_all_buku()

    search = request.args.get("search", "")

    if search:

        keyword = search.lower()

        df = df[
            df["judul"].astype(str).str.lower().str.contains(keyword)
            |
            df["kategori"].astype(str).str.lower().str.contains(keyword)
            |
            df["stok"].astype(str).str.contains(keyword)
            |
            df["harga"].astype(str).str.contains(keyword)
        ]

    if not df.empty:

        df["kategori"] = df["kategori"].astype(str).str.strip().str.title()
        df["judul"] = df["judul"].astype(str).str.strip().str.title()

        df = df.sort_values(
            by=["kategori", "judul"],
            ascending=[True, True]
        )

    # KPI

    if df.empty:
        total_produk = 0
        total_variasi = 0
        rata_harga = 0
    else:
        total_produk = df["kategori"].nunique()
        total_variasi = df["judul"].nunique()
        rata_harga = int(df["harga"].mean())

    data = df.to_dict(orient="records")

    return render_template(
        "data_buku/index.html",

        data=data,

        total_produk=total_produk,
        total_variasi=total_variasi,
        rata_harga=rata_harga,

        search=search
    )

# =====================================================
# TAMBAH
# =====================================================

@data_buku_bp.route(
    "/data-buku/tambah",
    methods=["POST"]
)
def tambah():

    from services.database_service import DatabaseService

    db = DatabaseService()

    db.save_buku({
        "judul": request.form["judul"],
        "kategori": request.form["kategori"],
        "harga": request.form["harga"],
        "stok": request.form["stok"]
    })

    flash("Data berhasil ditambah", "success")

    return redirect(url_for("data_buku.index"))

# =====================================================
# EDIT
# =====================================================

@data_buku_bp.route(
    "/data-buku/edit/<int:id>",
    methods=["POST"]
)
def edit(id):

    from services.database_service import DatabaseService

    db = DatabaseService()

    db.save_buku({
        "id": id,
        "judul": request.form["judul"],
        "kategori": request.form["kategori"],
        "harga": request.form["harga"],
        "stok": request.form["stok"]
    })

    flash("Data berhasil diupdate", "success")

    return redirect(url_for("data_buku.index"))

# =====================================================
# HAPUS
# =====================================================

@data_buku_bp.route("/data-buku/hapus/<int:id>")
def hapus(id):

    from services.database_service import DatabaseService

    db = DatabaseService()

    db.hapus_buku(id)

    flash("Data berhasil dihapus", "success")

    return redirect(url_for("data_buku.index"))

# =====================================================
# RESET
# =====================================================

@data_buku_bp.route("/data-buku/reset")
def reset():

    from services.database_service import DatabaseService

    db = DatabaseService()

    db.hapus_semua_buku()

    flash("Semua data berhasil dihapus", "success")

    return redirect(url_for("data_buku.index"))

# =====================================================
# EXPORT CSV
# =====================================================

@data_buku_bp.route("/data-buku/export")
def export_csv():

    from services.database_service import DatabaseService

    db = DatabaseService()

    df = db.get_all_buku()

    output = io.StringIO()

    df.to_csv(output, index=False)

    mem = io.BytesIO()

    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)

    return send_file(
        mem,
        as_attachment=True,
        download_name="data_buku.csv",
        mimetype="text/csv"
    )

# =====================================================
# IMPORT MULTIFILE (Excel & CSV)
# =====================================================

@data_buku_bp.route(
    "/data-buku/import",
    methods=["POST"]
)
def import_excel():

    from services.database_service import DatabaseService

    db = DatabaseService()

    uploaded_files = request.files.getlist("files")

    if not uploaded_files or uploaded_files[0].filename == '':
        flash("Tidak ada file yang dipilih", "danger")
        return redirect(url_for("data_buku.index"))

    jumlah_file_sukses = 0

    # =========================================
    # LOOP SEMUA FILE
    # =========================================
    for file in uploaded_files:

        filename = file.filename.lower()

        try:

            # =========================================
            # BACA FILE
            # =========================================
            if filename.endswith(".csv"):
                df = pd.read_csv(file)

            elif filename.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file)

            else:
                continue

            # =========================================
            # NORMALISASI NAMA KOLOM
            # =========================================
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
            )

            # =========================================
            # LOOP DATA
            # =========================================
            for _, row in df.iterrows():

                judul = str(
                    row.get("nama variasi", "Tanpa Variasi")
                ).strip()

                kategori = str(
                    row.get("nama produk", "-")
                ).strip()

                harga = pd.to_numeric(
                    row.get("harga awal", 0),
                    errors="coerce"
                )

                stok = pd.to_numeric(
                    row.get("stok", 0),
                    errors="coerce"
                )

                harga = 0 if pd.isna(harga) else int(harga)
                stok = 0 if pd.isna(stok) else int(stok)

                # =========================================
                # CEK DATA EXISTING
                # =========================================
                existing = db.get_all_buku()

                duplicate = existing[
                    (
                        existing["judul"]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        == judul.lower()
                    )
                    &
                    (
                        existing["kategori"]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        == kategori.lower()
                    )
                ]

                # =========================================
                # INSERT BARU
                # =========================================
                if duplicate.empty:

                    db.save_buku({
                        "judul": judul,
                        "kategori": kategori,
                        "harga": harga,
                        "stok": stok
                    })

                # =========================================
                # UPDATE JIKA DATA LAMA KOSONG
                # =========================================
                else:

                    data_lama = duplicate.iloc[0]

                    harga_lama = int(
                        data_lama.get("harga", 0)
                    )

                    stok_lama = int(
                        data_lama.get("stok", 0)
                    )

                    update_harga = (
                        harga_lama == 0
                        and harga > 0
                    )

                    update_stok = (
                        stok_lama == 0
                        and stok > 0
                    )

                    # kalau data baru lebih lengkap
                    if update_harga or update_stok:

                        db.save_buku({
                            "id": int(data_lama["id"]),
                            "judul": judul,
                            "kategori": kategori,

                            "harga": (
                                harga
                                if update_harga
                                else harga_lama
                            ),

                            "stok": (
                                stok
                                if update_stok
                                else stok_lama
                            )
                        })

            jumlah_file_sukses += 1

        except Exception as e:

            flash(
                f"Gagal memproses file {file.filename}: {str(e)}",
                "danger"
            )

            continue

    # =========================================
    # FEEDBACK
    # =========================================
    if jumlah_file_sukses > 0:
        flash(
            f"Berhasil mengimport {jumlah_file_sukses} file.",
            "success"
        )

    return redirect(url_for("data_buku.index"))