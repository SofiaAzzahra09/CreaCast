# app/eda.py
import streamlit as st
import pandas as pd

try:
    import plotly.graph_objects as go
except ImportError:
    go = None


class EDASection:

    # =====================================================
    # TOP VARIASI
    # =====================================================
    @staticmethod
    def render_top_variasi(df):
        st.subheader("Top Variasi Terlaris")

        if df.empty:
            st.info("Belum ada data")
            return

        top_df = (
            df.groupby("nama_variasi")["net_jumlah"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top_df["nama_variasi"],
            y=top_df["net_jumlah"]
        ))

        fig.update_layout(
            height=350,
            xaxis_title="Variasi",
            yaxis_title="Total Terjual",
            margin=dict(l=20, r=20, t=40, b=80)
        )

        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # PRODUK KURANG LAKU
    # =====================================================
    @staticmethod
    def render_low_sales(df):
        st.subheader("Produk Kurang Laku")

        if df.empty:
            st.info("Belum ada data")
            return

        low_df = (
            df.groupby("nama_variasi")["net_jumlah"]
            .sum()
            .sort_values(ascending=True)
            .head(10)
            .reset_index()
        )

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=low_df["nama_variasi"],
            y=low_df["net_jumlah"]
        ))

        fig.update_layout(
            height=350,
            xaxis_title="Variasi",
            yaxis_title="Penjualan",
            margin=dict(l=20, r=20, t=40, b=80)
        )

        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # DISTRIBUSI PENJUALAN HARIAN
    # =====================================================
    @staticmethod
    def render_daily_sales(df):
        st.subheader("Distribusi Penjualan Harian")

        if df.empty:
            st.info("Belum ada data")
            return

        if "is_weekend" not in df.columns:
            st.warning("Kolom weekday belum tersedia")
            return

        if "weekday" not in df.columns:
            daily = pd.DataFrame({
                "hari": ["Weekday", "Weekend"],
                "net_jumlah": [
                    df[df["is_weekend"] == 0]["net_jumlah"].sum(),
                    df[df["is_weekend"] == 1]["net_jumlah"].sum()
                ]
            })
        else:
            hari_map = {
                0: "Senin",
                1: "Selasa",
                2: "Rabu",
                3: "Kamis",
                4: "Jumat",
                5: "Sabtu",
                6: "Minggu"
            }

            daily = (
                df.groupby("weekday")["net_jumlah"]
                .sum()
                .reset_index()
            )

            daily["hari"] = daily["weekday"].map(hari_map)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily["hari"],
            y=daily["net_jumlah"]
        ))

        fig.update_layout(
            height=350,
            xaxis_title="Hari",
            yaxis_title="Total Penjualan",
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # STOK MENIPIS
    # =====================================================
    @staticmethod
    def render_stok_menipis(book_df):
        st.subheader("Stok Menipis")

        if book_df.empty:
            st.info("Belum ada data buku")
            return

        if "stok" not in book_df.columns:
            st.warning("Kolom stok tidak ditemukan")
            return

        stok_tipis = (
            book_df[book_df["stok"] <= 5]
            .sort_values("stok")
        )

        if stok_tipis.empty:
            st.success("Tidak ada stok menipis")
            return

        st.dataframe(
            stok_tipis[["judul", "stok"]],
            use_container_width=True
        )