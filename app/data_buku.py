# app/data_buku.py

import streamlit as st
import pandas as pd
import re
import os
from components.table import TableComponent

def load_html_template(filename):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base_dir, "components", filename)

    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class DataBukuPage:
    def __init__(self, db_service):
        self.db = db_service

    def _set_notification(self, message, notif_type="success"):
        st.session_state["notif_message"] = message
        st.session_state["notif_type"] = notif_type

    def _show_notification(self):
        if "notif_message" in st.session_state:

            msg = st.session_state["notif_message"]
            notif_type = st.session_state.get("notif_type", "success")

            if notif_type == "success":
                st.success(msg)
            elif notif_type == "warning":
                st.warning(msg)
            elif notif_type == "error":
                st.error(msg)

            del st.session_state["notif_message"]
            del st.session_state["notif_type"]

    # ==================================================
    # KPI
    # ==================================================
    def _render_kpi(self, df):

        if df.empty:
            total_produk = 0
            total_variasi = 0
            rata_harga = 0
        else:
            total_produk = df["kategori"].nunique()
            total_variasi = df["judul"].nunique()
            rata_harga = int(df["harga"].mean())

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Produk", total_produk)
        c2.metric("Total Variasi", total_variasi)
        c3.metric("Rata-rata Harga", f"Rp {rata_harga:,}".replace(",", "."))
    
    # ==================================================
    # TOOLBAR
    # ==================================================
    def _render_toolbar(self):

        c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])

        with c1:
            search = st.text_input(
                "",
                placeholder="Cari judul variasi, nama produk, stok, harga...",
                label_visibility="collapsed"
            )

        with c2:
            tambah = st.button(
                "Tambah",
                type="primary",
                use_container_width=True
            )

        with c3:
            impor = st.button(
                "Import",
                type="secondary",
                use_container_width=True
            )

        with c4:
            export = st.button(
                "Export",
                type="secondary",
                use_container_width=True
            )

        with c5:
            st.markdown('<div class="danger-btn">', unsafe_allow_html=True)

            hapus_semua = st.button(
                "Reset",
                use_container_width=True
            )

            st.markdown('</div>', unsafe_allow_html=True)

        return search, tambah, impor, export, hapus_semua

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


    def _to_harga(self, val):

        if pd.isna(val):
            return 0

        if isinstance(val, (int, float)):
            num = int(val)

            if num < 1000 and num > 0:
                num *= 1000

            return num

        txt = str(val).strip()
        txt = re.sub(r"[^0-9]", "", txt)

        if not txt:
            return 0

        num = int(txt)

        if num < 1000:
            num *= 1000

        return num
    # ==================================================
    # FILTER
    # ==================================================
    def _apply_filter(self, df, search):

        if df.empty:
            return df

        if search:

            keyword = str(search).lower()

            df = df[
                df["judul"].astype(str).str.lower().str.contains(keyword, na=False)
                |
                df["kategori"].astype(str).str.lower().str.contains(keyword, na=False)
                |
                df["stok"].astype(str).str.contains(keyword, na=False)
                |
                df["harga"].astype(str).str.contains(keyword, na=False)
            ]

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

        if st.button("Simpan", use_container_width=True):

            self.db.save_buku({
                "judul": judul if judul else "-",
                "kategori": kategori if kategori else "-",
                "harga": harga,
                "stok": stok
            })

            self._set_notification("Data berhasil ditambah")
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

        if st.button("Update", type="primary", use_container_width=True):

            self.db.save_buku({
                "id": row["id"],
                "judul": judul,
                "kategori": kategori,
                "harga": harga,
                "stok": stok
            })

            self._set_notification("Data berhasil diupdate")
            st.rerun()

    @st.dialog("Konfirmasi Hapus")
    def _confirm_delete(self, row):

        st.warning(f"Yakin hapus buku: {row['judul']} ?")

        c1, c2 = st.columns(2)

        if c1.button("Batal", type="secondary", use_container_width=True):
            st.rerun()

        with c2:
            st.markdown(
                '<div class="danger-btn">',
                unsafe_allow_html=True
            )

            hapus = st.button(
                "Hapus",
                use_container_width=True
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        if hapus:
            self.db.hapus_buku(row["id"])
            self._set_notification("Data dihapus")
            st.rerun()

    @st.dialog("Hapus Semua Data")
    def _confirm_delete_all(self):

        st.warning("Yakin ingin menghapus semua data buku?")

        c1, c2 = st.columns(2)

        if c1.button("Batal", type="secondary", use_container_width=True):
            st.rerun()

        
        with c2:
            st.markdown(
                '<div class="danger-btn">',
                unsafe_allow_html=True
            )

            hapus_semua_btn = st.button(
                "Hapus Semua",
                use_container_width=True
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True
            )

        if hapus_semua_btn:
            self.db.hapus_semua_buku()
            self._set_notification("Semua data berhasil dihapus")
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

        if st.button("Simpan", type="primary", use_container_width=True):
            total = 0
            missing_variasi = 0

            for df in data_all:
                for _, row in df.iterrows():

                    judul = str(self._get_value(row, ["nama variasi"], "")).strip()

                    if not judul:
                        missing_variasi += 1

                    self.db.save_buku({
                        "judul": judul,
                        "kategori": str(self._get_value(row, ["nama produk"], "-")),
                        "harga": self._to_harga(
                            self._get_value(row, ["harga awal"], 0)
                        ),
                        "stok": 0
                    })

                    total += 1

            msg = f"{total} data berhasil diimport"

            if missing_variasi > 0:
                msg += f" ({missing_variasi} data tanpa variasi)"

            notif_type = "warning" if missing_variasi > 0 else "success"

            self._set_notification(msg, notif_type)
            st.rerun()

    # ==================================================
    # TABLE
    # ==================================================
    def _render_table(self, df):
        st.markdown("### Daftar Buku")

        if df.empty:
            st.info("Belum ada data buku.")
            return

        # Ambil kolom yang diperlukan saja untuk display
        # Kita sertakan 'id' tapi nanti kita bisa filter agar tidak muncul di header
        df_display = df[["judul", "kategori", "harga", "stok"]].copy()

        # Format Kolom untuk tampilan User
        df_display = df_display.rename(columns={
            "judul": "Judul Variasi",
            "kategori": "Nama Produk",
            "harga": "Harga",
            "stok": "Stok"
        })

        df_display["Harga"] = df_display["Harga"].apply(
            lambda x: f"Rp {int(x):,}".replace(",", ".")
        )

        # Panggil komponen (Akan otomatis membuat kolom sesuai df_display)
        TableComponent.render(
            df_display,
            show_index=True,
            actions=[
                {"callback": self._edit_dialog},
                {"callback": self._confirm_delete}
            ]
        )

    # ==================================================
    # PAGE
    # ==================================================
    def render(self):

        st.title("Data Buku")
        st.caption("Master data produk buku")
        self._show_notification()

        df = self.db.get_all_buku()

        self._render_kpi(df)

        search, tambah, impor, export, hapus_semua = self._render_toolbar()

        if tambah:
            self._tambah_dialog()

        if impor:
            self._import_dialog()

        if hapus_semua:
            self._confirm_delete_all()

        df = self._apply_filter(df, search)

        if export and not df.empty:

            csv = df.to_csv(index=False).encode("utf-8")

            downloaded = st.download_button(
                "⬇ Download CSV",
                csv,
                "data_buku.csv",
                "text/csv",
                use_container_width=True
            )

            if downloaded:
                self._set_notification("Export berhasil")
                st.rerun()

        elif export and df.empty:
            self._set_notification("Belum ada data untuk diexport.", "warning")
            st.rerun()

        self._render_table(df)