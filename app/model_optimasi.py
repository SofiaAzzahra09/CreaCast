# app/model_optimasi.py
import streamlit as st


class OptimasiStokPage:

    def __init__(self, db_service, optimizer_cls):
        self.db = db_service
        self.OptimizerCls = optimizer_cls

    def render(self):

        st.title("Optimasi Stok")

        buffer_stok = st.slider(
            "Safety Stock (eksemplar)",
            0, 20, 5
        )

        optimizer = self.OptimizerCls(buffer_stok)

        df_buku = self.db.get_all_buku()
        df_prediksi = self.db.get_latest_prediction()

        if df_buku.empty:
            st.warning("Data buku kosong")
            return

        if df_prediksi.empty:
            st.warning("Belum ada hasil prediksi")
            return


        hasil = optimizer.hitung_semua(
            df_buku,
            df_prediksi
        )

        col1, col2 = st.columns([4,1])

        with col1:
            st.subheader("Rekomendasi Restock")

        with col2:
            st.download_button(
                "⬇️ Download",
                hasil.to_csv(index=False).encode("utf-8"),
                "optimasi_stok.csv",
                "text/csv"
            )

        st.dataframe(
            hasil[[
                "judul",
                "kategori",
                "stok",
                "demand_prediksi",
                "stok_rekomendasi",
                "restock",
                "status"
            ]],
            use_container_width=True
        )


# app/model_optimasi.py
# import streamlit as st
# import pandas as pd

# class OptimasisStokPage:
#     def __init__(self, db_service, optimizer_cls):
#         self.db = db_service
#         self.OptimizerCls = optimizer_cls

#     def render(self):

#         st.title("Optimasi Stok")

#         # =============================
#         # PARAMETER
#         # =============================
#         # lead_time = st.slider("Lead time (hari)", 1, 14, 7)
#         # service_level = st.selectbox("Service level (%)", [90, 95, 99], index=1)

#         col_lt, col_sl = st.columns(2)

#         with col_lt:
#             lead_time = st.slider("Lead time (hari)", 1, 14, 7)

#         with col_sl:
#             service_level = st.selectbox("Service level (%)", [90, 95, 99], index=1)

#         optimizer = self.OptimizerCls(lead_time, service_level)

#         # =============================
#         # AMBIL DATA
#         # =============================
#         df_buku = self.db.get_all_buku()
#         df_prediksi = self.db.get_latest_prediction()
#         df_hist = self.db.get_all_penjualan()

#         # =============================
#         # VALIDASI
#         # =============================
#         if df_buku is None or df_buku.empty:
#             st.warning("Data buku masih kosong.")
#             return

#         if df_prediksi is None or df_prediksi.empty:
#             st.warning("Belum ada hasil prediksi.")
#             return

#         if df_hist is None or df_hist.empty:
#             st.warning("Data historis kosong.")
#             return

#         # =============================
#         # FILTER & ACTION (1 BARIS)
#         # =============================
#         col1, col2, col3 = st.columns([2, 2, 1])

#         with col1:
#             kategori_list = ["Semua"] + self.db.get_kategori()
#             selected_kategori = st.selectbox("Filter Kategori", kategori_list)

#         with col2:
#             search = st.text_input("Cari Judul")

#         with col3:
#             run_btn = st.button("Proses")

#         # =============================
#         # FILTER DATA
#         # =============================
#         if selected_kategori != "Semua":
#             df_buku = df_buku[df_buku["kategori"] == selected_kategori]

#         if search:
#             df_buku = df_buku[df_buku["judul"].str.contains(search, case=False, na=False)]

#         if df_buku.empty:
#             st.warning("Data tidak ditemukan.")
#             return

#         # tombol proses
#         if not run_btn:
#             st.info("Klik tombol Proses untuk menjalankan optimasi")
#             return

#         # =============================
#         # HITUNG
#         # =============================
#         try:
#             df = optimizer.hitung_semua(df_buku, df_prediksi, df_hist)
#         except Exception as e:
#             st.error(f"Error: {e}")
#             return

#         # =============================
#         # OUTPUT
#         # =============================
#         st.subheader("Rekomendasi Stok")

#         st.dataframe(df, use_container_width=True)

#         st.download_button(
#             "Download CSV",
#             df.to_csv(index=False).encode(),
#             "stok.csv"
#         )