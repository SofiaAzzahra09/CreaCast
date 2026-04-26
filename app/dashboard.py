# app/dashboard_page.py
import streamlit as st
import pandas as pd

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

class DashboardPage:
    def __init__(self, db_service):
        self.db = db_service  # dependency injection
        if go is None:
            st.error("Modul 'plotly' tidak ditemukan. Install dengan `pip install -r requirements.txt`.")
            st.stop()

    def _render_kpi(self, col, label, value, badge, badge_type="success"):
        colors = {"success": "🟢", "danger": "🔴", "info": "🔵", "warning": "🟡"}
        with col:
            st.metric(label=label, value=value, delta=badge)

    def _render_trend_chart(self):
        df = self.db.get_weekly_sales(weeks=8)
        pred = self.db.get_latest_prediction()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['minggu'], y=df['total_terjual'],
            name='Aktual', line=dict(color='#1D9E75', width=2),
            fill='tozeroy', fillcolor='rgba(29,158,117,0.08)'
        ))
        fig.add_trace(go.Scatter(
            x=[df['minggu'].iloc[-1], 'M-next'],
            y=[df['total_terjual'].iloc[-1], pred],
            name='Prediksi XGBoost',
            line=dict(color='#EF9F27', width=2, dash='dash'),
        ))
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=220)
        st.plotly_chart(fig, use_container_width=True)

    def _render_alerts(self):
        kritis = self.db.get_low_stock(threshold=15)
        for _, row in kritis.iterrows():
            status = "🔴 Kritis" if row['stok'] < 5 else "🟡 Menipis"
            st.write(f"{status} — **{row['judul']}** (sisa {row['stok']})")

    def render(self):
        st.title("Dashboard")
        st.caption("Ringkasan performa & prediksi terkini")

        col1, col2, col3, col4 = st.columns(4)
        self._render_kpi(col1, "Total buku", 248, "+12 bulan ini")
        self._render_kpi(col2, "Penjualan minggu ini", "1.340", "+8.2%")
        self._render_kpi(col3, "Prediksi minggu depan", "1.510", "XGBoost", "info")
        self._render_kpi(col4, "Stok kritis", 5, "Perlu restock", "danger")

        st.subheader("Tren penjualan & prediksi")
        self._render_trend_chart()

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Top 5 terlaris")
            st.dataframe(self.db.get_top_books(5), use_container_width=True)
        with col_b:
            st.subheader("Alert stok kritis")
            self._render_alerts()