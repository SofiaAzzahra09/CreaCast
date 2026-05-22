# import xgboost as xgb
# import pandas as pd
# import numpy as np
# import pickle, math

# from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# class XGBoostService:
#     def __init__(self, feature_engineer):
#         self.fe = feature_engineer
#         self.model = None

#         self.FEATURES = [
#                         'lag_1',
#                         'lag_2',
#                         'rolling_mean_2',
#                         'persen_diskon',
#                         'is_weekend',
#                         'is_holiday',
#                         'is_ramadhan',
#                         'ramadhan_week',
#                         'product_age_week',
#                         'variasi_encoded'
#                     ]

#         self.load()  # 🔥 langsung load model

#     def load(self, path='model/model_xgb.pkl'):
#         try:
#             with open(path, 'rb') as f:
#                 self.model = pickle.load(f)
#         except:
#             self.model = None

#     def evaluate(self, df_raw: pd.DataFrame) -> dict:

#         if self.model is None:
#             raise ValueError("Model belum tersedia")

#         df = self.fe.create_features(df_raw)

#         if df.empty:
#             raise ValueError("Data tidak cukup untuk evaluasi")

#         split = int(len(df) * 0.8)
#         train, test = df.iloc[:split], df.iloc[split:]

#         X_test  = test[self.FEATURES]
#         y_test  = test['jumlah_terjual']

#         y_pred = self.model.predict(X_test)

#         mse  = mean_squared_error(y_test, y_pred)
#         rmse = math.sqrt(mse)
#         mae  = mean_absolute_error(y_test, y_pred)
#         r2   = r2_score(y_test, y_pred)
#         mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

#         return {
#             'mse': round(mse, 2),
#             'rmse': round(rmse, 2),
#             'mae': round(mae, 2),
#             'r2': round(r2, 3),
#             'mape': round(mape, 2),
#             'y_test': y_test.tolist(),
#             'y_pred': y_pred.tolist(),
#         }

#     def forecast(self, df_raw: pd.DataFrame, n_weeks: int = 4):

#         if self.model is None:
#             raise ValueError("Model belum tersedia")

#         df = self.fe.create_features(df_raw)

#         if df.empty:
#             raise ValueError("Data tidak cukup untuk prediksi")

#         results = []

#         for _ in range(n_weeks):
#             last_row = df.iloc[[-1]][self.FEATURES]
#             pred = float(self.model.predict(last_row)[0])
#             results.append(round(pred))

#             new_row = df.iloc[-1].copy()
#             new_row['jumlah_terjual'] = pred
#             new_row['minggu_ke'] = (new_row['minggu_ke'] % 52) + 1

#             df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
#             df = self.fe.create_features(df)

#         return results


# services/xgboost_service.py
import pandas as pd
import numpy as np
import joblib

from xgboost import XGBRegressor
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy.stats import randint, uniform


