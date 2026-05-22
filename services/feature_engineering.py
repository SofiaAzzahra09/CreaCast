# service/feature_engineering.py
import json
import os
import holidays
import numpy as np
import pandas as pd
from hijri_converter import Gregorian, Hijri


class FeatureEngineer:

    VARIASI_MAP_PATH = "data/variasi_map.json"
    REQUIRED_COLUMNS = ["jumlah"]

    COLUMN_MAPPING = {
        "tanggal_order": [
            "waktu_pesanan_dibuat",
            "waktu_pembayaran_dilakukan",
            "tanggal_order",
            "tanggal",
        ],
        "tanggal_selesai": ["waktu_pesanan_selesai"],
        "jumlah": ["jumlah"],
        "harga_awal": ["harga_awal"],
        "harga_diskon": ["harga_setelah_diskon"],
        "returned_quantity": ["returned_quantity"],
        "status_pembatalan_pengembalian": [
            "status_pembatalan_pengembalian",
            "status_pembatalan_pengembalian_",
        ],
    }

    def normalize_column_name(self, col: str) -> str:
        return col.lower().strip().replace(" ", "_").replace(".", "").replace("/", "_")

    def load_variasi_map(self) -> dict:
        if not os.path.exists(self.VARIASI_MAP_PATH):
            return {}
        with open(self.VARIASI_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_variasi_map(self, mapping: dict):
        os.makedirs(os.path.dirname(self.VARIASI_MAP_PATH), exist_ok=True)
        with open(self.VARIASI_MAP_PATH, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=4)

    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [self.normalize_column_name(c) for c in df.columns]

        new_columns = {}
        for standard_col, variations in self.COLUMN_MAPPING.items():
            for var in variations:
                var_norm = self.normalize_column_name(var)
                if var_norm in df.columns:
                    new_columns[var_norm] = standard_col
                    break

        return df.rename(columns=new_columns)

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        print("KOLOM ASLI:", df.columns.tolist())
        df = self.map_columns(df)
        print("SETELAH MAPPING:", df.columns.tolist())

        # Handle Tanggal
        date_candidates = [
            "tanggal_order",
            "waktu_pesanan_dibuat",
            "waktu_pembayaran_dilakukan",
        ]
        selected_date_col = next((col for col in date_candidates if col in df.columns), None)

        if selected_date_col:
            df["tanggal_order"] = pd.to_datetime(
                df[selected_date_col].astype(str).str.strip(), errors="coerce"
            )

        if "tanggal_selesai" in df.columns:
            df["tanggal_selesai"] = pd.to_datetime(
                df["tanggal_selesai"].astype(str).str.strip(), errors="coerce"
            )

        # Numerik
        numeric_cols = ["jumlah", "harga_awal", "harga_diskon", "returned_quantity"]
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
                .replace(["", "nan", "None"], np.nan)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # String Lowercase & Strip
        for col in df.columns:
            if col != "tanggal_order" and df[col].dtype == "object":
                df[col] = df[col].astype(str).str.lower().str.strip()

        subset_cols = [
            c
            for c in ["no_pesanan", "nama_produk", "nama_variasi", "tanggal_order"]
            if c in df.columns
        ]
        df = df.drop_duplicates(subset=subset_cols).reset_index(drop=True)
        print("Tanggal parsed:", df["tanggal_order"].notna().sum())
        return df

    def validate_columns(self, df: pd.DataFrame):
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")

    def _fill_variasi(self, row, prod_price_mode, prod_mode):
        if pd.notna(row["nama_variasi"]):
            return row["nama_variasi"]
        key = (row["nama_produk"], row["harga_awal"])
        if key in prod_price_mode:
            return prod_price_mode[key]
        if row["nama_produk"] in prod_mode:
            return prod_mode[row["nama_produk"]]
        return "tanpa variasi"

    def _fill_harga(self, row, prod_var_median, prod_median, global_median):
        if pd.notna(row["harga_awal"]):
            return row["harga_awal"]
        key = (row["nama_produk"], row["nama_variasi"])
        if key in prod_var_median and pd.notna(prod_var_median[key]):
            return prod_var_median[key]
        if row["nama_produk"] in prod_median and pd.notna(prod_median[row["nama_produk"]]):
            return prod_median[row["nama_produk"]]
        return global_median

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # =========================================================
        # NORMALISASI STRING
        # =========================================================
        for col in ["nama_produk", "nama_variasi"]:

            if col in df.columns:

                df[col] = (
                    df[col]
                    .astype(str)
                    .str.lower()
                    .str.strip()
                    .replace(
                        ["nan", "none", "null", ""],
                        np.nan
                    )
                )

        # =========================================================
        # NORMALISASI HARGA AWAL
        # =========================================================
        if "harga_awal" in df.columns:

            df["harga_awal"] = (
                df["harga_awal"]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
                .replace(
                    ["nan", "none", "null", ""],
                    np.nan
                )
            )

            df["harga_awal"] = pd.to_numeric(
                df["harga_awal"],
                errors="coerce"
            )

        # =========================================================
        # IMPUTASI NAMA VARIASI
        # =========================================================
        required_variasi_cols = [
            "nama_produk",
            "harga_awal",
            "nama_variasi"
        ]

        if all(col in df.columns for col in required_variasi_cols):

            valid_variasi_df = df[df["nama_variasi"].notna()]

            # MODE berdasarkan produk + harga
            product_price_mode = (
                valid_variasi_df
                .groupby(["nama_produk", "harga_awal"])["nama_variasi"]
                .agg(
                    lambda x:
                    x.mode().iloc[0]
                    if not x.mode().empty
                    else np.nan
                )
                .to_dict()
            )

            # MODE berdasarkan produk
            product_mode = (
                valid_variasi_df
                .groupby("nama_produk")["nama_variasi"]
                .agg(
                    lambda x:
                    x.mode().iloc[0]
                    if not x.mode().empty
                    else np.nan
                )
                .to_dict()
            )

            df["nama_variasi"] = df.apply(
                self._fill_variasi,
                args=(product_price_mode, product_mode),
                axis=1
            )

        # =========================================================
        # IMPUTASI HARGA AWAL
        # =========================================================
        if "harga_awal" in df.columns:

            global_median = df["harga_awal"].median()

            if pd.isna(global_median):
                global_median = 0

            product_variasi_median = (
                df.groupby(
                    ["nama_produk", "nama_variasi"]
                )["harga_awal"]
                .median()
                .to_dict()
            )

            product_median = (
                df.groupby("nama_produk")["harga_awal"]
                .median()
                .to_dict()
            )

            df["harga_awal"] = df.apply(
                self._fill_harga,
                args=(
                    product_variasi_median,
                    product_median,
                    global_median
                ),
                axis=1
            )

        # =========================================================
        # HARGA DISKON
        # =========================================================
        if "harga_diskon" in df.columns:

            df["harga_diskon"] = (
                pd.to_numeric(
                    df["harga_diskon"],
                    errors="coerce"
                )
                .fillna(df["harga_awal"])
            )

        # =========================================================
        # RETURNED QUANTITY
        # =========================================================
        if "returned_quantity" not in df.columns:
            df["returned_quantity"] = 0

        df["returned_quantity"] = (
            pd.to_numeric(
                df["returned_quantity"],
                errors="coerce"
            )
            .fillna(0)
        )

        # =========================================================
        # FINAL CLEANING NAMA VARIASI
        # =========================================================
        if "nama_variasi" in df.columns:

            df["nama_variasi"] = (
                df["nama_variasi"]
                .astype(str)
                .str.lower()
                .str.strip()
            )

            df.loc[
                df["nama_variasi"].isin(
                    ["nan", "none", "null", ""]
                ),
                "nama_variasi"
            ] = "tanpa variasi"

        return df

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Net Jumlah & Outlier Clip
        if all(col in df.columns for col in ["jumlah", "returned_quantity"]):
            df["jumlah"] = pd.to_numeric(df["jumlah"], errors="coerce").fillna(0)
            df["returned_quantity"] = pd.to_numeric(df["returned_quantity"], errors="coerce").fillna(
                0
            )

            df["net_jumlah"] = df["jumlah"] - df["returned_quantity"]
            upper = df["net_jumlah"].quantile(0.99)
            df["net_jumlah"] = df["net_jumlah"].clip(lower=0, upper=upper)

        # Status Pesanan
        if "status_pesanan" not in df.columns and "tanggal_selesai" in df.columns:
            df["status_pesanan"] = df["tanggal_selesai"].apply(
                lambda x: "selesai" if pd.notna(x) else "batal"
            )

        # Jumlah Produk Dalam Pesanan
        if "no_pesanan" in df.columns and "jumlah" in df.columns:
            df["jumlah_produk_dipesan"] = df.groupby("no_pesanan")["jumlah"].transform("sum")

        # Persen Diskon
        if all(col in df.columns for col in ["harga_awal", "harga_diskon"]):
            df["persen_diskon"] = np.where(
                df["harga_awal"] != 0,
                (df["harga_awal"] - df["harga_diskon"]) / df["harga_awal"],
                0,
            )
        else:
            df["persen_diskon"] = 0

        return df

    def standardize_output(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        target_columns = [
            "no_pesanan",
            "status_pesanan",
            "status_pembatalan_pengembalian",
            "tanggal_order",
            "nama_produk",
            "nama_variasi",
            "harga_awal",
            "harga_diskon",
            "jumlah",
            "returned_quantity",
            "jumlah_produk_dipesan",
            "tanggal_selesai",
            "net_jumlah",
            "persen_diskon",
        ]

        for col in target_columns:
            if col not in df.columns:
                df[col] = 0

        return df[target_columns]

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        print(df[["tanggal_order"]].head(20))
        print("ROWS BEFORE:", len(df))

        df["tanggal_order"] = pd.to_datetime(df["tanggal_order"], errors="coerce")
        df = df[df["tanggal_order"].notna()]

        if len(df) == 0:
            print(df.columns.tolist())
            raise ValueError("Tanggal gagal diparse. Format tanggal Shopee tidak terbaca.")

        df["weekday"] = df["tanggal_order"].dt.weekday
        df["is_weekend"] = (df["weekday"] >= 5).astype(int)

        print("ROWS AFTER:", len(df))

        indo_holidays = holidays.ID()
        df["is_holiday"] = df["tanggal_order"].apply(
            lambda x: 1 if pd.notna(x) and x.date() in indo_holidays else 0
        )

        print("NULL tanggal_order:", df["tanggal_order"].isna().sum())
        return df

    def add_ramadhan_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["is_ramadhan"] = 0
        df["ramadhan_week"] = -1

        if "tanggal_order" not in df.columns:
            return df

        years = df["tanggal_order"].dt.year.dropna().unique()

        for year in years:
            try:
                hijri_year = Gregorian(int(year), 1, 1).to_hijri().year

                for hy in [hijri_year - 1, hijri_year, hijri_year + 1]:
                    start = pd.Timestamp(Hijri(hy, 9, 1).to_gregorian().datetuple())
                    end = start + pd.Timedelta(days=29)

                    mask = (df["tanggal_order"] >= start) & (df["tanggal_order"] <= end)
                    df.loc[mask, "is_ramadhan"] = 1
                    df.loc[mask, "ramadhan_week"] = (
                        (df.loc[mask, "tanggal_order"] - start).dt.days // 7
                    ) + 1
            except Exception:
                continue

        return df

    def encode_variasi(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "nama_variasi" not in df.columns:
            df["nama_variasi"] = "tanpa variasi"

        mapping = self.load_variasi_map()
        current_max = max(mapping.values(), default=-1)

        for variasi in df["nama_variasi"].unique():
            if variasi not in mapping:
                current_max += 1
                mapping[variasi] = current_max

        self.save_variasi_map(mapping)
        df["variasi_encoded"] = df["nama_variasi"].map(mapping)
        return df

    def add_product_age(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        first_sale = (
            df.groupby("nama_variasi")["tanggal_order"]
            .min()
            .reset_index()
            .rename(columns={"tanggal_order": "first_sale_date"})
        )

        df = df.merge(first_sale, on="nama_variasi", how="left")
        df["product_age_week"] = (
            (df["tanggal_order"] - df["first_sale_date"]).dt.days // 7
        ).clip(lower=0)
        return df

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["tanggal_order"] = pd.to_datetime(df["tanggal_order"], errors="coerce")
        df = df.dropna(subset=["tanggal_order"])

        numeric_cols = [
            "net_jumlah",
            "persen_diskon",
            "is_weekend",
            "is_holiday",
            "is_ramadhan",
            "ramadhan_week",
            "product_age_week",
            "variasi_encoded",
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df["tahun"] = df["tanggal_order"].dt.year
        df["minggu_ke"] = df["tanggal_order"].dt.isocalendar().week.astype(int)
        df = df.sort_values(["variasi_encoded", "tanggal_order"])

        # Agregasi Mingguan
        weekly = df.groupby(
            ["nama_variasi", "variasi_encoded", "tahun", "minggu_ke"], as_index=False
        ).agg(
            {
                "net_jumlah": "sum",
                "persen_diskon": "mean",
                "is_weekend": "sum",
                "is_holiday": "sum",
                "is_ramadhan": "sum",
                "ramadhan_week": "max",
                "product_age_week": "max",
            }
        )

        completed = []
        fill_cols = [
            "net_jumlah",
            "persen_diskon",
            "is_weekend",
            "is_holiday",
            "is_ramadhan",
            "ramadhan_week",
            "product_age_week",
        ]

        # ... (kode awal create_features tetap sama sampai loop kode) ...
        for kode in weekly["variasi_encoded"].unique():
            temp = weekly[weekly["variasi_encoded"] == kode].copy()
            temp["week_date"] = pd.to_datetime(
                temp["tahun"].astype(str) + "-" + temp["minggu_ke"].astype(str) + "-1",
                format="%G-%V-%u",
            )
            temp = temp.sort_values("week_date")

            # Membuat rentang waktu hanya dari penjualan pertama produk tersebut
            full_dates = pd.date_range(
                start=temp["week_date"].min(), end=temp["week_date"].max(), freq="W-MON"
            )
            full_weeks = pd.DataFrame({"week_date": full_dates})

            iso = full_weeks["week_date"].dt.isocalendar()
            full_weeks["tahun"] = iso.year
            full_weeks["minggu_ke"] = iso.week

            temp = full_weeks.merge(temp, on=["tahun", "minggu_ke"], how="left")
            temp["variasi_encoded"] = kode
            temp["nama_variasi"] = temp["nama_variasi"].ffill()
            
            # Khusus fitur target net_jumlah, isi kosong dengan 0 hanya jika rentang waktu valid
            temp["net_jumlah"] = temp["net_jumlah"].fillna(0)
            
            # Fitur pendukung sebaiknya diisi menggunakan nilai logis terdekat (forward fill)
            other_features = ["persen_diskon", "is_weekend", "is_holiday", "is_ramadhan", "ramadhan_week", "product_age_week"]
            temp[other_features] = temp[other_features].ffill().fillna(0)

            completed.append(temp)

        if completed:
            weekly = pd.concat(completed, ignore_index=True)
            # Pastikan urutan kronologis terjaga untuk kalkulasi lag berikutnya
            weekly = weekly.sort_values(["variasi_encoded", "tahun", "minggu_ke"]).reset_index(drop=True)
        else:
            weekly = pd.DataFrame()

        if not weekly.empty:
            weekly["lag_1"] = weekly.groupby("variasi_encoded")["net_jumlah"].shift(1)
            weekly["lag_2"] = weekly.groupby("variasi_encoded")["net_jumlah"].shift(2)
            weekly["rolling_mean_2"] = (
                weekly.groupby("variasi_encoded")["net_jumlah"]
                .transform(lambda x: x.shift(1).rolling(2).mean())
            )
            # Ambil nilai terdekat untuk baris awal agar tidak menghasilkan angka 0 mutlak
            weekly[["lag_1", "lag_2", "rolling_mean_2"]] = weekly.groupby("variasi_encoded")[["lag_1", "lag_2", "rolling_mean_2"]].bfill().fillna(0)

        return weekly

    def detect_missing_critical(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        critical_cols = ["tanggal_order", "nama_produk", "jumlah", "nama_variasi", "harga_awal"]
        existing_cols = [c for c in critical_cols if c in df.columns]

        if not existing_cols:
            return pd.DataFrame()

        for col in existing_cols:
            df[col] = df[col].replace(["nan", "", "none"], np.nan)

        missing_mask = df[existing_cols].isna().any(axis=1)
        return df[missing_mask].copy()

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.clean_data(df)
        self.validate_columns(df)
        df = self.handle_missing_values(df)
        df = self.compute_features(df)
        df = self.add_time_features(df)
        df = self.add_ramadhan_features(df)
        df = self.encode_variasi(df)
        df = self.add_product_age(df)
        df = self.create_features(df)
        return df