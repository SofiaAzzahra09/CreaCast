# # pages/data_buku_page.py
# import streamlit as st
# import pandas as pd

# class DataBukuPage:
#     def __init__(self, db_service):
#         self.db = db_service

#     def _render_kpi(self, df):
#         col1, col2, col3 = st.columns(3)
#         col1.metric("Total judul buku", len(df))
#         col2.metric("Stok kritis (<5)", len(df[df['stok'] < 5]))
#         col3.metric("Total kategori", df['kategori'].nunique())

#     def _render_toolbar(self):
#         col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1])
#         with col1:
#             search = st.text_input("", placeholder="Cari judul, penulis...", label_visibility="collapsed")
#         with col2:
#             kat = st.selectbox("", ["Semua kategori"] + self.db.get_kategori(), label_visibility="collapsed")
#         with col3:
#             stok_filter = st.selectbox("", ["Semua stok", "Kritis (<5)", "Menipis (<15)", "Aman (≥15)"], label_visibility="collapsed")
#         with col4:
#             tambah = st.button("+ Tambah", use_container_width=True, type="primary")
#         return search, kat, stok_filter, tambah

#     def _apply_filter(self, df, search, kat, stok_filter):
#         if search:
#             mask = df['judul'].str.contains(search, case=False) | df['penulis'].str.contains(search, case=False)
#             df = df[mask]
#         if kat != "Semua kategori":
#             df = df[df['kategori'] == kat]
#         if stok_filter == "Kritis (<5)":
#             df = df[df['stok'] < 5]
#         elif stok_filter == "Menipis (<15)":
#             df = df[(df['stok'] >= 5) & (df['stok'] < 15)]
#         elif stok_filter == "Aman (≥15)":
#             df = df[df['stok'] >= 15]
#         return df

#     @st.dialog("Tambah / Edit Buku")
#     def _form_dialog(self, buku=None):
#         judul    = st.text_input("Judul *", value=buku['judul'] if buku else "")
#         penulis  = st.text_input("Penulis *", value=buku['penulis'] if buku else "")
#         col1, col2 = st.columns(2)
#         with col1:
#             kategori = st.selectbox("Kategori", self.db.get_kategori())
#             harga    = st.number_input("Harga (Rp)", min_value=0, value=int(buku['harga']) if buku else 0)
#         with col2:
#             isbn   = st.text_input("ISBN", value=buku.get('isbn','') if buku else "")
#             stok   = st.number_input("Stok", min_value=0, value=int(buku['stok']) if buku else 0)
#         stok_min = st.number_input("Threshold stok minimum", min_value=0, value=15,
#                                     help="Dipakai untuk kalkulasi safety stock di model XGBoost")
#         if st.button("Simpan", type="primary", use_container_width=True):
#             self.db.save_buku(dict(judul=judul, penulis=penulis,
#                                    kategori=kategori, harga=harga,
#                                    isbn=isbn, stok=stok, stok_min=stok_min))
#             st.rerun()

#     def render(self):
#         st.title("Data produk buku")
#         st.caption("Master katalog buku — kelola, filter, dan pantau stok")

#         df = self.db.get_all_buku()
#         self._render_kpi(df)

#         search, kat, stok_filter, tambah = self._render_toolbar()
#         if tambah:
#             self._form_dialog()

#         df_filtered = self._apply_filter(df, search, kat, stok_filter)

#         st.dataframe(
#             df_filtered[['judul','penulis','kategori','harga','stok']],
#             use_container_width=True,
#             hide_index=True,
#             column_config={
#                 "harga": st.column_config.NumberColumn("Harga", format="Rp%d"),
#                 "stok":  st.column_config.NumberColumn("Stok"),
#             }
#         )

#         col_e, col_d = st.columns([1,5])
#         with col_e:
#             if st.button("Ekspor CSV"):
#                 csv = df_filtered.to_csv(index=False).encode('utf-8')
#                 st.download_button("Download", csv, "creatroka_buku.csv", "text/csv")


# pages/data_buku_page.py
import streamlit as st
import pandas as pd


