from flask import render_template, session, redirect, url_for
import pandas as pd


def dashboard_route(db):

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    # =====================================================
    # LOAD DATA
    # =====================================================

    df = db.get_weekly_sales()
    book_df = db.get_all_buku()

    # =====================================================
    # HANDLE EMPTY
    # =====================================================

    if df.empty:

        total_minggu = 0
        total_penjualan = 0
        rata_penjualan = 0
        total_variasi = 0

    else:

        total_minggu = (
            df[["tahun", "minggu_ke"]]
            .drop_duplicates()
            .shape[0]
        )

        total_penjualan = int(
            df["net_jumlah"].sum()
        )

        rata_penjualan = int(
            df["net_jumlah"].mean()
        )

        total_variasi = (
            df["nama_variasi"]
            .nunique()
        )

    # =====================================================
    # TREND CHART
    # =====================================================

    trend_labels = []
    trend_values = []

    if not df.empty:

        trend_df = (
            df.groupby(["tahun", "minggu_ke"])["net_jumlah"]
            .sum()
            .reset_index()
            .sort_values(["tahun", "minggu_ke"])
        )

        trend_df["label"] = (
            trend_df["tahun"].astype(str)
            + "-W" +
            trend_df["minggu_ke"].astype(str)
        )

        trend_labels = trend_df["label"].tolist()
        trend_values = trend_df["net_jumlah"].tolist()

    return render_template(
        "dashboard.html",

        total_minggu=total_minggu,
        total_penjualan=f"{total_penjualan:,}",
        rata_penjualan=f"{rata_penjualan:,}",
        total_variasi=total_variasi,

        trend_labels=trend_labels,
        trend_values=trend_values
    )