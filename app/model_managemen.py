# app/model_management_page.py
# import streamlit as st
# import pandas as pd
# import plotly.graph_objects as go
# import json

# class ModelManagementPage:
#     def __init__(self, registry: ModelRegistry, xgb_service):
#         self.registry = registry
#         self.xgb = xgb_service

#     def _render_loss_curve(self, versi: str):
#         # Ambil evals_result dari training (disimpan di session atau db)
#         evals = st.session_state.get(f'evals_{versi}', {})
#         if not evals:
#             st.caption("Kurva loss tidak tersedia untuk versi ini.")
#             return
#         train_rmse = evals.get('train', {}).get('rmse', [])
#         val_rmse   = evals.get('eval',  {}).get('rmse', [])
#         fig = go.Figure()
#         fig.add_scatter(y=train_rmse, name='Train RMSE',
#                         line=dict(color='#1D9E75', width=1.5))
#         fig.add_scatter(y=val_rmse, name='Val RMSE',
#                         line=dict(color='#EF9F27', width=1.5, dash='dash'))
#         fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=200,
#                           legend=dict(orientation='h', y=1.1))
#         st.plotly_chart(fig, use_container_width=True)

#     def _render_compare_chart(self, df: pd.DataFrame):
#         fig = go.Figure(go.Bar(
#             x=df['versi'], y=df['rmse'],
#             marker_color=['#1D9E75' if s == 'active' else '#B4B2A9'
#                           for s in df['status']],
#             marker_cornerradius=4
#         ))
#         fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=200,
#                           yaxis_title='RMSE')
#         st.plotly_chart(fig, use_container_width=True)

#     def render(self):
#         st.title("Model management")
#         st.caption("Kelola versi model XGBoost — training, evaluasi, dan registry")

#         df = self.registry.get_all()
#         active = df[df['status'] == 'active'].iloc[0] if len(df) else None

#         c1, c2, c3, c4 = st.columns(4)
#         c1.metric("Total versi",    len(df))
#         c2.metric("Model aktif",    active['versi'] if active is not None else '—')
#         c3.metric("R² terbaik",     df['r2'].max() if len(df) else '—')
#         c4.metric("Training terakhir", df['tanggal_training'].iloc[0][:10] if len(df) else '—')

#         # Tombol retrain
#         col1, col2 = st.columns([4,1])
#         with col2:
#             if st.button("Retrain model", type="primary", use_container_width=True):
#                 with st.spinner("Melatih ulang model XGBoost..."):
#                     db_data = self.xgb.db.get_all_penjualan()
#                     hasil   = self.xgb.train(db_data)
#                     versi   = self.registry.save(
#                         self.xgb.model, hasil,
#                         self.xgb.model.get_params(), "Retrain otomatis")
#                     st.success(f"Model {versi} berhasil dilatih! RMSE: {hasil['rmse']}")
#                     st.rerun()

#         # Tabel registry
#         st.dataframe(
#             df[['versi','tanggal_training','rmse','mae','r2','mape','status']],
#             use_container_width=True, hide_index=True,
#             column_config={
#                 'r2':   st.column_config.NumberColumn("R²",   format="%.3f"),
#                 'mape': st.column_config.NumberColumn("MAPE", format="%.1f%%"),
#             }
#         )

#         # Detail & aksi per versi
#         versi_list = df['versi'].tolist()
#         selected   = st.selectbox("Pilih versi untuk detail", versi_list)
#         row        = df[df['versi'] == selected].iloc[0]

#         col_a, col_b = st.columns(2)
#         with col_a:
#             st.markdown("##### Hyperparameter")
#             params = json.loads(row['hyperparameter'])
#             for k, v in params.items():
#                 st.markdown(f"`{k}` = **{v}**")
#         with col_b:
#             st.markdown("##### Perbandingan RMSE")
#             self._render_compare_chart(df)

#         self._render_loss_curve(selected)

#         col_act, col_dl, col_del = st.columns(3)
#         with col_act:
#             if row['status'] != 'active':
#                 if st.button(f"Aktifkan {selected}", use_container_width=True, type="primary"):
#                     self.registry.activate(selected)
#                     st.success(f"Model {selected} kini aktif!")
#                     st.rerun()
#             else:
#                 st.success(f"Model {selected} sudah aktif")
#         with col_dl:
#             with open(row['file_path'], 'rb') as f:
#                 st.download_button("Download .pkl", f,
#                                    file_name=f"xgboost_{selected}.pkl",
#                                    use_container_width=True)
#         with col_del:
#             if row['status'] != 'active':
#                 if st.button(f"Hapus {selected}", use_container_width=True):
#                     self.registry.delete(selected)
#                     st.warning(f"Model {selected} dihapus.")
#                     st.rerun()

#app/model_managemen.py
import streamlit as st
import pandas as pd
import json
import os

class ModelManagementPage:
    def __init__(self, registry, xgb_service, db):
        self.registry = registry
        self.xgb = xgb_service
        self.db = db

    def render(self):
        st.title("Model Management")

        df = self.registry.get_all()

        if df is None or df.empty:
            st.info("Belum ada model.")
        else:
            st.dataframe(df, use_container_width=True)

        st.divider()

        # =============================
        # UPLOAD MODEL
        # =============================
        st.subheader("Upload Model (.pkl)")

        uploaded = st.file_uploader("Upload model", type=["pkl"])

        if uploaded:
            save_path = f"model/uploaded_{uploaded.name}"

            with open(save_path, "wb") as f:
                f.write(uploaded.read())

            st.success("Model berhasil diupload")

        # =============================
        # AKTIFKAN MODEL
        # =============================
        if df is not None and not df.empty:

            versi = st.selectbox("Pilih model", df["versi"])

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Aktifkan model"):
                    try:
                        self.registry.activate(versi)
                        st.success(f"Model {versi} aktif")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

            with col2:
                if st.button("Hapus model"):
                    try:
                        self.registry.delete(versi)
                        st.warning(f"Model {versi} dihapus")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        # =============================
        # LOAD MODEL AKTIF KE XGB
        # =============================
        st.divider()

        if st.button("Load model aktif ke sistem"):

            try:
                model = self.registry.load_active()
                self.xgb.model = model
                st.success("Model aktif berhasil dimuat")
            except Exception as e:
                st.error(str(e))