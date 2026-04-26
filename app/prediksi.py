# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go


# class PrediksiPage:
#     def __init__(self, xgb_service, db_service):
#         self.xgb = xgb_service
#         self.db  = db_service

#     def render(self):

#         st.title("Prediksi permintaan buku")

#         # =============================
#         # INPUT
#         # =============================
#         n_weeks = st.selectbox("Jumlah minggu prediksi", [1,2,4,8], index=2)
#         hist = st.selectbox("Data historis (minggu)", [12,26,52], index=1)

#         # =============================
#         # BUTTON
#         # =============================
#         if st.button("Jalankan prediksi", type="primary"):

#             df = self.db.get_penjualan(weeks=hist)

#             if df is None or df.empty:
#                 st.warning("Data penjualan masih kosong.")
#                 return

#             if self.xgb.model is None:
#                 st.error("Model belum tersedia. Pastikan file model_xgb.pkl ada di folder model/")
#                 return

#             with st.spinner("Memproses..."):

#                 hasil = self.xgb.evaluate(df)
#                 forecast = self.xgb.forecast(df, n_weeks)

#                 st.session_state["hasil"] = hasil
#                 st.session_state["forecast"] = forecast

#         # =============================
#         # OUTPUT
#         # =============================
#         if "hasil" not in st.session_state:
#             st.info("Belum ada hasil prediksi.")
#             return

#         hasil = st.session_state["hasil"]

#         c1,c2,c3,c4,c5 = st.columns(5)
#         c1.metric("MSE", hasil['mse'])
#         c2.metric("RMSE", hasil['rmse'])
#         c3.metric("MAE", hasil['mae'])
#         c4.metric("R²", hasil['r2'])
#         c5.metric("MAPE", f"{hasil['mape']}%")

#         # =============================
#         # CHART
#         # =============================
#         fig = go.Figure()
#         fig.add_trace(go.Scatter(y=hasil['y_test'], name='Aktual'))
#         fig.add_trace(go.Scatter(y=hasil['y_pred'], name='Prediksi'))
#         st.plotly_chart(fig, use_container_width=True)

#         # =============================
#         # FORECAST TABLE
#         # =============================
#         st.subheader("Hasil Forecast")

#         fc_df = pd.DataFrame({
#             "Minggu": [f"M+{i+1}" for i in range(len(st.session_state["forecast"]))],
#             "Prediksi": st.session_state["forecast"]
#         })

#         st.dataframe(fc_df, use_container_width=True)

#         st.download_button(
#             "Download CSV",
#             fc_df.to_csv(index=False).encode(),
#             "forecast.csv"
#         )



# app/prediksi.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


class PrediksiPage:
    def __init__(self, xgb_service, db_service):
        self.xgb = xgb_service
        self.db  = db_service

    def render(self):

        st.title("Prediksi permintaan buku")

        # =============================
        # PARAMETER (1 BARIS)
        # =============================
        st.markdown("### Parameter Prediksi")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            n_weeks = st.selectbox(
                "Jumlah minggu prediksi",
                [1, 2, 4, 8],
                index=2
            )

        with col2:
            hist = st.selectbox(
                "Data historis (minggu)",
                [12, 26, 52],
                index=1
            )

        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            run_btn = st.button(
                "Jalankan",
                type="primary",
                use_container_width=True
            )

        # =============================
        # BUTTON ACTION
        # =============================
        if run_btn:

            df = self.db.get_penjualan(weeks=hist)

            if df is None or df.empty:
                st.warning("Data penjualan masih kosong.")
                return

            if self.xgb.model is None:
                st.error("Model belum tersedia. Pastikan model sudah dilatih.")
                return

            with st.spinner("Memproses prediksi..."):

                hasil = self.xgb.evaluate(df)
                forecast = self.xgb.forecast(df, n_weeks)

                st.session_state["hasil"] = hasil
                st.session_state["forecast"] = forecast

        # =============================
        # VALIDASI OUTPUT
        # =============================
        if "hasil" not in st.session_state:
            st.info("Belum ada hasil prediksi.")
            return

        hasil = st.session_state["hasil"]

        # =============================
        # METRIC
        # =============================
        st.markdown("### Evaluasi Model")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("MSE", round(hasil['mse'], 2))
        c2.metric("RMSE", round(hasil['rmse'], 2))
        c3.metric("MAE", round(hasil['mae'], 2))
        c4.metric("R²", round(hasil['r2'], 3))
        c5.metric("MAPE", f"{round(hasil['mape'],2)}%")

        # =============================
        # CHART
        # =============================
        st.markdown("### Grafik Prediksi vs Aktual")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=hasil['y_test'],
            name='Aktual'
        ))
        fig.add_trace(go.Scatter(
            y=hasil['y_pred'],
            name='Prediksi'
        ))

        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        # =============================
        # FORECAST
        # =============================
        st.markdown("### Hasil Forecast")

        forecast = st.session_state["forecast"]

        if forecast is None or len(forecast) == 0:
            st.warning("Forecast kosong.")
            return

        fc_df = pd.DataFrame({
            "Minggu": [f"M+{i+1}" for i in range(len(forecast))],
            "Prediksi": forecast
        })

        st.dataframe(fc_df, use_container_width=True)

        # =============================
        # DOWNLOAD
        # =============================
        st.download_button(
            "Download CSV",
            fc_df.to_csv(index=False).encode(),
            "forecast.csv",
            use_container_width=True
        )
