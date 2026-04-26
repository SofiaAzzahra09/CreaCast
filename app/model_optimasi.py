# app/optimasi_stok_page.py
# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go

# class OptimasisStokPage:
#     def __init__(self, db_service, stock_optimizer_cls):
#         self.db = db_service
#         self.OptimizerCls = stock_optimizer_cls  # inject class, bukan instance

#     def _render_kpi(self, df: pd.DataFrame):
#         kritis  = len(df[df['status'] == 'kritis'])
#         menipis = len(df[df['status'] == 'menipis'])
#         aman    = len(df[df['status'] == 'aman'])
#         total_restock = int(df['jumlah_restock'].sum())

#         c1, c2, c3, c4 = st.columns(4)
#         c1.metric("Perlu restock segera", kritis)
#         c2.metric("Hampir habis",         menipis)
#         c3.metric("Stok aman",            aman)
#         c4.metric("Total restock",        f"{total_restock:,} eksemplar")

#     def _render_chart(self, df: pd.DataFrame):
#         top8 = df.head(8)
#         colors = ['rgba(226,75,74,0.8)' if s == 'kritis'
#                   else 'rgba(239,159,39,0.75)' if s == 'menipis'
#                   else 'rgba(29,158,117,0.75)'
#                   for s in top8['status']]

#         fig = go.Figure()
#         fig.add_bar(x=top8['judul'], y=top8['stok'],
#                     name='Stok sekarang', marker_color=colors, marker_cornerradius=3)
#         fig.add_scatter(x=top8['judul'], y=top8['reorder_point'],
#                         mode='lines+markers', name='Reorder point',
#                         line=dict(color='#EF9F27', dash='dash', width=2))
#         fig.update_layout(
#             margin=dict(l=0, r=0, t=0, b=0), height=240,
#             showlegend=True,
#             legend=dict(orientation='h', y=1.15),
#             xaxis=dict(tickfont=dict(size=10))
#         )
#         st.plotly_chart(fig, use_container_width=True)

#     def render(self):
#         st.title("Optimasi stok")
#         st.caption("Rekomendasi reorder point & safety stock berbasis prediksi XGBoost")

#         # Parameter sidebar
#         with st.sidebar:
#             st.markdown("### Parameter optimasi")
#             lt = st.slider("Lead time (hari)", 1, 14, 7)
#             sl = st.select_slider("Service level (%)",
#                                   options=[80,85,90,91,92,93,94,95,96,97,98,99],
#                                   value=95)

#         optimizer = self.OptimizerCls(lead_time_days=lt, service_level=sl)
#         st.info(f"Z-score untuk SL {sl}% = {optimizer.z}")

#         # Ambil data & hitung
#         df_buku     = self.db.get_all_buku()
#         df_prediksi = self.db.get_latest_prediction()
#         df_historis = self.db.get_all_penjualan()
#         df = optimizer.hitung_semua(df_buku, df_prediksi, df_historis)

#         self._render_kpi(df)
#         self._render_chart(df)

#         st.dataframe(
#             df[['judul','stok','safety_stock','reorder_point','jumlah_restock','status','cukup_minggu']],
#             use_container_width=True, hide_index=True,
#             column_config={
#                 'jumlah_restock': st.column_config.NumberColumn("Restock", format="+%d"),
#                 'cukup_minggu':   st.column_config.NumberColumn("Cukup (minggu)", format="%.1f"),
#             }
#         )

#         csv = df.to_csv(index=False).encode()
#         st.download_button("Ekspor rekomendasi CSV", csv, "rekomendasi_stok.csv")

# app/model_optimasi.py
import streamlit as st
import pandas as pd

class OptimasisStokPage:
    def __init__(self, db_service, optimizer_cls):
        self.db = db_service
        self.OptimizerCls = optimizer_cls

    def render(self):

        st.title("Optimasi Stok")

        # =============================
        # PARAMETER
        # =============================
        lead_time = st.slider("Lead time (hari)", 1, 14, 7)
        service_level = st.selectbox("Service level (%)", [90, 95, 99], index=1)

        optimizer = self.OptimizerCls(lead_time, service_level)

        # =============================
        # AMBIL DATA
        # =============================
        df_buku = self.db.get_all_buku()
        df_prediksi = self.db.get_latest_prediction()
        df_hist = self.db.get_all_penjualan()

        # =============================
        # VALIDASI
        # =============================
        if df_buku is None or df_buku.empty:
            st.warning("Data buku masih kosong.")
            return

        if df_prediksi is None or df_prediksi.empty:
            st.warning("Belum ada hasil prediksi.")
            return

        if df_hist is None or df_hist.empty:
            st.warning("Data historis kosong.")
            return

        # =============================
        # FILTER & ACTION (1 BARIS)
        # =============================
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            kategori_list = ["Semua"] + self.db.get_kategori()
            selected_kategori = st.selectbox("Filter Kategori", kategori_list)

        with col2:
            search = st.text_input("Cari Judul")

        with col3:
            run_btn = st.button("Proses")

        # =============================
        # FILTER DATA
        # =============================
        if selected_kategori != "Semua":
            df_buku = df_buku[df_buku["kategori"] == selected_kategori]

        if search:
            df_buku = df_buku[df_buku["judul"].str.contains(search, case=False, na=False)]

        if df_buku.empty:
            st.warning("Data tidak ditemukan.")
            return

        # tombol proses
        if not run_btn:
            st.info("Klik tombol Proses untuk menjalankan optimasi")
            return

        # =============================
        # HITUNG
        # =============================
        try:
            df = optimizer.hitung_semua(df_buku, df_prediksi, df_hist)
        except Exception as e:
            st.error(f"Error: {e}")
            return

        # =============================
        # OUTPUT
        # =============================
        st.subheader("Rekomendasi Stok")

        st.dataframe(df, use_container_width=True)

        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode(),
            "stok.csv"
        )