# route/stok_optimizer.py
import pandas as pd
import numpy as np


class StockOptimizer:

    def __init__(self):
        pass

    # ==================================================
    # HITUNG RESTOCK
    # ==================================================
    def hitung_restock(
        self,
        stok,
        demand_prediksi
    ):

        restock = max(
            0,
            int(np.ceil(demand_prediksi - stok))
        )

        return restock

    # ==================================================
    # STATUS
    # ==================================================
    def get_status(
        self,
        stok,
        demand_prediksi
    ):

        selisih = demand_prediksi - stok

        if selisih > 10:
            return "Restock Tinggi"

        elif selisih > 0:
            return "Perlu Dipantau"

        else:
            return "Stok Aman"

    # ==================================================
    # PROSES SEMUA DATA
    # ==================================================
    def hitung_semua(
        self,
        df_buku,
        df_prediksi
    ):

        if df_buku.empty or df_prediksi.empty:
            return pd.DataFrame()

        hasil = pd.merge(
            df_buku,
            df_prediksi,
            left_on="id",
            right_on="id_buku",
            how="inner"
        )

        hasil["restock"] = hasil.apply(
            lambda row: self.hitung_restock(
                row["stok"],
                row["demand_prediksi"]
            ),
            axis=1
        )

        hasil["status"] = hasil.apply(
            lambda row: self.get_status(
                row["stok"],
                row["demand_prediksi"]
            ),
            axis=1
        )

        return hasil