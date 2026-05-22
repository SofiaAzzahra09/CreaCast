#app/data_penjualan.py
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# from services.data.data_loader import DataLoader
# from services.data.data_validator import DataValidator
from services.feature_engineering import FeatureEngineer


class DataPenjualanPage:
    def __init__(self, db_service, pipeline_service):
        self.db = db_service
        self.pipeline = pipeline_service

    # =========================
    # LOAD DATA
    # =========================
    def _load_data(self):
        df = self.db.get_all_penjualan()

        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        return df

    # =========================
    # KPI
    # =========================
    def _render_kpi(self, df):
        if df.empty:
            st.warning("Belum ada data.")
            return

        last_week = df['week'].max()
        prev_week = last_week - pd.Timedelta(days=7)

        minggu_ini = df[df['week'] == last_week]
        minggu_lalu = df[df['week'] == prev_week]

        total_ini = minggu_ini['jumlah_terjual'].sum()
        total_lalu = minggu_lalu['jumlah_terjual'].sum()

        delta = ((total_ini - total_lalu) / total_lalu * 100) if total_lalu else 0

        c1, c2, c3 = st.columns(3)

        c1.metric("Penjualan minggu ini", f"{total_ini:,}", f"{delta:+.1f}%")
        c2.metric("Rata-rata mingguan", f"{int(df['jumlah_terjual'].mean()):,}")
        c3.metric("Jumlah minggu", df['week'].nunique())

    # =========================
    # CHART
    # =========================
    def _render_chart(self, df):
        df_grp = df.groupby(['week'])['jumlah_terjual'].sum().reset_index()

        fig = px.line(df_grp, x='week', y='jumlah_terjual', markers=True)

        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # UPLOAD
    # =========================
    def _handle_upload(self):
        file = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])

        if file:
            try:
                df = DataLoader.load(file)

                # VALIDASI
                DataValidator.validate_sales(df)

                # SIMPAN RAW
                self.db.insert_raw_transactions(df)

                st.session_state["upload_success"] = (
                    f"{len(df)} data berhasil disimpan ke RAW"
                )
                st.rerun()

            except Exception as e:
                st.error(str(e))

    # =========================
    # FILTER
    # =========================
    def _filter(self, df):
        search = st.text_input("Cari buku")

        if search:
            df = df[df['judul'].str.contains(search, case=False)]

        return df

    def _process_with_validation(self, df):
        fe = FeatureEngineer()

        # =============================
        # CLEANING AWAL
        # =============================
        df = fe.clean_data(df)
        df = fe.handle_missing_values(df)

        # =============================
        # DETEKSI MISSING
        # =============================
        df_missing = fe.detect_missing_critical(df)

        if not df_missing.empty:

            st.warning(
                f"Ditemukan {len(df_missing)} data yang belum lengkap."
            )

            st.subheader("Lengkapi Data")

            edited_df = st.data_editor(
                df_missing,
                use_container_width=True
            )

            col1, col2 = st.columns(2)

            with col1:
                save_manual = st.button(
                    "Gunakan Data Manual"
                )

            with col2:
                auto_fill = st.button(
                    "Isi Otomatis"
                )

            if save_manual:
                df.update(edited_df)
                st.success("Data manual diterapkan")

            elif auto_fill:
                df = fe.auto_impute_variasi(df)
                st.info("Sistem mengisi otomatis")

            else:
                st.stop()

        # =============================
        # VALIDASI FINAL
        # =============================
        remaining = fe.detect_missing_critical(df)

        if not remaining.empty:
            st.error("Masih ada data kosong.")
            st.stop()

        # =============================
        # LANJUT PIPELINE
        # =============================
        df = fe.compute_features(df)
        df = fe.add_time_features(df)
        df = fe.add_ramadhan_features(df)
        df = fe.encode_variasi(df)
        df = fe.add_product_age(df)
        df = fe.create_features(df)

        return df

    def _handle_interactive(self, df):
        fe = FeatureEngineer()

        df = fe.clean_data(df)
        df = fe.handle_missing_values(df)

        df_missing = fe.detect_missing_critical(df)

        if df_missing.empty:
            return df

        st.warning(f"Ditemukan {len(df_missing)} data belum lengkap.")
        st.subheader("Lengkapi Data Missing")

        edited_df = st.data_editor(
            df_missing,
            use_container_width=True,
            num_rows="fixed",
            key="missing_editor"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Gunakan Data Manual", use_container_width=True):
                st.session_state["fixed_df"] = edited_df
                st.session_state["continue_pipeline"] = True
                st.rerun()

        with col2:
            if st.button("Isi Otomatis", use_container_width=True):
                df = fe.auto_impute_variasi(df)
                st.session_state["fixed_df"] = df
                st.session_state["continue_pipeline"] = True
                st.rerun()

        st.stop()

    # Di dalam class DataPenjualanPage, perbaiki bagian ini:

    def _handle_missing_interactive(self, df):
        fe = FeatureEngineer()

        df = fe.clean_data(df)
        df = fe.handle_missing_values(df)

        df_missing = fe.detect_missing_critical(df)

        if df_missing.empty:
            return df

        st.warning(f"Ditemukan {len(df_missing)} data belum lengkap.")
        st.subheader("Lengkapi Data Missing")

        # Ini tabel tempat user memperbaiki data
        edited_df = st.data_editor(
            df_missing,
            use_container_width=True,
            num_rows="fixed",
            key="missing_editor"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Gunakan Data Manual", type="secondary", use_container_width=True):
                # Update data asli (df) dengan sel yang baru diketik (edited_df)
                df.update(edited_df)
                st.session_state["fixed_df"] = df
                st.session_state["continue_pipeline"] = True
                st.rerun()

        with col2:
            if st.button("Isi Otomatis", type="secondary", use_container_width=True):
                # Eksekusi algoritma isi otomatis
                df = fe.auto_impute_variasi(df)
                st.session_state["fixed_df"] = df
                st.session_state["continue_pipeline"] = True
                st.rerun()

        # Stop Streamlit agar user punya waktu mengisi data & klik tombol di atas
        st.stop()

    def render(self):
        st.title("Data Historis Penjualan")

        # =========================
        # UPLOAD + PIPELINE SATU BARIS
        # =========================
        if "upload_success" in st.session_state:
            st.success(st.session_state["upload_success"])
            del st.session_state["upload_success"]

        if "pipeline_success" in st.session_state:
            st.success(st.session_state["pipeline_success"])
            del st.session_state["pipeline_success"]
        st.subheader("📥 Upload & Proses Data")

        # col1, col2 = st.columns([3, 1])
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            files = st.file_uploader(
                "Upload CSV / Excel",
                type=["csv", "xlsx"],
                accept_multiple_files=True,
                label_visibility="collapsed"
            )

        with col2:
            upload_btn = st.button(
                "Simpan RAW",
                type="primary",
                use_container_width=True
            )

        with col3:
            run_pipeline = st.button(
                "Pipeline",
                type="primary",
                use_container_width=True
            )

        # Upload raw
        if files and upload_btn:
            try:
                all_df = []

                for file in files:
                    if file.name.endswith(".csv"):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)

                    all_df.append(df)

                df_combined = pd.concat(all_df, ignore_index=True)

                self.db.execute("DELETE FROM raw_transactions")
                self.db.execute("DELETE FROM weekly_sales")

                self.db.insert_raw_transactions(df_combined)

                st.session_state["upload_success"] = (
                    f"{len(files)} file berhasil disimpan ke RAW "
                    f"({len(df_combined)} baris)"
                )
                st.rerun()

            except Exception as e:
                st.error(str(e))

        # Proses pipeline
        # =========================
        # 1. TANGKAP EVENT KLIK TOMBOL PIPELINE
        # =========================
        if run_pipeline:
            # Kunci status bahwa pipeline sedang berjalan
            st.session_state["is_pipeline_running"] = True

        # =========================
        # 2. JALANKAN PIPELINE BERDASARKAN STATUS, BUKAN TOMBOL
        # =========================
        # Jika status jalan ATAU ada perintah continue dari tombol manual/otomatis
        if st.session_state.get("is_pipeline_running") or st.session_state.get("continue_pipeline"):
            try:
                df_raw = self.db.get_raw_transactions()

                if df_raw.empty:
                    st.warning("Tidak ada data raw.")
                    st.session_state["is_pipeline_running"] = False # Reset
                    st.stop()

                if "fixed_df" in st.session_state:
                    df_fixed = pd.DataFrame(st.session_state["fixed_df"])
                    # Bersihkan state sementara
                    del st.session_state["fixed_df"]
                    del st.session_state["continue_pipeline"]
                else:
                    # Kalau ada data kosong, proses akan BERHENTI (st.stop) sementara di sini
                    df_fixed = self._handle_missing_interactive(df_raw)

                self.db.execute("DELETE FROM weekly_sales")

                # Eksekusi pipeline (pastikan parameter is_cleaned=True dipakai)
                result = self.pipeline.run(df_fixed, is_cleaned=True)

                if result is not None:
                    self.db.save_weekly_sales(result)

                    st.session_state["pipeline_success"] = (
                        f"Pipeline berhasil ({len(result)} row)"
                    )
                    st.session_state["is_pipeline_running"] = False # Selesai, reset state
                    st.rerun()

                else:
                    st.warning("Pipeline gagal.")
                    st.session_state["is_pipeline_running"] = False # Gagal, reset state

            except Exception as e:
                st.session_state["is_pipeline_running"] = False # Error, reset state
                st.error(f"Error Pipeline: {str(e)}")

        st.divider()

        # =========================
        # TAMPILKAN WEEKLY
        # =========================
        st.subheader("📊 Data Weekly Sales")

        df_weekly = self.db.get_weekly_sales()

        if df_weekly.empty:
            st.info("Belum ada data weekly. Silakan proses data dulu.")
        else:
            st.dataframe(df_weekly, use_container_width=True)