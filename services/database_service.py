# services/database_service.py

import sqlite3
import pandas as pd
import os
from config import DATABASE_PATH


class DatabaseService:

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    # ==================================================
    # INIT DB
    # ==================================================
    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with open("database/schema.sql", "r", encoding="utf-8") as f:
            schema = f.read()

        with self._connect() as conn:
            conn.executescript(schema)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==================================================
    # BASIC QUERY
    # ==================================================
    def execute(self, query, params=()):
        with self._connect() as conn:
            conn.execute(query, params)
            conn.commit()

    def fetchdf(self, query, params=()):
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def fetchone(self, query, params=()):
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    # ==================================================
    # BUKU
    # ==================================================
    def get_all_buku(self):
        return self.fetchdf("""
            SELECT *
            FROM buku
            ORDER BY id DESC
        """)

    
    # ==================================================
    # PREDIKSI
    # ==================================================

    def get_latest_prediction(self):
        try:
            df = self.fetchdf("""
                SELECT 
                    id_buku, 
                    prediksi AS demand_prediksi
                FROM prediksi
                ORDER BY created_at DESC
            """)

            if df.empty:
                return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

            return df

        except Exception:
            return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

    # defget_latest_prediction(self):
    #     """
    #     Ambil hasil prediksi terbaru.
    #     Format wajib:
    #     [id_buku, demand_prediksi]
    #     """

    #     try:
    #         df = self.fetchdf("""
    #             SELECT id_buku, demand_prediksi
    #             FROM prediksi
    #             ORDER BY created_at DESC
    #         """)

    #         if df.empty:
    #             return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

    #         return df

    #     except Exception:
    #         # fallback kalau tabel belum ada
    #         return pd.DataFrame(columns=["id_buku", "demand_prediksi"])
    
    def get_kategori(self):
        df = self.fetchdf("""
            SELECT DISTINCT kategori
            FROM buku
            ORDER BY kategori
        """)
        return df["kategori"].tolist()

    def save_buku(self, data):

        # default jika kosong
        judul = data.get("judul", "-")
        kategori = data.get("kategori", "-")
        penulis = data.get("penulis", "-")
        penerbit = data.get("penerbit", "-")
        isbn = data.get("isbn", "-")
        harga = int(data.get("harga", 0))
        stok = int(data.get("stok", 0))
        stok_min = int(data.get("stok_min", 15))

        # cek produk sudah ada / belum
        old = self.fetchone("""
            SELECT id, stok
            FROM buku
            WHERE judul = ?
            AND kategori = ?
        """, (judul, kategori))

        # kalau ada = update stok
        if old:
            self.execute("""
                UPDATE buku
                SET
                    harga = ?,
                    stok = stok + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                harga,
                stok,
                old["id"]
            ))

        # kalau belum ada = insert baru
        else:
            self.execute("""
                INSERT INTO buku (
                    judul,
                    kategori,
                    penulis,
                    penerbit,
                    isbn,
                    harga,
                    stok,
                    stok_min
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                judul,
                kategori,
                penulis,
                penerbit,
                isbn,
                harga,
                stok,
                stok_min
            ))

    def hapus_buku(self, id_buku):
        self.execute(
            "DELETE FROM buku WHERE id = ?",
            (id_buku,)
        )

    def update_stok(self, id_buku, stok_baru):
        self.execute("""
            UPDATE buku
            SET stok = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (stok_baru, id_buku))


    # ==================================================
    # PENJUALAN (DATA HISTORIS)
    # ==================================================
    def get_all_penjualan(self):
        """
        Ambil semua data historis penjualan
        Format:
        [id_buku, minggu_ke, jumlah_terjual]
        """
        try:
            df = self.fetchdf("""
                SELECT 
                    id_buku,
                    minggu_ke,
                    jumlah_terjual
                FROM penjualan
                ORDER BY tahun, minggu_ke
            """)

            if df.empty:
                return pd.DataFrame(columns=["id_buku", "minggu_ke", "jumlah_terjual"])

            return df

        except Exception:
            return pd.DataFrame(columns=["id_buku", "minggu_ke", "jumlah_terjual"])
    