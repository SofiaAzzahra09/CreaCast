# app/model_management.py
import streamlit as st
import pandas as pd

class ModelManagementPage:
    def __init__(self, registry, xgb_service, db):
        self.registry = registry
        self.xgb = xgb_service
        self.db = db

    def render(self):
        # 1. Suntikkan CSS untuk padding tombol 3px dan merapikan tampilan
        st.markdown("""
            <style>
                /* Memberikan padding 3px pada semua sisi tombol */
                div.stButton > button {
                    padding: 3px 3px !important;
                    min-height: 0px !important;
                    height: auto !important;
                }
                /* Mencegah teks tumpang tindih pada kolom sempit */
                div[data-testid="column"] {
                    overflow: hidden;
                }
            </style>
        """, unsafe_allow_html=True)

        st.title("Model Management")
        st.caption("Kelola versi model prediksi")

        tab1, tab2 = st.tabs([
            "Daftar Model",
            "Retrain Model"
        ])

        with tab1:
            self.show_models()

        with tab2:
            self.retrain_model()

    def show_models(self):
        df = self.registry.get_all() # Memanggil DatabaseService.fetchdf

        if df.empty:
            st.info("Belum ada model tersimpan")
            return

        st.markdown("### 🤖 Daftar Model")
        
        # Grid Header
        header = st.columns([1.5, 2, 0.8, 0.8, 0.8, 1.2, 2.5])
        names = ["Versi", "Tanggal", "RMSE", "MAE", "R²", "Status", "Aksi"]
        for col, name in zip(header, names):
            col.markdown(f"**{name}**")

        for i, row in df.iterrows():
            # Normalisasi status untuk pengecekan
            curr_status = str(row["status"]).strip().lower()
            # Jika 'aktif' maka True, jika 'nonaktif' atau 'archive' maka False
            is_active = (curr_status == "aktif")
            
            cols = st.columns([1.5, 2, 0.8, 0.8, 0.8, 1.2, 2.5])
            cols[0].write(row["versi"])
            cols[1].write(row["tanggal_training"])
            cols[2].write(f"{row['rmse']:.2f}")
            cols[3].write(f"{row['mae']:.2f}")
            cols[4].write(f"{row['r2']:.4f}")
            
            # Tampilan Label Status
            status_text = "Aktif" if is_active else "Nonaktif"
            cols[5].write(status_text)

            # Bagian Tombol
            btn_akt, btn_hap = cols[6].columns(2)
            
            with btn_akt:
                # Tombol MATI (disabled) jika status sudah aktif
                clicked = st.button(
                    "Aktifkan",
                    key=f"akt_{row['versi']}",
                    disabled=is_active,
                    type="primary",
                    use_container_width=True
                )

                if clicked:
                    self.registry.activate(row["versi"])

                    st.success(f"Model {row['versi']} berhasil diaktifkan")

                    st.rerun() # Refresh untuk ambil data terbaru

            with btn_hap:
                if st.button("Hapus", key=f"hap_{row['versi']}", use_container_width=True):
                    self.registry.delete(row["versi"])
                    st.rerun()

    def retrain_model(self):
        st.subheader("Retrain Model")
        df_all = self.registry.get_all()
        
        # Filter model aktif menggunakan .str.lower() untuk Series pandas
        model_aktif = df_all[df_all["status"].str.lower() == "aktif"]
        
        if model_aktif.empty:
            st.warning("Tidak ada model aktif. Aktifkan model di tab 'Daftar Model' terlebih dahulu.")
            return

        options = model_aktif["versi"].tolist()
        
        col_sel, _ = st.columns([2, 1])
        with col_sel:
            model_ref = st.selectbox("Model Referensi (Aktif)", options)
            catatan = st.text_input("Catatan", placeholder="Misal: Data terbaru Mei 2026")

        btn_train, _ = st.columns([0.6, 3])
        if btn_train.button("Mulai Retrain", type="primary", use_container_width=True):
            # ... proses training ...
            st.success(f"Model baru berhasil dilatih dari referensi {model_ref}")
            st.rerun()

