#app/prediksi.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from services.pipeline_service import PipelineService


class PrediksiPage:
    def __init__(self, xgb_service, db_service, registry):
        self.xgb = xgb_service
        self.db = db_service
        self.registry = registry
        self.pipeline = PipelineService()

    def render(self):

        st.title("Prediksi Permintaan Buku")

        # =============================
        # PARAMETER (RAPI 1 BARIS)
        # =============================
        container = st.container()

        with container:
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

            with col1:
                n_weeks = st.selectbox("Prediksi (minggu)", [1, 2, 4, 8], index=2)

            with col2:
                hist = st.selectbox("Data historis", [12, 26, 52], index=1)

            with col3:
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                run_btn = st.button("Jalankan", use_container_width=True)

            with col4:
                if "forecast" in st.session_state:
                    forecast = st.session_state["forecast"]

                    fc_df = pd.DataFrame({
                        "Minggu": [f"M+{i+1}" for i in range(len(forecast))],
                        "Prediksi": forecast
                    })

                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

                    st.download_button(
                        "Download",
                        fc_df.to_csv(index=False).encode(),
                        "forecast.csv",
                        use_container_width=True
                    )
        # =============================
        # RUN MODEL
        # =============================
        if run_btn:

            try:
                with st.spinner("Training model..."):
                    df = self.db.get_weekly_sales(weeks=hist)

                    if df.empty:
                        st.warning(
                            "Data mingguan belum tersedia. "
                            "Silakan proses data terlebih dahulu di menu Data Penjualan."
                        )
                        return

                    with st.expander("Preview Data Model"):
                        st.dataframe(df.head())

                    # =============================
                    # TRAIN
                    # =============================
                    metrics, params = self.xgb.train(df)

                    versi = self.registry.save(
                        self.xgb.model,
                        metrics,
                        params,
                        f"Auto forecast {n_weeks} minggu"
                    )

                    self.registry.activate(versi)

                    all_forecasts = []

                    for variasi in df["variasi_encoded"].unique():

                        df_var = df[df["variasi_encoded"] == variasi].copy()

                        if len(df_var) < 4:
                            continue

                        forecast = self.xgb.forecast(df_var, n_weeks)

                        nama_variasi = df_var.iloc[0]["nama_variasi"]
                        last_week = df_var.iloc[-1]["minggu_ke"]
                        last_year = df_var.iloc[-1]["tahun"]

                        all_forecasts.append({
                            "nama_variasi": nama_variasi,
                            "forecast": forecast[0]
                        })

                        self.db.save_prediction(
                            forecast,
                            start_week=last_week + 1,
                            start_year=last_year,
                            model_versi=versi,
                            id_buku=variasi
                        )

                    st.session_state["forecast"] = pd.DataFrame(all_forecasts)

                    st.session_state["versi_model"] = versi

                    st.session_state["metrics"] = metrics

                    st.success(f"Prediksi berhasil dijalankan ({versi})")

            except Exception as e:
                st.error(f"Error model: {e}")

        # =============================
        # OUTPUT
        # =============================
        if "versi_model" in st.session_state:
            st.caption(f"Model aktif: {st.session_state['versi_model']}")

        if "metrics" not in st.session_state:
            st.info("Belum ada hasil prediksi.")
            return

        hasil = st.session_state["metrics"]

        st.subheader("Evaluasi Model")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("MSE", round(hasil['mse'], 2))
        c2.metric("RMSE", round(hasil['rmse'], 2))
        c3.metric("MAE", round(hasil['mae'], 2))
        c4.metric("R²", round(hasil['r2'], 3))

        # =============================
        # CHART
        # =============================
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=hasil['y_test'], name='Aktual'))
        fig.add_trace(go.Scatter(y=hasil['y_pred'], name='Prediksi'))

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        # =============================
        # FORECAST
        # =============================
        st.subheader("Hasil Forecast")

        forecast = st.session_state["forecast"]

        fc_df = pd.DataFrame({
            "Minggu": [f"M+{i+1}" for i in range(len(forecast))],
            "Prediksi": forecast
        })

        st.dataframe(fc_df, use_container_width=True)
