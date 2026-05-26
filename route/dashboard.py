# route/dashboard.py
from flask import Blueprint, render_template
import pandas as pd

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)

# =====================================================
# DASHBOARD
# =====================================================

@dashboard_bp.route("/dashboard")
def dashboard():

    from services.database_service import DatabaseService

    db = DatabaseService()

    df = db.get_weekly_sales()

    df_buku = db.get_all_buku()
    raw_df = db.get_raw_transactions()

    # =====================================================
    # FALLBACK KOLOM
    # =====================================================

    required_columns = [
        "net_jumlah",
        "nama_variasi",
        "tahun",
        "minggu_ke",
        "weekday"
    ]

    for col in required_columns:

        if col not in df.columns:

            if col == "nama_variasi":
                df[col] = "Unknown"

            else:
                df[col] = 0

    # =====================================================
    # KPI
    # =====================================================

    total_minggu = 0
    total_penjualan = 0
    rata_penjualan = 0
    total_variasi = 0

    if not df.empty:

        total_minggu = len(df)

        total_penjualan = int(
            df["net_jumlah"].sum()
        )

        rata_penjualan = round(
            df["net_jumlah"].mean(),
            2
        )

        total_variasi = df[
            "nama_variasi"
        ].nunique()

    # =====================================================
    # TREND
    # =====================================================

    trend_df = (
        df.groupby(
            ["tahun", "minggu_ke"]
        )["net_jumlah"]
        .sum()
        .reset_index()
    )

    trend_labels = [
        f"{r['tahun']}-W{r['minggu_ke']}"
        for _, r in trend_df.iterrows()
    ]

    trend_values = trend_df[
        "net_jumlah"
    ].tolist()

    # =====================================================
    # TOP VARIASI
    # =====================================================

    top_df = (
        df.groupby("nama_variasi")["net_jumlah"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    top_labels = top_df[
        "nama_variasi"
    ].tolist()

    top_values = top_df[
        "net_jumlah"
    ].tolist()

    # =====================================================
    # LOW SALES
    # =====================================================

    low_df = (
        df.groupby("nama_variasi")["net_jumlah"]
        .sum()
        .sort_values(ascending=True)
        .head(10)
        .reset_index()
    )

    low_labels = low_df[
        "nama_variasi"
    ].tolist()

    low_values = low_df[
        "net_jumlah"
    ].tolist()

    # =====================================================
    # DAILY SALES
    # =====================================================

    daily_labels = []
    daily_values = []

    if not raw_df.empty:

        raw_df["waktu_pesanan_dibuat"] = pd.to_datetime(
            raw_df["waktu_pesanan_dibuat"],
            errors="coerce"
        )

        raw_df = raw_df.dropna(
            subset=["waktu_pesanan_dibuat"]
        )

        raw_df["weekday"] = (
            raw_df["waktu_pesanan_dibuat"]
            .dt.weekday
        )

        hari_map = {
            0: "Senin",
            1: "Selasa",
            2: "Rabu",
            3: "Kamis",
            4: "Jumat",
            5: "Sabtu",
            6: "Minggu"
        }

        daily_df = (
            raw_df.groupby("weekday")
            .size()
            .reset_index(name="total")
        )

        daily_df["hari"] = (
            daily_df["weekday"]
            .map(hari_map)
        )

        daily_labels = (
            daily_df["hari"]
            .tolist()
        )

        daily_values = (
            daily_df["total"]
            .tolist()
        )

    # =====================================================
    # STOK MENIPIS
    # =====================================================

    stok_tipis = pd.DataFrame()

    if (
        not df_buku.empty and
        "stok" in df_buku.columns
    ):

        stok_tipis = (
            df_buku[df_buku["stok"] <= 5]
            .sort_values("stok")
        )

    return render_template(
        "dashboard.html",

        total_minggu=total_minggu,
        total_penjualan=total_penjualan,
        rata_penjualan=rata_penjualan,
        total_variasi=total_variasi,

        trend_labels=trend_labels,
        trend_values=trend_values,

        top_labels=top_labels,
        top_values=top_values,

        low_labels=low_labels,
        low_values=low_values,

        daily_labels=daily_labels,
        daily_values=daily_values,

        stok_tipis=stok_tipis.to_dict(
            orient="records"
        )
    )