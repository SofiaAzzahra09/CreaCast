# app/laporan.py
import streamlit as st

class LaporanPage:
    def __init__(self, report_service, db_service):
        self.rs = report_service
        self.db = db_service

    def render(self):
        st.title("Laporan & ekspor")
        st.caption("Generate dan download laporan prediksi, penjualan, dan rekomendasi stok")

        # Pilih jenis laporan
        jenis = st.radio("Jenis laporan",
                         ["Prediksi mingguan", "Penjualan periodik", "Rekomendasi stok"],
                         horizontal=True)
        fmt = st.radio("Format", ["PDF", "CSV", "Excel (.xlsx)"], horizontal=True)

        col1, col2 = st.columns(2)
        with col1:
            periode = st.selectbox("Periode",
                ["Minggu ini", "Bulan ini", "Q2 2025", "Rentang kustom"])
        with col2:
            kategori = st.selectbox("Kategori",
                ["Semua", "Novel", "Bisnis", "Self-help"])

        if st.button("Generate laporan", type="primary", use_container_width=True):
            with st.spinner("Membuat laporan..."):
                forecast  = st.session_state.get('forecast', [1510,1488,1524,1563])
                metrics   = st.session_state.get('hasil_prediksi',
                                {'rmse':42.3,'mae':31.7,'r2':0.924,'mape':4.8})
                stok      = self.db.get_rekomendasi_stok()

                if fmt == "PDF":
                    data = self.rs.buat_pdf_prediksi(27, forecast, metrics, stok)
                    mime = "application/pdf"
                    nama = "creatroka_prediksi_m27.pdf"
                elif fmt == "CSV":
                    data = self.rs.buat_csv_penjualan(periode)
                    mime = "text/csv"
                    nama = "creatroka_penjualan.csv"
                else:
                    data = self.rs.buat_xlsx_prediksi(forecast, stok)
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    nama = "creatroka_prediksi.xlsx"

                self.db.save_laporan_history(nama, fmt.lower(), len(data) // 1024)
                st.success("Laporan berhasil dibuat!")
                st.download_button(
                    label=f"Download {nama}",
                    data=data,
                    file_name=nama,
                    mime=mime,
                    use_container_width=True
                )

        # Riwayat laporan
        st.subheader("Riwayat laporan")
        df_hist = self.db.get_laporan_history()
        st.dataframe(df_hist, use_container_width=True, hide_index=True)