# route/optimasi_stok.py

from flask import Blueprint, render_template, request, make_response
import io

from services.database_service import DatabaseService
from services.stok_optimizer import StockOptimizer

optimasi_stok_bp = Blueprint(
    "optimasi_stok",
    __name__,
    url_prefix="/optimasi-stok"
)

db = DatabaseService()


@optimasi_stok_bp.route("/", methods=["GET"])
def index():

    # =============================
    # PARAMETER
    # =============================
    buffer_stok = request.args.get("buffer_stok", default=5, type=int)

    optimizer = StockOptimizer(buffer_stok)

    # =============================
    # DATA
    # =============================
    df_buku = db.get_all_buku()
    df_prediksi = db.get_latest_prediction()

    if df_buku.empty:
        return render_template(
            "optimasi_stok/index.html",
            data=[],
            warning="Data buku kosong",
            buffer_stok=buffer_stok
        )

    if df_prediksi.empty:
        return render_template(
            "optimasi_stok/index.html",
            data=[],
            warning="Belum ada hasil prediksi",
            buffer_stok=buffer_stok
        )

    # =============================
    # PROSES OPTIMASI
    # =============================
    hasil = optimizer.hitung_semua(
        df_buku,
        df_prediksi
    )

    # Pastikan data tidak kosong sebelum di-format dan di-sort
    if not hasil.empty:
        # Deteksi nama kolom (bisa kategori/nama_produk dan judul/nama_variasi)
        kolom_produk = "kategori" if "kategori" in hasil.columns else "nama_produk"
        kolom_variasi = "judul" if "judul" in hasil.columns else "nama_variasi"

        if kolom_produk in hasil.columns:
            hasil[kolom_produk] = hasil[kolom_produk].astype(str).str.strip().str.title()
        if kolom_variasi in hasil.columns:
            hasil[kolom_variasi] = hasil[kolom_variasi].astype(str).str.strip().str.title()

        # Sort Produk A-Z, lalu Variasi A-Z
        hasil = hasil.sort_values(
            by=[kolom_produk, kolom_variasi],
            ascending=[True, True]
        )

    data = hasil.to_dict(orient="records")

    return render_template(
        "optimasi_stok/index.html",
        data=data,
        warning=None,
        buffer_stok=buffer_stok
    )


@optimasi_stok_bp.route("/download")
def download_csv():

    buffer_stok = request.args.get("buffer_stok", default=5, type=int)

    optimizer = StockOptimizer(buffer_stok)

    df_buku = db.get_all_buku()
    df_prediksi = db.get_latest_prediction()

    hasil = optimizer.hitung_semua(
        df_buku,
        df_prediksi
    )

    output = io.StringIO()

    hasil.to_csv(output, index=False)

    response = make_response(output.getvalue())

    response.headers["Content-Disposition"] = "attachment; filename=optimasi_stok.csv"
    response.headers["Content-type"] = "text/csv"

    return response