# services/model_registry.py
import json, pickle, os
import pandas as pd
from datetime import datetime

class ModelRegistry:
    """
    Mengelola versi model XGBoost: simpan, load, aktifkan, hapus.
    Satu-satunya class yang boleh menyentuh file .pkl dan tabel model_registry.
    """

    def __init__(self, db_service, model_dir: str = "model/"):
        self.db = db_service
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

    def save(self, model, metrics: dict, params: dict, catatan: str = "") -> str:
        """Simpan model baru ke registry, otomatis beri nomor versi."""
        versi = self._next_version()
        file_path = f"{self.model_dir}xgboost_creatroka_{versi}.pkl"

        with open(file_path, 'wb') as f:
            pickle.dump(model, f)

        # Cek apakah ini model pertama
        is_first_model = self.get_all().empty
        
        # PERBAIKAN: Gunakan 'aktif' dan 'nonaktif'
        status_awal = 'aktif' if is_first_model else 'nonaktif'

        self.db.execute("""
            INSERT INTO model_registry 
                (versi, jumlah_data, mse, rmse, mae, r2, 
                 hyperparameter, file_path, status, catatan)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            versi,
            metrics.get('n_data', 0),
            metrics['mse'],
            metrics['rmse'],
            metrics['mae'],
            metrics['r2'],
            json.dumps(params),
            file_path,
            status_awal,
            catatan
        ))

        return versi

    def activate(self, versi: str):
        # nonaktifkan semua
        self.db.execute(
            "UPDATE model_registry SET status='nonaktif'"
        )

        # aktifkan versi dipilih
        self.db.execute(
            "UPDATE model_registry SET status='aktif' WHERE versi=?",
            (versi,)
        )

        return True

    def load_active(self):
        """Load model yang sedang aktif dari disk."""
        # PERBAIKAN: Sesuaikan query dengan status 'aktif'
        row = self.db.fetchone(
            "SELECT file_path FROM model_registry WHERE status='aktif'")
        if not row:
            raise FileNotFoundError("Tidak ada model aktif di registry.")
        with open(row['file_path'], 'rb') as f:
            return pickle.load(f)

    def get_all(self) -> pd.DataFrame:
        return self.db.fetchdf(
            "SELECT * FROM model_registry ORDER BY id DESC")

    def delete(self, versi: str):
        row = self.db.fetchone(
            "SELECT status, file_path FROM model_registry WHERE versi=?", (versi,)
        )

        if not row:
            raise ValueError("Model tidak ditemukan.")

        if row['status'].strip().lower() == 'aktif':
            raise ValueError("Tidak bisa menghapus model aktif.")

        if os.path.exists(row['file_path']):
            os.remove(row['file_path'])

        self.db.execute(
            "DELETE FROM model_registry WHERE versi=?", (versi,)
        )

    def _next_version(self) -> str:
        row = self.db.fetchone(
            "SELECT MAX(CAST(SUBSTR(versi,2) AS INTEGER)) AS n FROM model_registry")
        n = (row['n'] or 0) + 1
        return f"v{n}"