class DataBukuPage:
    def __init__(self, db_service):
        self.db = db_service

    # ==================================================
    # KPI
    # ==================================================
    def _render_kpi(self, df):
        c1, c2, c3 = st.columns(3)
        c1.metric("Total judul buku", len(df))
        c2.metric("Stok kritis (<5)", len(df[df["stok"] < 5]))
        c3.metric("Total variasi", df["kategori"].nunique())

    # ==================================================
    # TOOLBAR
    # ==================================================
    def _render_toolbar(self):
        col1, col2, col3, col4, col5, col6 = st.columns(
            [3, 1.6, 1.6, 1.1, 1.1, 1.1]
        )

        with col1:
            search = st.text_input(
                "",
                placeholder="Cari judul, penulis...",
                label_visibility="collapsed"
            )

        with col2:
            kategori = st.selectbox(
                "",
                ["Semua buku", "Variasi A", "Variasi B"],
                label_visibility="collapsed"
            )

        with col3:
            stok = st.selectbox(
                "",
                ["Semua stok", "Kritis (<5)", "Menipis (<15)", "Aman (≥15)"],
                label_visibility="collapsed"
            )

        with col4:
            tambah = st.button("+ Tambah", use_container_width=True, type="primary")

        with col5:
            impor = st.button("📥 Import", use_container_width=True)

        with col6:
            ekspor = st.button("📤 Ekspor", use_container_width=True)

        return search, kategori, stok, tambah, impor, ekspor

    # ==================================================
    # FILTER
    # ==================================================
    def _apply_filter(self, df, search, kategori, stok):

        if search:
            mask = (
                df["judul"].str.contains(search, case=False, na=False)
                | df["penulis"].str.contains(search, case=False, na=False)
            )
            df = df[mask]

        if kategori != "Semua buku":
            df = df[df["kategori"] == kategori]

        if stok == "Kritis (<5)":
            df = df[df["stok"] < 5]

        elif stok == "Menipis (<15)":
            df = df[(df["stok"] >= 5) & (df["stok"] < 15)]

        elif stok == "Aman (≥15)":
            df = df[df["stok"] >= 15]

        return df

    # ==================================================
    # FORM TAMBAH
    # ==================================================
    @st.dialog("Tambah Buku")
    def _form_dialog(self):
        judul = st.text_input("Judul")
        penulis = st.text_input("Penulis")

        c1, c2 = st.columns(2)

        with c1:
            kategori = st.selectbox("Kategori", ["Variasi A", "Variasi B"])
            harga = st.number_input("Harga", min_value=0)

        with c2:
            isbn = st.text_input("ISBN")
            stok = st.number_input("Stok", min_value=0)

        if st.button("Simpan", use_container_width=True, type="primary"):
            self.db.save_buku(
                dict(
                    judul=judul,
                    penulis=penulis,
                    kategori=kategori,
                    harga=harga,
                    isbn=isbn,
                    stok=stok
                )
            )
            st.success("Data berhasil disimpan")
            st.rerun()

    # ==================================================
    # IMPORT EXCEL
    # ==================================================
    @st.dialog("Import File Excel")
    def _import_dialog(self):

        files = st.file_uploader(
            "Pilih file Excel",
            type=["xlsx", "xls"],
            accept_multiple_files=True
        )

        if files:

            st.success(f"{len(files)} file dipilih")

            gabung = []

            for file in files:
                try:
                    df = pd.read_excel(file)

                    st.markdown(f"### 📄 {file.name}")
                    st.dataframe(df.head(), use_container_width=True)

                    gabung.append(df)

                except Exception as e:
                    st.error(f"Gagal membaca {file.name}")

            if st.button("💾 Simpan Semua Data", use_container_width=True, type="primary"):

                total = 0

                for data in gabung:
                    for _, row in data.iterrows():

                        self.db.save_buku(
                            dict(
                                judul=row.get("judul", ""),
                                penulis=row.get("penulis", ""),
                                kategori=row.get("kategori", "Variasi A"),
                                harga=row.get("harga", 0),
                                isbn=row.get("isbn", ""),
                                stok=row.get("stok", 0)
                            )
                        )
                        total += 1

                st.success(f"{total} data berhasil diimport")
                st.rerun()

    # ==================================================
    # PAGE
    # ==================================================
    def render(self):

        st.title("Data produk buku")
        st.caption("Master katalog buku")

        df = self.db.get_all_buku()

        self._render_kpi(df)

        (
            search,
            kategori,
            stok,
            tambah,
            impor,
            ekspor
        ) = self._render_toolbar()

        if tambah:
            self._form_dialog()

        if impor:
            self._import_dialog()

        df_filtered = self._apply_filter(df, search, kategori, stok)

        if ekspor:
            csv = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download CSV",
                csv,
                "data_buku.csv",
                "text/csv",
                use_container_width=True
            )

        st.dataframe(
            df_filtered[
                ["judul", "penulis", "kategori", "harga", "stok"]
            ],
            use_container_width=True,
            hide_index=True
        )