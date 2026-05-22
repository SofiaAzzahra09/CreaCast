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

    # 1. Ambil list semua file yang di-upload dari HTML (sesuai name="files")
    uploaded_files = request.files.getlist("files")

    # Validasi jika user klik import tapi tidak memilih file sama sekali
    if not uploaded_files or uploaded_files[0].filename == '':
        flash("Tidak ada file yang dipilih", "danger")
        return redirect(url_for("data_buku.index"))

    jumlah_file_sukses = 0

    # 2. Iterasi/looping setiap file yang diunggah
    for file in uploaded_files:
        filename = file.filename.lower()

        try:
            # 3. Cek ekstensi file dan baca menggunakan Pandas yang sesuai
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                # Jika ada file dengan ekstensi aneh, skip ke file berikutnya
                continue

            # 4. Bersihkan nama kolom seperti kode aslimu
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
            )

            # 5. Looping isi baris data dan simpan ke database
            for _, row in df.iterrows():
                db.save_buku({
                    "judul": row.get("nama variasi", "Tanpa Variasi"),
                    "kategori": row.get("nama produk", "-"),
                    "harga": row.get("harga", 0), # Disambungkan ke kolom 'harga' jika ada di excel
                    "stok": row.get("stok", 0)    # Disambungkan ke kolom 'stok' jika ada di excel
                })
            
            jumlah_file_sukses += 1

        except Exception as e:
            # Jika ada satu file yang rusak/error, aplikasi tidak akan crash, melainkan lanjut log file lain
            flash(f"Gagal memproses file {file.filename}: {str(e)}", "danger")
            continue

    # 6. Beri feedback sukses ke user
    if jumlah_file_sukses > 0:
        flash(f"Berhasil mengimport {jumlah_file_sukses} file.", "success")
    
    return redirect(url_for("data_buku.index"))