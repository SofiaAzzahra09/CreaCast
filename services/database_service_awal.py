# services/database_service.py
import sqlite3
import pandas as pd
from config import DATABASE_PATH
import os

class DatabaseService:
    """
    Satu-satunya class yang boleh menyentuh database.
    Semua halaman dan service lain harus lewat sini.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open("database/schema.sql") as f:
            schema = f.read()
        with self._connect() as conn:
            conn.executescript(schema)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, query: str, params: tuple = ()):
        with self._connect() as conn:
            conn.execute(query, params)
            conn.commit()

    def fetchdf(self, query: str, params: tuple = ()) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    # ── Buku ──────────────────────────────────────────────────────────
    def get_all_buku(self) -> pd.DataFrame:
        return self.fetchdf("SELECT * FROM buku ORDER BY judul")

    def get_kategori(self) -> list:
        df = self.fetchdf("SELECT DISTINCT kategori FROM buku ORDER BY kategori")
        return df['kategori'].tolist()

    def save_buku(self, data: dict):
        if data.get('id'):
            self.execute("""
                UPDATE buku SET judul=?,penulis=?,penerbit=?,kategori=?,
                isbn=?,harga=?,stok=?,stok_min=?,updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (data['judul'], data['penulis'], data.get('penerbit'),
                  data['kategori'], data.get('isbn'), data['harga'],
                  data['stok'], data.get('stok_min', 15), data['id']))
        else:
            self.execute("""
                INSERT INTO buku (judul,penulis,penerbit,kategori,isbn,harga,stok,stok_min)
                VALUES (?,?,?,?,?,?,?,?)
            """, (data['judul'], data['penulis'], data.get('penerbit'),
                  data['kategori'], data.get('isbn'), data['harga'],
                  data['stok'], data.get('stok_min', 15)))

    def hapus_buku(self, id_buku: int):
        self.execute("DELETE FROM buku WHERE id=?", (id_buku,))

    def update_stok(self, id_buku: int, stok_baru: int):
        self.execute(
            "UPDATE buku SET stok=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (stok_baru, id_buku))

    # ── Penjualan ─────────────────────────────────────────────────────
    def get_all_penjualan(self, weeks: int = None) -> pd.DataFrame:
        if weeks:
            return self.fetchdf("""
                SELECT p.*, b.judul, b.kategori FROM penjualan p
                JOIN buku b ON b.id = p.id_buku
                ORDER BY p.tahun DESC, p.minggu_ke DESC
                LIMIT ?
            """, (weeks * 50,))
        return self.fetchdf("""
            SELECT p.*, b.judul, b.kategori FROM penjualan p
            JOIN buku b ON b.id = p.id_buku
            ORDER BY p.tahun DESC, p.minggu_ke DESC
        """)

    def insert_penjualan_bulk(self, df: pd.DataFrame):
        with self._connect() as conn:
            df.to_sql('penjualan', conn, if_exists='append', index=False)

    # ── Prediksi ──────────────────────────────────────────────────────
    def save_prediction(self, predictions: list,
                         minggu_base: int, tahun: int,
                         model_versi: str = 'v3'):
        for i, pred in enumerate(predictions):
            self.execute("""
                INSERT INTO prediksi (minggu_ke, tahun, prediksi, model_versi)
                VALUES (?,?,?,?)
            """, (minggu_base + i + 1, tahun, pred, model_versi))

    def get_latest_prediction(self) -> float:
        row = self.fetchone("""
            SELECT prediksi FROM prediksi
            ORDER BY created_at DESC LIMIT 1
        """)
        return row['prediksi'] if row else 0

    # ── Model registry ────────────────────────────────────────────────
    def get_model_registry(self) -> pd.DataFrame:
        return self.fetchdf(
            "SELECT * FROM model_registry ORDER BY id DESC")

    # ── Laporan history ───────────────────────────────────────────────
    def get_laporan_history(self) -> pd.DataFrame:
        return self.fetchdf(
            "SELECT * FROM laporan_history ORDER BY created_at DESC")

    def save_laporan_history(self, nama: str, format: str, ukuran_kb: int):
        self.execute("""
            INSERT INTO laporan_history (nama, format, ukuran_kb)
            VALUES (?,?,?)
        """, (nama, format, ukuran_kb))