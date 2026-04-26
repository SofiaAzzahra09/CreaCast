import xgboost as xgb
import pandas as pd
import numpy as np
import pickle, math

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


class XGBoostService:
    def __init__(self, feature_engineer):
        self.fe = feature_engineer
        self.model = None

        self.FEATURES = [
                        'lag_1',
                        'lag_2',
                        'rolling_mean_2',
                        'persen_diskon',
                        'is_weekend',
                        'is_holiday',
                        'is_ramadhan',
                        'ramadhan_week',
                        'product_age_week',
                        'variasi_encoded'
                    ]

        self.load()  # 🔥 langsung load model

    def load(self, path='model/model_xgb.pkl'):
        try:
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
        except:
            self.model = None

    def evaluate(self, df_raw: pd.DataFrame) -> dict:

        if self.model is None:
            raise ValueError("Model belum tersedia")

        df = self.fe.create_features(df_raw)

        if df.empty:
            raise ValueError("Data tidak cukup untuk evaluasi")

        split = int(len(df) * 0.8)
        train, test = df.iloc[:split], df.iloc[split:]

        X_test  = test[self.FEATURES]
        y_test  = test['jumlah_terjual']

        y_pred = self.model.predict(X_test)

        mse  = mean_squared_error(y_test, y_pred)
        rmse = math.sqrt(mse)
        mae  = mean_absolute_error(y_test, y_pred)
        r2   = r2_score(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

        return {
            'mse': round(mse, 2),
            'rmse': round(rmse, 2),
            'mae': round(mae, 2),
            'r2': round(r2, 3),
            'mape': round(mape, 2),
            'y_test': y_test.tolist(),
            'y_pred': y_pred.tolist(),
        }

    def forecast(self, df_raw: pd.DataFrame, n_weeks: int = 4):

        if self.model is None:
            raise ValueError("Model belum tersedia")

        df = self.fe.create_features(df_raw)

        if df.empty:
            raise ValueError("Data tidak cukup untuk prediksi")

        results = []

        for _ in range(n_weeks):
            last_row = df.iloc[[-1]][self.FEATURES]
            pred = float(self.model.predict(last_row)[0])
            results.append(round(pred))

            new_row = df.iloc[-1].copy()
            new_row['jumlah_terjual'] = pred
            new_row['minggu_ke'] = (new_row['minggu_ke'] % 52) + 1

            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
            df = self.fe.create_features(df)

        return results