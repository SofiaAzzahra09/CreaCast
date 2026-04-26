# services/feature_engineering.py
# import pandas as pd
# import numpy as np

# class FeatureEngineer:
#     def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
#         df = df.sort_values(['id_buku', 'tahun', 'minggu_ke']).copy()

#         # Fitur lag — penjualan N minggu yang lalu
#         for lag in [1, 2, 3, 4]:
#             df[f'lag_{lag}'] = df.groupby('id_buku')['jumlah_terjual'].shift(lag)

#         # Rolling statistics — rata-rata & std bergulir
#         grp = df.groupby('id_buku')['jumlah_terjual']
#         df['rolling_mean_4']  = grp.shift(1).rolling(4).mean().reset_index(level=0, drop=True)
#         df['rolling_mean_8']  = grp.shift(1).rolling(8).mean().reset_index(level=0, drop=True)
#         df['rolling_std_4']   = grp.shift(1).rolling(4).std().reset_index(level=0, drop=True)

#         # Fitur kalender
#         df['minggu_ke_sin'] = np.sin(2 * np.pi * df['minggu_ke'] / 52)
#         df['minggu_ke_cos'] = np.cos(2 * np.pi * df['minggu_ke'] / 52)

#         # Encode kategori
#         df['kategori_enc'] = pd.Categorical(df['kategori']).codes

#         # Hapus baris dengan NaN dari lag
#         df = df.dropna()
#         return df

import pandas as pd
import numpy as np

class FeatureEngineer:

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        # =============================
        # SORT DATA
        # =============================
        df = df.sort_values(['variasi_encoded', 'waktu_pesanan_dibuat'])

        # =============================
        # AGREGASI MINGGUAN
        # =============================
        df['waktu_pesanan_dibuat'] = pd.to_datetime(df['waktu_pesanan_dibuat'])

        weekly = (
            df
            .set_index('waktu_pesanan_dibuat')
            .groupby(['nama_variasi', 'variasi_encoded'])
            .resample('W')
            .agg({
                'net_jumlah': 'sum',
                'persen_diskon': 'mean',
                'is_weekend': 'sum',
                'is_holiday': 'sum',
                'is_ramadhan': 'sum',
                'ramadhan_week': 'max',
                'product_age_week': 'max'
            })
            .reset_index()
        )

        # =============================
        # LAG FEATURE (SESUAI ACF)
        # =============================
        weekly['lag_1'] = weekly.groupby('variasi_encoded')['net_jumlah'].shift(1)
        weekly['lag_2'] = weekly.groupby('variasi_encoded')['net_jumlah'].shift(2)

        # =============================
        # ROLLING MEAN 2
        # =============================
        weekly['rolling_mean_2'] = (
            weekly.groupby('variasi_encoded')['net_jumlah']
            .shift(1)
            .rolling(2)
            .mean()
            .reset_index(level=0, drop=True)
        )

        # =============================
        # DROP NA
        # =============================
        weekly = weekly.dropna()

        return weekly