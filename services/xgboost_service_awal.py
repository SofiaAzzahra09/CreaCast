# services/xgboost_service.py
import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle, math

class XGBoostService:
    def __init__(self, feature_engineer):
        self.fe = feature_engineer
        self.model = None
        self.FEATURES = ['lag_1','lag_2','lag_3','lag_4',
                         'rolling_mean_4','rolling_mean_8','rolling_std_4',
                         'minggu_ke_sin','minggu_ke_cos','kategori_enc']

    def train(self, df_raw: pd.DataFrame) -> dict:
        df = self.fe.create_features(df_raw)
        split = int(len(df) * 0.8)
        train, test = df.iloc[:split], df.iloc[split:]

        X_train, y_train = train[self.FEATURES], train['jumlah_terjual']
        X_test,  y_test  = test[self.FEATURES],  test['jumlah_terjual']

        self.model = xgb.XGBRegressor(
            n_estimators=200, learning_rate=0.1, max_depth=6,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, early_stopping_rounds=20,
            eval_metric='rmse'
        )
        self.model.fit(X_train, y_train,
                       eval_set=[(X_test, y_test)],
                       verbose=False)

        y_pred = self.model.predict(X_test)
        rmse = math.sqrt(mean_squared_error(y_test, y_pred))
        mae  = mean_absolute_error(y_test, y_pred)
        r2   = r2_score(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

        return {
            'rmse': round(rmse, 2), 'mae': round(mae, 2),
            'r2': round(r2, 3),     'mape': round(mape, 2),
            'y_test': y_test.tolist(), 'y_pred': y_pred.tolist(),
            'feature_importance': dict(zip(self.FEATURES,
                self.model.feature_importances_.tolist()))
        }

    def forecast(self, df_raw: pd.DataFrame, n_weeks: int = 4) -> list:
        df = self.fe.create_features(df_raw)
        results = []
        for _ in range(n_weeks):
            last_row = df.iloc[[-1]][self.FEATURES]
            pred = float(self.model.predict(last_row)[0])
            results.append(round(pred))
            # update lag untuk iterasi berikutnya
            new_row = df.iloc[-1].copy()
            new_row['jumlah_terjual'] = pred
            new_row['minggu_ke'] = (new_row['minggu_ke'] % 52) + 1
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)
            df = self.fe.create_features(df)
        return results

    def save(self, path='model/xgboost_creatroka.pkl'):
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)

    def load(self, path='model/xgboost_creatroka.pkl'):
        with open(path, 'rb') as f:
            self.model = pickle.load(f)