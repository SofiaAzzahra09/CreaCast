#service/pipeline_service.py
import pandas as pd
from services.feature_engineering import FeatureEngineer

class PipelineService:

    def __init__(self):
        self.fe = FeatureEngineer()

    def run(self, df_raw, is_cleaned=False):
        print("RAW:", len(df_raw))

        if not is_cleaned:
            df = self.fe.clean_data(df_raw)
            print("SETELAH CLEAN:", len(df))

            self.fe.validate_columns(df)

            df = self.fe.handle_missing_values(df)
            print("SETELAH MISSING:", len(df))
        else:
            df = df_raw.copy()

        df = self.fe.clean_data(df_raw)
        print("SETELAH CLEAN:", len(df))

        self.fe.validate_columns(df)

        df = self.fe.handle_missing_values(df)
        print("SETELAH MISSING:", len(df))

        df = self.fe.compute_features(df)
        print("SETELAH COMPUTE:", len(df))

        df = self.fe.add_time_features(df)
        print("SETELAH TIME:", len(df))

        df = self.fe.add_ramadhan_features(df)
        print("SETELAH RAMADHAN:", len(df))

        df = self.fe.encode_variasi(df)
        print("SETELAH ENCODE:", len(df))

        df = self.fe.add_product_age(df)
        print("SETELAH PRODUCT AGE:", len(df))

        df_final = self.fe.create_features(df)

        print("FINAL:", len(df_final))
        print("FINAL COLUMNS:", df_final.columns.tolist())

        return df_final

        df_final = self.fe.create_features(df)
        print("FINAL:", len(df_final))

        return df_final

    # def run(self, df_raw: pd.DataFrame):

    #     # =============================
    #     # CLEANING
    #     # =============================
    #     df = self.fe.clean_data(df_raw)
    #     self.fe.validate_columns(df)

    #     # =============================
    #     # MISSING VALUE
    #     # =============================
    #     df = self.fe.handle_missing_values(df)

    #     # =============================
    #     # FEATURE DASAR
    #     # =============================
    #     df = self.fe.compute_features(df)

    #     # =============================
    #     # TIME FEATURE
    #     # =============================
    #     df = self.fe.add_time_features(df)
    #     df = self.fe.add_ramadhan_features(df)

    #     # =============================
    #     # ENCODING
    #     # =============================
    #     df = self.fe.encode_variasi(df)

    #     # =============================
    #     # PRODUCT AGE
    #     # =============================
    #     df = self.fe.add_product_age(df)

    #     # =============================
    #     # AGREGASI + LAG
    #     # =============================
    #     df_final = self.fe.create_features(df)

    #     return df_final