class XGBoostService:

    def __init__(self, model_path="model/model_xgb.pkl"):
        self.model_path = model_path
        self.model = None

    # =============================
    # SPLIT TIME SERIES
    # =============================
    def split_data(self, df, target, features):

        df = df.sort_values(["tahun", "minggu_ke"])

        split_index = int(len(df) * 0.8)

        train = df.iloc[:split_index]
        test = df.iloc[split_index:]

        X_train = train[features]
        y_train = train[target]

        X_test = test[features]
        y_test = test[target]

        return X_train, X_test, y_train, y_test

    # def pisah_data(self, df, target, features):

    #     df = df.sort_values("tanggal_order")

    #     unique_dates = df["tanggal_order"].unique()
    #     split_index = int(len(unique_dates) * 0.8)
    #     split_date = unique_dates[split_index]

    #     train = df[df["tanggal_order"] <= split_date]
    #     test  = df[df["tanggal_order"] > split_date]

    #     X_train = train[features]
    #     y_train = train[target]

    #     X_test = test[features]
    #     y_test = test[target]

    #     return X_train, X_test, y_train, y_test

    # =============================
    # HYPERPARAMETER TUNING
    # =============================
    # deftune_model(self, X_train, y_train):

    #     param_dist = {
    #         'n_estimators': randint(100, 800),
    #         'max_depth': randint(3, 10),
    #         'learning_rate': uniform(0.01, 0.25),
    #         'subsample': uniform(0.6, 0.4),
    #         'colsample_bytree': uniform(0.6, 0.4),
    #         'min_child_weight': randint(1, 10),
    #         'gamma': uniform(0, 0.5),
    #         'reg_alpha': uniform(0, 1),
    #         'reg_lambda': uniform(0.5, 3)
    #     }

    #     tscv = TimeSeriesSplit(n_splits=5)

    #     base_model = XGBRegressor(
    #         objective="reg:squarederror",
    #         random_state=42,
    #         n_jobs=-1
    #     )

    #     random_search = RandomizedSearchCV(
    #         estimator=base_model,
    #         param_distributions=param_dist,
    #         n_iter=50,
    #         scoring='neg_mean_absolute_error',
    #         cv=tscv,
    #         verbose=1,
    #         random_state=42,
    #         n_jobs=-1
    #     )

    #     random_search.fit(X_train, y_train)

    #     best_model = random_search.best_estimator_
    #     best_params = random_search.best_params_

    #     return best_model, best_params

    # =============================
    # HYPERPARAMETER TUNING (DIPERBAIKI JADI FLEKSIBEL & ADAPTIF)
    # =============================
    def tune_model(self, X_train, y_train):
        jumlah_baris = len(X_train)
        
        print(f"\n[TUNING INITIALIZATION] Mendeteksi {jumlah_baris} baris data agregat mingguan.")

        # -------------------------------------------------------------
        # STRATEGI ADAPTIF: Menentukan Ruang Parameter Berdasarkan Ukuran Data
        # -------------------------------------------------------------
        if jumlah_baris < 500:
            # Fase Awal / Data Sedikit (Mencegah Overfitting & Hemat Waktu)
            param_dist = {
                'n_estimators': [30, 50, 80],            # Pohon sedikit saja agar tidak menghafal data
                'max_depth': [3, 4],                     # Pohon dangkal
                'learning_rate': [0.03, 0.05, 0.1],      # Langkah agak besar karena pohon sedikit
                'subsample': [0.8, 0.9],
                'colsample_bytree': [0.8, 0.9]
            }
            n_iter_search = 8  # Cukup uji 8 kombinasi acak biar cepat
            n_splits_cv = 2    # Cross validation cukup 2-fold karena data tipis
            print("[TUNING MODE] Mengaktifkan konfigurasi data kecil (Cold-Start Mode).")

        elif 500 <= jumlah_baris < 5000:
            # Fase Menengah / Data Mulai Berkembang
            param_dist = {
                'n_estimators': [80, 100, 150, 200],
                'max_depth': [3, 4, 5],
                'learning_rate': [0.01, 0.03, 0.05, 0.1],
                'subsample': [0.7, 0.8, 0.9],
                'colsample_bytree': [0.7, 0.8, 0.9]
            }
            n_iter_search = 15 # Mencoba 15 kombinasi acak
            n_splits_cv = 3    # 3-fold TimeSeriesSplit
            print("[TUNING MODE] Mengaktifkan konfigurasi data menengah.")

        else:
            # Fase Data Besar (Saat Owner sudah pakai berbulan-bulan / bertahun-tahun)
            param_dist = {
                'n_estimators': [150, 200, 300, 400, 500], # Model bisa belajar pola musiman lebih detail
                'max_depth': [4, 5, 6, 7],                  # Mengizinkan pohon lebih dalam
                'learning_rate': [0.01, 0.02, 0.03, 0.05],  # Learning rate mengecil agar konvergensi makin presisi
                'subsample': [0.6, 0.7, 0.8],
                'colsample_bytree': [0.6, 0.7, 0.8]
            }
            n_iter_search = 25 # Mencoba 25 kombinasi acak agar pencarian makin optimal
            n_splits_cv = 4    # 4-fold TimeSeriesSplit agar evaluasi makin kokoh
            print("[TUNING MODE] Mengaktifkan konfigurasi data besar (Enterprise Mode).")

        # -------------------------------------------------------------
        # PROSES VALIDASI & SEARCHING
        # -------------------------------------------------------------
        # Pastikan n_splits tidak lebih besar dari jumlah data yang tersedia
        if jumlah_baris <= n_splits_cv:
            n_splits_cv = max(2, jumlah_baris - 1)

        tscv = TimeSeriesSplit(n_splits=n_splits_cv)

        base_model = XGBRegressor(
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1  # Menggunakan seluruh core prosesor agar hemat waktu
        )

        random_search = RandomizedSearchCV(
            estimator=base_model,
            param_distributions=param_dist,
            n_iter=n_iter_search,
            scoring='neg_mean_absolute_error',
            cv=tscv,
            verbose=1,
            random_state=42,
            n_jobs=-1
        )

        random_search.fit(X_train, y_train)

        best_model = random_search.best_estimator_
        best_params = random_search.best_params_

        print(f"[TUNING SUCCESS] Parameter terbaik ditemukan: {best_params}")
        return best_model, best_params

    def pilihparameter_model(self, X_train, y_train):

        param_dist = {
            'n_estimators': [200, 300, 400, 500],
            'max_depth': [3, 4, 5],
            'learning_rate': [0.01, 0.03, 0.05],
            'subsample': [0.8, 0.9],
            'colsample_bytree': [0.8, 0.9],
            'min_child_weight': [1, 3, 5],
            'gamma': [0, 0.1, 0.2],
            'reg_alpha': [0, 0.1],
            'reg_lambda': [1, 2, 3]
        }

        tscv = TimeSeriesSplit(n_splits=3)

        random_search = RandomizedSearchCV(
            estimator=XGBRegressor(random_state=42),
            param_distributions=param_dist,
            n_iter=20,
            cv=tscv,
            scoring='neg_mean_absolute_error',
            n_jobs=-1,
            verbose=1,
            random_state=42
        )

        random_search.fit(X_train, y_train)

        return random_search.best_estimator_, random_search.best_params_

    # =============================
    # TRAIN FINAL MODEL
    # =============================
    
    def train(self, df):

        target = "net_jumlah"

        features = [
            "variasi_encoded",
            "tahun",
            "minggu_ke",
            "persen_diskon",
            "is_weekend",
            "is_holiday",
            "is_ramadhan",
            "ramadhan_week",
            "product_age_week",
            "lag_1",
            "lag_2",
            "rolling_mean_2"
        ]

        # cek kolom
        missing = [col for col in features + [target] if col not in df.columns]

        # if missing:
        #     raise ValueError(f"Kolom model tidak ditemukan: {missing}")

        if missing:
            raise ValueError(
                f"Kolom model tidak ditemukan: {missing} Kolom tersedia: {df.columns.tolist()}")

        X_train, X_test, y_train, y_test = self.split_data(
            df,
            target,
            features
        )

        best_model, best_params = self.tune_model(X_train, y_train)

        best_model.fit(
            X_train,
            y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )

        self.model = best_model

        metrics = self.evaluate(X_test, y_test)

        self.save_model()

        return metrics, best_params

    # =============================
    # EVALUASI
    # =============================
    def evaluate(self, X_test, y_test):

        y_pred = self.model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)


        return {
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
            "r2": r2,
            "y_test": y_test.values,
            "y_pred": y_pred
        }

    # =============================
    # SAVE / LOAD
    # =============================
    def save_model(self):
        joblib.dump(self.model, self.model_path)

    def load_model(self):
        self.model = joblib.load(self.model_path)
        return self.model

    def load_external_model(self, model):
        self.model = model

    # =============================
    # FORECAST (MULTI STEP)
    # =============================
    # defforecast(self, df, n_weeks=4):

    #     df = df.sort_values(["tahun", "minggu_ke"]).copy()

    #     features = [
    #         "variasi_encoded",
    #         "tahun",
    #         "minggu_ke",
    #         "persen_diskon",
    #         "is_weekend",
    #         "is_holiday",
    #         "is_ramadhan",
    #         "ramadhan_week",
    #         "product_age_week",
    #         "lag_1",
    #         "lag_2",
    #         "rolling_mean_2"
    #     ]

    #     results = []

    #     for _ in range(n_weeks):

    #         last_row = df.iloc[-1:].copy()

    #         pred = self.model.predict(
    #             last_row[features]
    #         )[0]

    #         results.append(round(pred))

    #         new_row = last_row.copy()

    #         # update waktu
    #         new_row["minggu_ke"] += 1

    #         if new_row["minggu_ke"].iloc[0] > 52:
    #             new_row["minggu_ke"] = 1
    #             new_row["tahun"] += 1

    #         # update lag
    #         new_row["lag_2"] = new_row["lag_1"]
    #         new_row["lag_1"] = pred
    #         new_row["rolling_mean_2"] = (
    #             new_row["lag_1"] + new_row["lag_2"]
    #         ) / 2

    #         new_row["net_jumlah"] = pred

    #         df = pd.concat([df, new_row], ignore_index=True)

    #     return results

    # ==================================================
    # FORECAST (MULTI STEP) - UPDATED WITH TIME FEATURES
    # ==================================================
    def forecast(self, df, n_weeks=4):
        # Import lokal di dalam fungsi untuk menghindari circular import dengan Pipeline
        from services.feature_engineering import FeatureEngineer
        fe = FeatureEngineer()

        df = df.sort_values(["tahun", "minggu_ke"]).copy()

        features = [
            "variasi_encoded",
            "tahun",
            "minggu_ke",
            "persen_diskon",
            "is_weekend",
            "is_holiday",
            "is_ramadhan",
            "ramadhan_week",
            "product_age_week",
            "lag_1",
            "lag_2",
            "rolling_mean_2"
        ]

        results = []

        for _ in range(n_weeks):
            last_row = df.iloc[-1:].copy()

            # Predict menggunakan 12 fitur lengkap
            pred = self.model.predict(last_row[features])[0]
            
            # Amankan hasil prediksi jika minus (XGBoost kadang bisa memprediksi minus)
            pred = max(0.0, pred)
            results.append(round(pred))

            new_row = last_row.copy()

            # 1. Update Waktu / Kalender Utama
            current_week = int(new_row["minggu_ke"].iloc[0]) + 1
            current_year = int(new_row["tahun"].iloc[0])

            if current_week > 52:
                current_week = 1
                current_year += 1

            new_row["minggu_ke"] = current_week
            new_row["tahun"] = current_year
            new_row["product_age_week"] += 1

            # 2. Hitung Ulang Fitur Kalender & Ramadhan secara Dinamis
            try:
                # Rekonstruksi tanggal berdasarkan tahun dan minggu baru (asumsi hari Senin)
                approx_date = pd.to_datetime(f"{current_year}-{current_week}-1", format="%G-%V-%u")
                new_row["tanggal_order"] = approx_date
                
                # Manfaatkan fungsi dari FeatureEngineer yang sudah kamu buat
                new_row = fe.add_time_features(new_row)
                new_row = fe.add_ramadhan_features(new_row)
            except Exception as e:
                print(f"Peringatan (Fitur Waktu Forecast): {str(e)}")
                # Jika gagal, biarkan menyalin nilai minggu sebelumnya sebagai fallback keselamatan

            # 3. Update Fitur Autoregressive (Lag & Rolling Mean)
            new_row["lag_2"] = last_row["lag_1"].iloc[0]
            new_row["lag_1"] = pred
            new_row["rolling_mean_2"] = (new_row["lag_1"] + new_row["lag_2"]) / 2
            new_row["net_jumlah"] = pred

            df = pd.concat([df, new_row], ignore_index=True)

        return results