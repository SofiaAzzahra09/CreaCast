# app/data_buku_page.py

import streamlit as st
import pandas as pd
import re


class DataBukuPage:
    def __init__(self, db_service):
        self.db = db_service

    # ==================================================
    # KPI
    # ==================================================
    def _render_kpi(self, df):

        total_produk = len(df) if not df.empty else 0
        stok_kritis = len(df[df["stok"] < 5]) if not df.empty else 0
        total_variasi = df["kategori"].nunique() if not df.empty else 0

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Produk", total_produk)
        c2.metric("Stok Kritis (<5)", stok_kritis)
        c3.metric("Total Variasi", total_variasi)

    # ==================================================
    # TOOLBAR
    # ==================================================
    def _render_toolbar(self):

        kategori_db = self.db.get_kategori()
        kategori_list = ["Semua"] + kategori_db if kategori_db else ["Semua"]

        c1, c2, c3, c4, c5, c6 = st.columns([3, 1.5, 1.5, 1, 1, 1])

        with c1:
            search = st.text_input(
                "",
                placeholder="Cari judul buku...",
                label_visibility="collapsed"
            )

        with c2:
            kategori = st.selectbox(
                "",
                kategori_list,
                label_visibility="collapsed"
            )

        with c3:
            stok = st.selectbox(
                "",
                ["Semua stok", "Kritis (<5)", "Menipis (<15)", "Aman (≥15)"],
                label_visibility="collapsed"
            )

        with c4:
            tambah = st.button("➕ Tambah", use_container_width=True)

        with c5:
            impor = st.button("📥 Import", use_container_width=True)

        with c6:
            export = st.button("📤 Export", use_container_width=True)

        return search, kategori, stok, tambah, impor, export

    # ==================================================
    # NORMALISASI HEADER
    # ==================================================
    def _normalize_columns(self, df):
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace("\n", " ", regex=False)
        )
        return df

    # ==================================================
    # GET VALUE
    # ==================================================
    def _get_value(self, row, cols, default="-"):

        for col in cols:
            if col in row.index:
                val = row[col]

                if pd.isna(val) or str(val).strip() == "":
                    return default

                return val

        return default

    # ==================================================
    # TO INT
    # ==================================================
    def _to_int(self, val):

        if pd.isna(val):
            return 0

        txt = str(val)
        txt = re.sub(r"[^0-9]", "", txt)

        return int(txt) if txt else 0

    # ==================================================
    # FILTER
    # ==================================================
    def _apply_filter(self, df, search, kategori, stok):

        if df.empty:
            return df

        if search:
            df = df[
                df["judul"].str.contains(search, case=False, na=False)
            ]

        if kategori != "Semua":
            df = df[df["kategori"] == kategori]

        if stok == "Kritis (<5)":
            df = df[df["stok"] < 5]

        elif stok == "Menipis (<15)":
            df = df[(df["stok"] >= 5) & (df["stok"] < 15)]

        elif stok == "Aman (≥15)":
            df = df[df["stok"] >= 15]

        return df

    # ==================================================
    # TAMBAH
    # ==================================================
    @st.dialog("Tambah Buku")
    def _tambah_dialog(self):

        judul = st.text_input("Judul")
        kategori = st.text_input("Variasi")
        harga = st.number_input("Harga", min_value=0)
        stok = st.number_input("Stok", min_value=0)

        if st.button("💾 Simpan", use_container_width=True):

            self.db.save_buku({
                "judul": judul if judul else "-",
                "kategori": kategori if kategori else "-",
                "harga": harga,
                "stok": stok
            })

            st.success("Data berhasil ditambah")
            st.rerun()

    # ==================================================
    # EDIT
    # ==================================================
    @st.dialog("Edit Buku")
    def _edit_dialog(self, row):

        judul = st.text_input("Judul", value=row["judul"])
        kategori = st.text_input("Variasi", value=row["kategori"])
        harga = st.number_input("Harga", min_value=0, value=int(row["harga"]))
        stok = st.number_input("Stok", min_value=0, value=int(row["stok"]))

        if st.button("💾 Update", use_container_width=True):

            self.db.save_buku({
                "id": row["id"],
                "judul": judul,
                "kategori": kategori,
                "harga": harga,
                "stok": stok
            })

            st.success("Data berhasil diupdate")
            st.rerun()

    # ==================================================
    # IMPORT
    # ==================================================
    @st.dialog("Import Excel")
    def _import_dialog(self):

        files = st.file_uploader(
            "Upload file Excel",
            type=["xlsx", "xls"],
            accept_multiple_files=True
        )

        if not files:
            st.info("Belum ada file dipilih.")
            return

        data_all = []

        for file in files:
            try:
                df = pd.read_excel(file)
                df = self._normalize_columns(df)

                st.success(f"{file.name} berhasil dibaca")
                st.dataframe(df.head(3), use_container_width=True)

                data_all.append(df)

            except:
                st.error(f"Gagal membaca {file.name}")

        if st.button("💾 Simpan Semua", use_container_width=True):

            total = 0

            for df in data_all:
                for _, row in df.iterrows():

                    self.db.save_buku({
                        "judul": str(self._get_value(row, ["nama produk"], "-")),
                        "kategori": str(self._get_value(row, ["nama variasi"], "-")),
                        "harga": self._to_int(self._get_value(row, ["harga awal"], 0)),
                        "stok": self._to_int(self._get_value(row, ["jumlah"], 0))
                    })

                    total += 1

            st.success(f"{total} data berhasil diimport")
            st.rerun()

    # ==================================================
    # TABLE
    # ==================================================
    def _render_table(self, df):

        st.markdown("### 📚 Daftar Buku")

        if df.empty:
            st.info("Belum ada data buku.")
            return

        head = st.columns([0.7, 4, 2, 1.5, 1, 1, 1])

        head[0].markdown("**No**")
        head[1].markdown("**Judul**")
        head[2].markdown("**Variasi**")
        head[3].markdown("**Harga**")
        head[4].markdown("**Stok**")
        head[5].markdown("**Edit**")
        head[6].markdown("**Hapus**")

        no = 1

        for _, row in df.iterrows():

            col = st.columns([0.7, 4, 2, 1.5, 1, 1, 1])

            col[0].write(no)
            col[1].write(row["judul"])
            col[2].write(row["kategori"])
            col[3].write(f"Rp {int(row['harga']):,}".replace(",", "."))
            col[4].write(int(row["stok"]))

            if col[5].button("✏️", key=f"edit_{row['id']}"):
                self._edit_dialog(row)

            if col[6].button("🗑️", key=f"hapus_{row['id']}"):
                self.db.hapus_buku(row["id"])
                st.success("Data dihapus")
                st.rerun()

            no += 1

    # ==================================================
    # PAGE
    # ==================================================
    def render(self):

        st.title("Data Buku")
        st.caption("Master data produk buku")

        df = self.db.get_all_buku()

        self._render_kpi(df)

        search, kategori, stok, tambah, impor, export = self._render_toolbar()

        if tambah:
            self._tambah_dialog()

        if impor:
            self._import_dialog()

        df = self._apply_filter(df, search, kategori, stok)

        if export and not df.empty:

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "⬇ Download CSV",
                csv,
                "data_buku.csv",
                "text/csv",
                use_container_width=True
            )

        elif export and df.empty:
            st.warning("Belum ada data untuk diexport.")

        self._render_table(df)