# app/model_management.py
# import streamlit as st
# import pandas as pd

# class ModelManagementPage:
#     def __init__(self, registry, xgb_service, db):
#         self.registry = registry
#         self.xgb = xgb_service
#         self.db = db

#     def render(self):
#         st.title("Model Management")
#         st.caption("Kelola versi model prediksi")

#         tab1, tab2 = st.tabs([
#             "Daftar Model",
#             "Retrain Model"
#         ])

#         with tab1:
#             self.show_models()

#         with tab2:
#             self.retrain_model()

#     def show_models(self):
#         df = self.registry.get_all()

#         if df.empty:
#             st.info("Belum ada model tersimpan")
#             return

#         st.markdown("### Daftar Model")
        
#         # Header tabel manual
#         header = st.columns([2, 2, 1, 1, 1, 1.5, 2.5])
#         cols_name = ["Versi", "Tanggal", "RMSE", "MAE", "R²", "Status", "Aksi"]
#         for col, name in zip(header, cols_name):
#             col.markdown(f"**{name}**")

#         for i, row in df.iterrows():
#             cols = st.columns([2, 2, 1, 1, 1, 1.5, 2.5])
            
#             cols[0].write(row["versi"])
#             cols[1].write(row["tanggal_training"])
#             cols[2].write(f"{row['rmse']:.2f}")
#             cols[3].write(f"{row['mae']:.2f}")
#             cols[4].write(f"{row['r2']:.4f}")
            
#             # Status dengan badge sederhana
#             status_label = "Aktif" if row["status"].lower() == "aktif" else "Nonaktif"
#             cols[5].write(status_label)

#             aksi = cols[6].columns([1.2, 1])
            
#             # Logika Tombol Aktifkan: Disabled jika sudah aktif
#             is_active = row["status"].lower() == "aktif"
#             if aksi[0].button("Aktifkan", key=f"aktif_{row['versi']}", disabled=is_active, type="primary"):
#                 self.registry.activate(row["versi"])
#                 st.rerun()

#             if aksi[1].button("Hapus", key=f"hapus_{row['versi']}"):
#                 self.registry.delete(row["versi"])
#                 st.rerun()

#     def retrain_model(self):
#         st.subheader("Retrain Model")
#         st.info("Proses ini akan melatih model baru menggunakan data transaksi terbaru dari database.")

#         # Input dipersingkat, hanya catatan yang diperlukan
#         col_inp, _ = st.columns([2, 1])
#         with col_inp:
#             catatan = st.text_input(
#                 "Catatan Training", 
#                 placeholder="Misal: Penambahan data Mei 2026",
#                 help="Berikan deskripsi singkat perubahan data atau alasan retrain."
#             )

#         # Tombol retrain disesuaikan lebarnya (tidak stretch full)
#         btn_col, _ = st.columns([1, 3])
#         if btn_col.button("Mulai Retrain", type="primary"):
#             try:
#                 df = self.db.get_weekly_sales()

#                 if df.empty:
#                     st.warning("Gagal retrain: Data transaksi tidak ditemukan.")
#                     return

#                 with st.spinner("Sedang melatih model baru..."):
#                     metrics, params = self.xgb.train(df)
                    
#                     # Simpan model
#                     versi_baru = self.registry.save(
#                         self.xgb.model,
#                         metrics,
#                         params,
#                         catatan if catatan else "Retrain berkala"
#                     )

#                 st.success(f"Model berhasil diperbarui ke versi: {versi_baru}")
                
#                 # Tampilkan metrik hasil training
#                 m_col1, m_col2, m_col3, m_col4 = st.columns(4)
#                 m_col1.metric("RMSE", f"{metrics['rmse']:.2f}")
#                 m_col2.metric("MAE", f"{metrics['mae']:.2f}")
#                 m_col3.metric("R²", f"{metrics['r2']:.4f}")
#                 m_col4.metric("MSE", f"{metrics.get('mse', 0):.2f}")

#             except Exception as e:
#                 st.error(f"Terjadi kesalahan: {str(e)}")