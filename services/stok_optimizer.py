# services/stock_optimizer.py
import math
import numpy as np
import pandas as pd

class StockOptimizer:
    """
    Menghitung safety stock, reorder point, dan jumlah restock
    berdasarkan output prediksi XGBoost.
    
    Referensi: Silver, Pyke & Thomas (2017) — Inventory and Production Management
    """

    Z_TABLE = {
        80: 0.84, 85: 1.04, 90: 1.28, 91: 1.34, 92: 1.41,
        93: 1.48, 94: 1.56, 95: 1.65, 96: 1.75, 97: 1.88,
        98: 2.05, 99: 2.33
    }

    def __init__(self, lead_time_days: int = 7, service_level: int = 95):
        self.lead_time = lead_time_days
        self.service_level = service_level
        self.z = self.Z_TABLE.get(service_level, 1.65)

    def hitung_safety_stock(self, std_demand_mingguan: float) -> int:
        """
        Safety Stock = Z × σ_demand × √(lead_time / 7)
        
        σ_demand: standar deviasi permintaan mingguan (dari data historis)
        Z       : z-score sesuai service level yang dipilih
        """
        ss = self.z * std_demand_mingguan * math.sqrt(self.lead_time / 7)
        return math.ceil(ss)

    def hitung_reorder_point(self,
                              demand_prediksi: float,
                              std_demand: float) -> int:
        """
        ROP = (demand_prediksi / 7) × lead_time + safety_stock
        
        Demand prediksi berasal langsung dari output XGBoost
        """
        daily_demand = demand_prediksi / 7
        ss = self.hitung_safety_stock(std_demand)
        rop = math.ceil(daily_demand * self.lead_time + ss)
        return rop

    def hitung_restock(self,
                        stok_sekarang: int,
                        demand_prediksi: float,
                        std_demand: float) -> dict:
        # =============================
        # HANDLE NULL / NAN (WAJIB)
        # =============================
        demand_prediksi = demand_prediksi if pd.notna(demand_prediksi) else 0
        std_demand = std_demand if pd.notna(std_demand) else 0

        
        """
        Menghitung semua komponen rekomendasi stok untuk satu buku.
        Mengembalikan dict lengkap untuk ditampilkan di UI.
        """
        ss  = self.hitung_safety_stock(std_demand)
        rop = self.hitung_reorder_point(demand_prediksi, std_demand)

        # Jumlah restock = yang dibutuhkan untuk memenuhi prediksi demand
        # + buffer sampai reorder point berikutnya
        jumlah_restock = max(0, rop + demand_prediksi - stok_sekarang)

        if stok_sekarang < ss:
            status = 'kritis'
        elif stok_sekarang < rop:
            status = 'menipis'
        else:
            status = 'aman'

        if demand_prediksi == 0:
            cukup_minggu = 0
        else:
            cukup_minggu = round(stok_sekarang / (demand_prediksi / 7), 1)

        return {
            'safety_stock':     ss,
            'reorder_point':    rop,
            'jumlah_restock':   math.ceil(jumlah_restock),
            'status':           status,
            'cukup_minggu':     cukup_minggu
            # 'cukup_minggu':     round(stok_sekarang / (demand_prediksi / 7), 1)
        }

    def hitung_semua(self,
                      df_buku: pd.DataFrame,
                      df_prediksi: pd.DataFrame,
                      df_historis: pd.DataFrame) -> pd.DataFrame:
        """
        Menghitung rekomendasi stok untuk semua buku sekaligus.
        
        df_buku    : kolom [id_buku, judul, stok, kategori]
        df_prediksi: output XGBoost — kolom [id_buku, demand_prediksi]
        df_historis: kolom [id_buku, minggu_ke, jumlah_terjual]
        """
        # Hitung std demand per buku dari data historis
        std_per_buku = (df_historis
                        .groupby('id_buku')['jumlah_terjual']
                        .std()
                        .reset_index()
                        .rename(columns={'jumlah_terjual': 'std_demand'}))

        df = (df_buku
              .merge(df_prediksi, on='id_buku', how='left')
              .merge(std_per_buku, on='id_buku', how='left'))

        results = []
        # for _, row in df.iterrows():
        #     r = self.hitung_restock(
        #         stok_sekarang=row['stok'],
        #         demand_prediksi=row['demand_prediksi'],
        #         std_demand=row['std_demand']
        #     )
        #     results.append({**row.to_dict(), **r})

        for _, row in df.iterrows():
            demand_prediksi = row['demand_prediksi']
            std_demand = row['std_demand']

            # HANDLE NULL / NaN
            demand_prediksi = demand_prediksi if pd.notna(demand_prediksi) else 0
            std_demand = std_demand if pd.notna(std_demand) else 0

            r = self.hitung_restock(
                stok_sekarang=row['stok'],
                demand_prediksi=demand_prediksi,
                std_demand=std_demand
            )

            results.append({**row.to_dict(), **r})

        return (pd.DataFrame(results)
                .sort_values('status', key=lambda s: s.map({'kritis':0,'menipis':1,'aman':2}))
                .reset_index(drop=True))