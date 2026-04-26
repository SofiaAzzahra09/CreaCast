# app/prediksi_page.py
import streamlit as st
import plotly.graph_objects as go

class PrediksiPage:
    def __init__(self, xgb_service, db_service):
        self.xgb = xgb_service
        self.db  = db_service

    def _render_metrics(self, hasil: dict):
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("RMSE",  hasil['rmse'])
        c2.metric("MAE",   hasil['mae'])
        c3.metric("R²",    hasil['r2'])
        c4.metric("MAPE",  f"{hasil['mape']}%")

    def _render_chart(self, hasil: dict):
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=hasil['y_test'], name='Aktual',
                                 line=dict(color='#1D9E75', width=2)))
        fig.add_trace(go.Scatter(y=hasil['y_pred'], name='Prediksi XGBoost',
                                 line=dict(color='#EF9F27', width=2, dash='dash')))
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=250,
                          legend=dict(orientation='h', y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    def render(self):
        st.title("Prediksi permintaan buku mingguan")
        st.caption("Implementasi algoritma XGBoost untuk forecasting demand")

        with st.expander("Parameter input", expanded=True):
            c1,c2 = st.columns(2)
            with c1:
                target = st.selectbox("Buku / kategori", ["Semua","Novel","Bisnis"])
                n_weeks = st.selectbox("Jumlah minggu prediksi", [1,2,4,8], index=2)
            with c2:
                hist = st.selectbox("Data historis", [12,26,52], index=1)
                split = st.selectbox("Metode split", ["80/20","70/30","Time-series split"])

        if st.button("Jalankan prediksi", type="primary", use_container_width=True):
            with st.spinner("Menjalankan model XGBoost..."):
                df = self.db.get_penjualan(weeks=hist)
                hasil = self.xgb.train(df)
                st.session_state['hasil_prediksi'] = hasil
                forecast = self.xgb.forecast(df, n_weeks=n_weeks)
                st.session_state['forecast'] = forecast
                self.db.save_prediction(forecast)

        if 'hasil_prediksi' in st.session_state:
            hasil = st.session_state['hasil_prediksi']
            self._render_metrics(hasil)
            self._render_chart(hasil)

            col_fi, col_fc = st.columns(2)
            with col_fi:
                st.markdown("##### Feature importance")
                fi = pd.DataFrame(hasil['feature_importance'].items(),
                                  columns=['Fitur','Importance'])
                fi = fi.sort_values('Importance', ascending=False)
                st.bar_chart(fi.set_index('Fitur'))
            with col_fc:
                st.markdown("##### Hasil forecast")
                fc_df = pd.DataFrame({
                    'Minggu': [f"M+{i+1}" for i in range(len(st.session_state['forecast']))],
                    'Prediksi': st.session_state['forecast']
                })
                st.dataframe(fc_df, use_container_width=True, hide_index=True)
                csv = fc_df.to_csv(index=False).encode()
                st.download_button("Ekspor CSV", csv, "prediksi_xgboost.csv")