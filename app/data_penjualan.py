# pages/data_penjualan_page.py
import streamlit as st
import pandas as pd
import plotly.express as px

class DataPenjualanPage:
    def __init__(self, db_service):
        self.db = db_service

    def _render_kpi(self, df):
        minggu_ini = df[df['minggu_ke'] == df['minggu_ke'].max()]
        minggu_lalu = df[df['minggu_ke'] == df['minggu_ke'].max() - 1]
        total_ini  = minggu_ini['jumlah_terjual'].sum()
        total_lalu = minggu_lalu['jumlah_terjual'].sum()
        delta = ((total_ini - total_lalu) / total_lalu * 100) if total_lalu else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Terjual minggu ini", f"{total_ini:,}", f"{delta:+.1f}%")
        c2.metric("Rata-rata per hari", f"{total_ini//7:,}")
        c3.metric("Total data historis", f"{df['minggu_ke'].nunique()} minggu")
        top_kat = df.groupby('kategori')['jumlah_terjual'].sum().idxmax()
        c4.metric("Kategori terlaris", top_kat)

    def _render_trend_chart(self, df):
        df_grp = df.groupby(['minggu_ke','kategori'])['jumlah_terjual'].sum().reset_index()
        fig = px.line(df_grp, x='minggu_ke', y='jumlah_terjual',
                      color='kategori', markers=True,
                      color_discrete_map={
                          'Novel':'#1D9E75', 'Bisnis':'#378ADD',
                          'Self-help':'#EF9F27', 'Anak-anak':'#D4537E', 'Agama':'#7F77DD'
                      })
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=220,
                          legend=dict(orientation='h', y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    def _handle_upload(self):
        f = st.file_uploader("Upload data CSV", type=['csv'],
                             help="Kolom: id_buku, judul, kategori, minggu_ke, tahun, jumlah_terjual, harga_satuan")
        if f:
            df_up = pd.read_csv(f)
            required = {'id_buku','kategori','minggu_ke','tahun','jumlah_terjual','harga_satuan'}
            if not required.issubset(df_up.columns):
                st.error(f"Kolom tidak lengkap. Dibutuhkan: {required}")
                return
            self.db.insert_penjualan_bulk(df_up)
            st.success(f"{len(df_up):,} baris data berhasil diimport!")
            st.rerun()

    def render(self):
        st.title("Data penjualan")
        st.caption("Riwayat transaksi mingguan — sumber data utama training model XGBoost")

        col_btn1, col_btn2 = st.columns([5, 1])
        with col_btn2:
            show_upload = st.toggle("Upload CSV")

        df = self.db.get_all_penjualan()
        self._render_kpi(df)

        col_chart, col_donut = st.columns([1.6, 1])
        with col_chart:
            st.markdown("##### Tren penjualan mingguan")
            self._render_trend_chart(df)
        with col_donut:
            st.markdown("##### Komposisi per kategori")
            df_kat = df.groupby('kategori')['jumlah_terjual'].sum().reset_index()
            fig2 = px.pie(df_kat, values='jumlah_terjual', names='kategori', hole=0.6,
                          color_discrete_map={'Novel':'#1D9E75','Bisnis':'#378ADD',
                                              'Self-help':'#EF9F27','Anak-anak':'#D4537E','Agama':'#7F77DD'})
            fig2.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=220,
                               showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Filter & tabel
        c1, c2, c3 = st.columns([3, 1.5, 1.5])
        with c1: search = st.text_input("", placeholder="Cari judul...", label_visibility="collapsed")
        with c2: kat    = st.selectbox("", ["Semua"]+df['kategori'].unique().tolist(), label_visibility="collapsed")
        with c3: periode = st.selectbox("", ["Semua","Minggu ini","Bulan ini"], label_visibility="collapsed")

        df_f = df.copy()
        if search:   df_f = df_f[df_f['judul'].str.contains(search, case=False)]
        if kat != "Semua": df_f = df_f[df_f['kategori'] == kat]

        df_f['delta'] = df_f.groupby('id_buku')['jumlah_terjual'].diff()
        st.dataframe(df_f[['judul','kategori','minggu_ke','jumlah_terjual','harga_satuan','delta']],
                     use_container_width=True, hide_index=True,
                     column_config={
                         "jumlah_terjual": st.column_config.NumberColumn("Terjual"),
                         "harga_satuan":   st.column_config.NumberColumn("Harga", format="Rp%d"),
                         "delta":          st.column_config.NumberColumn("vs minggu lalu"),
                     })

        c_exp, _ = st.columns([1, 4])
        with c_exp:
            csv = df_f.to_csv(index=False).encode('utf-8')
            st.download_button("Ekspor CSV", csv, "penjualan_creatroka.csv", "text/csv")

        if show_upload:
            st.divider()
            self._handle_upload()