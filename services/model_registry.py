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

        self.db.execute("""
            INSERT INTO model_registry
                (versi, jumlah_data, rmse, mae, r2, mape,
                 hyperparameter, file_path, status, catatan)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (versi,
              metrics.get('n_data', 0),
              metrics['rmse'], metrics['mae'],
              metrics['r2'],   metrics['mape'],
              json.dumps(params), file_path,
              'archive', catatan))

        return versi

    def activate(self, versi: str):
        """Set satu versi sebagai active, arsipkan semua yang lain."""
        self.db.execute("UPDATE model_registry SET status='archive'")
        self.db.execute(
            "UPDATE model_registry SET status='active' WHERE versi=?", (versi,))

    def load_active(self):
        """Load model yang sedang aktif dari disk."""
        row = self.db.fetchone(
            "SELECT file_path FROM model_registry WHERE status='active'")
        if not row:
            raise FileNotFoundError("Tidak ada model aktif di registry.")
        with open(row['file_path'], 'rb') as f:
            return pickle.load(f)

    def get_all(self) -> pd.DataFrame:
        return self.db.fetchdf(
            "SELECT * FROM model_registry ORDER BY id DESC")

    def delete(self, versi: str):
        row = self.db.fetchone(
            "SELECT status, file_path FROM model_registry WHERE versi=?", (versi,))
        if row['status'] == 'active':
            raise ValueError("Tidak bisa menghapus model aktif.")
        if os.path.exists(row['file_path']):
            os.remove(row['file_path'])
        self.db.execute(
            "DELETE FROM model_registry WHERE versi=?", (versi,))

    def _next_version(self) -> str:
        row = self.db.fetchone(
            "SELECT MAX(CAST(SUBSTR(versi,2) AS INTEGER)) AS n FROM model_registry")
        n = (row['n'] or 0) + 1
        return f"v{n}"