# services/database_service.py
import sqlite3
import pandas as pd
import os
from config import DATABASE_PATH


class DatabaseService:

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    # ==================================================
    # INIT DB
    # ==================================================
    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with open("database/schema.sql", "r", encoding="utf-8") as f:
            schema = f.read()

        with self._connect() as conn:
            conn.executescript(schema)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==================================================
    # BASIC QUERY
    # ==================================================
    def execute(self, query, params=()):
        with self._connect() as conn:
            conn.execute(query, params)
            conn.commit()

    def fetchdf(self, query, params=()):
        with self._connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def fetchone(self, query, params=()):
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None

    # ==================================================
    # BUKU
    # ==================================================
    def get_all_buku(self):
        return self.fetchdf("""
            SELECT *
            FROM buku
            ORDER BY id DESC
        """)

    
    # ==================================================
    # PREDIKSI
    # ==================================================

    # defget_latest_prediction(self):
    #     try:
    #         df = self.fetchdf("""
    #             SELECT 
    #                 id_buku, 
    #                 prediksi AS demand_prediksi
    #             FROM prediksi
    #             ORDER BY created_at DESC
    #         """)

    #         if df.empty:
    #             return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

    #         return df

    #     except Exception:
    #         return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

    def get_latest_prediction(self):
        try:
            df = self.fetchdf("""
                SELECT 
                    id_buku, 
                    SUM(prediksi) AS demand_prediksi
                FROM prediksi
                WHERE model_versi = (
                    SELECT versi FROM model_registry WHERE LOWER(status) = 'aktif' LIMIT 1
                )
                GROUP BY id_buku
            """)

            if df.empty:
                return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

            return df

        except Exception as e:
            print(f"Error get_latest_prediction: {str(e)}")
            return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

    # defget_latest_prediction(self):
    #     """
    #     Ambil hasil prediksi terbaru.
    #     Format wajib:
    #     [id_buku, demand_prediksi]
    #     """

    #     try:
    #         df = self.fetchdf("""
    #             SELECT id_buku, demand_prediksi
    #             FROM prediksi
    #             ORDER BY created_at DESC
    #         """)

    #         if df.empty:
    #             return pd.DataFrame(columns=["id_buku", "demand_prediksi"])

    #         return df

    #     except Exception:
    #         # fallback kalau tabel belum ada
    #         return pd.DataFrame(columns=["id_buku", "demand_prediksi"])
    
    def get_kategori(self):
        df = self.fetchdf("""
            SELECT DISTINCT kategori
            FROM buku
            ORDER BY kategori
        """)
        return df["kategori"].tolist()

    # def save_buku(self, data):
    #     judul = data.get("judul", "-")
    #     kategori = data.get("kategori", "-")
    #     harga = int(data.get("harga", 0))
    #     stok = int(data.get("stok", 0))
    #     stok_min = int(data.get("stok_min", 15))

    #     # =========================
    #     # MODE UPDATE
    #     # =========================
    #     if "id" in data:

    #         self.execute("""
    #             UPDATE buku
    #             SET
    #                 judul = ?,
    #                 kategori = ?,
    #                 harga = ?,
    #                 stok = ?,
    #                 updated_at = CURRENT_TIMESTAMP
    #             WHERE id = ?
    #         """, (
    #             judul,
    #             kategori,
    #             harga,
    #             stok,
    #             data["id"]
    #         ))

    #     # =========================
    #     # MODE INSERT
    #     # =========================
    #     else:

    #         self.execute("""
    #             INSERT INTO buku (
    #                 judul,
    #                 kategori,
    #                 harga,
    #                 stok,
    #                 stok_min
    #             )
    #             VALUES (?, ?, ?, ?, ?)
    #         """, (
    #             judul,
    #             kategori,
    #             harga,
    #             stok,
    #             stok_min
    #         ))

    def save_buku(self, data):
        judul = str(data.get("judul", "")).strip()
        kategori = str(data.get("kategori", "-")).strip()
        harga = int(data.get("harga", 0))
        stok = int(data.get("stok", 0))
        stok_min = int(data.get("stok_min", 15))

        # =========================
        # HANDLE CASE 3
        # variasi kosong
        # =========================
        is_missing_variasi = False

        if not judul:
            judul = "Tanpa Variasi"
            is_missing_variasi = True

        # =========================
        # MODE UPDATE MANUAL
        # =========================
        if "id" in data:
            self.execute("""
                UPDATE buku
                SET
                    judul = ?,
                    kategori = ?,
                    harga = ?,
                    stok = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                judul,
                kategori,
                harga,
                stok,
                data["id"]
            ))
            return

        # =========================
        # CEK DUPLIKAT
        # HANDLE CASE 1 & 2
        # =========================
        existing = self.fetchone("""
            SELECT *
            FROM buku
            WHERE judul = ? AND kategori = ?
        """, (judul, kategori))

        if existing:
            harga_final = existing["harga"]
            stok_final = existing["stok"]

            # CASE 1:
            # keep data yang lebih lengkap
            if harga_final == 0 and harga > 0:
                harga_final = harga

            if stok_final == 0 and stok > 0:
                stok_final = stok

            self.execute("""
                UPDATE buku
                SET
                    harga = ?,
                    stok = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                harga_final,
                stok_final,
                existing["id"]
            ))

        else:
            # CASE 2:
            # insert hanya kalau belum ada
            self.execute("""
                INSERT INTO buku (
                    judul,
                    kategori,
                    harga,
                    stok,
                    stok_min
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                judul,
                kategori,
                harga,
                stok,
                stok_min
            ))

    def hapus_buku(self, id_buku):
        self.execute(
            "DELETE FROM buku WHERE id = ?",
            (id_buku,)
        )

    def hapus_semua_buku(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM buku")
            conn.commit()

    def update_stok(self, id_buku, stok_baru):
        self.execute("""
            UPDATE buku
            SET stok = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (stok_baru, id_buku))


    # save_weekly_sales(self, df):
    #     with self._connect() as conn:
    #         for _, row in df.iterrows():
    #             conn.execute("""
    #                 INSERT INTO weekly_sales (
    #                     nama_variasi,
    #                     variasi_encoded,
    #                     tahun,
    #                     minggu_ke,
    #                     total_net_jumlah,
    #                     avg_diskon,
    #                     total_weekend,
    #                     total_ramadhan,
    #                     ramadhan_week,
    #                     product_age_week
    #                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #             """, (
    #                 row["nama_variasi"],
    #                 int(row["variasi_encoded"]),
    #                 int(row["tahun"]),
    #                 int(row["minggu_ke"]),
    #                 int(row["net_jumlah"]),
    #                 float(row["persen_diskon"]),
    #                 int(row["is_weekend"]),
    #                 int(row["is_ramadhan"]),
    #                 int(row["ramadhan_week"]),
    #                 int(row["product_age_week"])
    #             ))

    #         conn.commit()

    def save_weekly_sales(self, df):
        # ==========================================
        # VALIDASI DATAFRAME
        # ==========================================
        if df.empty:
            print("Peringatan: DataFrame Weekly Sales kosong.")
            return

        print("\n==============================")
        print("DEBUG SAVE WEEKLY SALES")
        print("==============================")
        print("JUMLAH ROW :", len(df))
        print("KOLOM DF   :", df.columns.tolist())
        print(df.head())

        with self._connect() as conn:

            # ==========================================
            # HAPUS DATA LAMA
            # ==========================================
            conn.execute("DELETE FROM weekly_sales")

            inserted = 0

            # ==========================================
            # INSERT DATA BARU
            # ==========================================
            for _, row in df.iterrows():

                try:

                    # ==============================
                    # FLEXIBLE COLUMN MAPPING
                    # ==============================
                    net_jumlah = row.get(
                        "net_jumlah",
                        row.get("total_net_jumlah", 0)
                    )

                    persen_diskon = row.get(
                        "persen_diskon",
                        row.get("avg_diskon", 0)
                    )

                    is_weekend = row.get(
                        "is_weekend",
                        row.get("total_weekend", 0)
                    )

                    is_ramadhan = row.get(
                        "is_ramadhan",
                        row.get("total_ramadhan", 0)
                    )

                    # ==============================
                    # HANDLE NaN
                    # ==============================
                    net_jumlah = 0 if pd.isna(net_jumlah) else int(net_jumlah)
                    persen_diskon = 0 if pd.isna(persen_diskon) else float(persen_diskon)
                    is_weekend = 0 if pd.isna(is_weekend) else int(is_weekend)
                    is_ramadhan = 0 if pd.isna(is_ramadhan) else int(is_ramadhan)

                    conn.execute("""
                        INSERT INTO weekly_sales (
                            nama_variasi,
                            variasi_encoded,
                            tahun,
                            minggu_ke,
                            total_net_jumlah,
                            avg_diskon,
                            total_weekend,
                            total_ramadhan,
                            ramadhan_week,
                            product_age_week
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get("nama_variasi", "-")),
                        int(row.get("variasi_encoded", 0)),
                        int(row.get("tahun", 0)),
                        int(row.get("minggu_ke", 0)),
                        net_jumlah,
                        persen_diskon,
                        is_weekend,
                        is_ramadhan,
                        int(row.get("ramadhan_week", 0)),

                        int(row.get("product_age_week", 0))
                    ))

                    inserted += 1

                except Exception as row_error:

                    print("\nERROR INSERT ROW:")
                    print(row.to_dict())
                    print("DETAIL ERROR:", str(row_error))

            conn.commit()

            print(f"\nBerhasil simpan {inserted} data weekly_sales")

    # ==================================================
    # MODEL PROTECTION & REGISTRY MANAGEMENT
    # ==================================================
    # save_trained_model(self, metadata):
    #     """Menyimpan metadata lengkap hasil training XGBoost"""
    #     self.execute("""
    #         INSERT INTO model_registry (
    #             versi, jumlah_data, mse, rmse, mae, r2, 
    #             hyperparameter, file_path, status, features_used, 
    #             train_test_split_ratio, catatan
    #         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'nonaktif', ?, ?, ?)
    #     """, (
    #         metadata['versi'], metadata['jumlah_data'], metadata['mse'], 
    #         metadata['rmse'], metadata['mae'], metadata['r2'],
    #         metadata['hyperparameter'], metadata['file_path'],
    #         metadata['features_used'], metadata['train_test_split_ratio'],
    #         metadata['catatan']
    #     ))

    

    # ==================================================
    # PENJUALAN (DATA HISTORIS)
    # ==================================================
    def get_all_penjualan(self):
        """
        Ambil semua data historis penjualan
        Format:
        [id_buku, minggu_ke, jumlah_terjual]
        """
        try:
            df = self.fetchdf("""
                SELECT 
                    id_buku,
                    minggu_ke,
                    jumlah_terjual
                FROM penjualan
                ORDER BY tahun, minggu_ke
            """)

            if df.empty:
                return pd.DataFrame(columns=["id_buku", "minggu_ke", "jumlah_terjual"])

            return df

        except Exception:
            return pd.DataFrame(columns=["id_buku", "minggu_ke", "jumlah_terjual"])
    
    # ==================================================
    # RAW TRANSACTIONS
    # ==================================================
    def insert_raw_transactions(
        self,
        df,
        source_file=None,
        total_rows=None
    ):

        with self._connect() as conn:

            df = df.fillna("")

            df.columns = [
                c.lower().strip().replace(" ", "_").replace("/", "_")
                for c in df.columns
            ]

            inserted = 0
            skipped = 0

            for _, row in df.iterrows():

                no_pesanan = row.get("no_pesanan")
                nama_produk = row.get("nama_produk")
                nama_variasi = row.get("nama_variasi")
                waktu_order = row.get("waktu_pesanan_dibuat")

                # ==========================================
                # CEK DUPLIKAT
                # ==========================================

                existing = conn.execute("""
                    SELECT id
                    FROM raw_transactions
                    WHERE
                        no_pesanan = ?
                        AND nama_produk = ?
                        AND nama_variasi = ?
                        AND waktu_pesanan_dibuat = ?
                """, (
                    no_pesanan,
                    nama_produk,
                    nama_variasi,
                    waktu_order
                )).fetchone()

                if existing:
                    skipped += 1
                    continue

                conn.execute("""
                    INSERT INTO raw_transactions (
                        no_pesanan,
                        status_pesanan,
                        status_pembatalan,

                        nama_produk,
                        nama_variasi,

                        harga_awal,
                        harga_setelah_diskon,
                        jumlah,
                        returned_quantity,

                        waktu_pesanan_dibuat,
                        waktu_pesanan_selesai,

                        metode_pembayaran,
                        provinsi
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("no_pesanan"),
                    row.get("status_pesanan"),
                    row.get("status_pembatalan"),

                    row.get("nama_produk"),
                    row.get("nama_variasi"),

                    row.get("harga_awal"),
                    row.get("harga_setelah_diskon"),

                    row.get("jumlah"),
                    row.get("returned_quantity"),

                    row.get("waktu_pesanan_dibuat"),
                    row.get("waktu_pesanan_selesai"),

                    row.get("metode_pembayaran"),
                    row.get("provinsi")
                ))

                inserted += 1

            conn.commit()

            return {
                "inserted": inserted,
                "skipped": skipped
            }

    # ==================================================
    # RAW TRANSACTIONS (DENGAN METADATA & VALIDASI)
    # ==================================================
    # insert_raw_transactions(self, df, filename, row_count):
    #     with self._connect() as conn:
    #         df = df.fillna("")
    #         df.columns = [
    #             c.lower().strip().replace(" ", "_").replace("/", "_")
    #             for c in df.columns
    #         ]

    #         for _, row in df.iterrows():
    #             conn.execute("""
    #                 INSERT INTO raw_transactions (
    #                     no_pesanan, status_pesanan, status_pembatalan,
    #                     nama_produk, nama_variasi, harga_awal,
    #                     harga_setelah_diskon, jumlah, returned_quantity,
    #                     waktu_pesanan_dibuat, waktu_pesanan_selesai,
    #                     metode_pembayaran, provinsi,
    #                     upload_file_name, upload_row_count
    #                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #             """, (
    #                 str(row.get("no_pesanan")),
    #                 str(row.get("status_pesanan")),
    #                 str(row.get("status_pembatalan")),
    #                 str(row.get("nama_produk")),
    #                 str(row.get("nama_variasi")),
    #                 str(row.get("harga_awal")),
    #                 str(row.get("harga_setelah_diskon")),
    #                 str(row.get("jumlah")),
    #                 str(row.get("returned_quantity")),
    #                 str(row.get("waktu_pesanan_dibuat")),
    #                 str(row.get("waktu_pesanan_selesai")),
    #                 str(row.get("metode_pembayaran")),
    #                 str(row.get("provinsi")),
    #                 filename,
    #                 row_count
    #             ))
    #         conn.commit()

    def get_raw_transactions(self):
        return self.fetchdf("SELECT * FROM raw_transactions ORDER BY created_at DESC")

    def process_pipeline(self, pipeline_service):
        df_raw = self.get_raw_transactions()

        if df_raw.empty:
            return None

        # df_final = pipeline_service.run(df_raw)
        # self.execute("DELETE FROM weekly_sales")
        # self.save_weekly_sales(df_final)
        df_final = pipeline_service.run(df_raw)

        print("HASIL PIPELINE:")
        print(df_final.head())
        print("JUMLAH ROW:", len(df_final))

        if df_final.empty:
            print("PIPELINE KOSONG")
            return None

        self.execute("DELETE FROM weekly_sales")
        self.save_weekly_sales(df_final)

        return df_final

    # defget_weekly_sales(self, weeks=None):
    #     query = """
    #         SELECT *
    #         FROM weekly_sales
    #         ORDER BY variasi_encoded, tahun, minggu_ke
    #     """

    #     if weeks:
    #         query += f" LIMIT {weeks}"

    #     df = self.fetchdf(query)

    #     if df.empty:
    #         return df

    #     # =========================================================
    #     # Kembalikan nama kolom database ke format internal Pipeline
    #     # =========================================================
    #     df = df.rename(columns={
    #         "total_net_jumlah": "net_jumlah",
    #         "avg_diskon": "persen_diskon",
    #         "total_weekend": "is_weekend",
    #         "total_ramadhan": "is_ramadhan"
    #     })

    #     # Tambah kolom default jika belum ada di database schema
    #     if "is_holiday" not in df.columns:
    #         df["is_holiday"] = 0

    #     # =========================================================
    #     # RE-GENERATE LAG & ROLLING FEATURES (Wajib Groupby per Produk)
    #     # =========================================================
    #     # Catatan: Perhitungan lag harus di-groupby per variasi agar data tidak bocor antar-produk
    #     df["lag_1"] = df.groupby("variasi_encoded")["net_jumlah"].shift(1)
    #     df["lag_2"] = df.groupby("variasi_encoded")["net_jumlah"].shift(2)

    #     df["rolling_mean_2"] = (
    #         df.groupby("variasi_encoded")["net_jumlah"]
    #         .transform(lambda x: x.shift(1).rolling(2).mean())
    #     )

    #     # Isi sisa data kosong hasil shift dengan 0
    #     df = df.fillna(0)

    #     return df

    # defget_weekly_sales(self, weeks=None):
    #     query = """
    #         SELECT *
    #         FROM weekly_sales
    #         ORDER BY variasi_encoded, tahun, minggu_ke
    #     """

    #     if weeks:
    #         query += f" LIMIT {weeks}"

    #     df = self.fetchdf(query)

    #     if df.empty:
    #         return df

    #     df = df.rename(columns={
    #         "total_net_jumlah": "net_jumlah",
    #         "avg_diskon": "persen_diskon",
    #         "total_weekend": "is_weekend",
    #         "total_ramadhan": "is_ramadhan"
    #     })

    #     if "is_holiday" not in df.columns:
    #         df["is_holiday"] = 0

    #     # =========================================================
    #     # RE-GENERATE LAG & ROLLING FEATURES (Urutan Kronologis Wajib!)
    #     # =========================================================
    #     # Urutkan secara eksplisit sebelum melakukan shift
    #     df = df.sort_values(["variasi_encoded", "tahun", "minggu_ke"]).reset_index(drop=True)
        
    #     df["lag_1"] = df.groupby("variasi_encoded")["net_jumlah"].shift(1)
    #     df["lag_2"] = df.groupby("variasi_encoded")["net_jumlah"].shift(2)

    #     df["rolling_mean_2"] = (
    #         df.groupby("variasi_encoded")["net_jumlah"]
    #         .transform(lambda x: x.shift(1).rolling(2).mean())
    #     )

    #     # Jangan isi semua dengan 0, melainkan bfill untuk lag awal atau biarkan model menghandle
    #     df[["lag_1", "lag_2", "rolling_mean_2"]] = df.groupby("variasi_encoded")[["lag_1", "lag_2", "rolling_mean_2"]].bfill().fillna(0)

    #     return df

    def get_weekly_sales(self, weeks=None):

        # =========================================================
        # AMBIL SEMUA DATA
        # =========================================================
        query = """
            SELECT *
            FROM weekly_sales
            ORDER BY variasi_encoded, tahun, minggu_ke
        """

        df = self.fetchdf(query)

        if df.empty:
            return df

        # =========================================================
        # RENAME KOLOM
        # =========================================================
        df = df.rename(columns={
            "total_net_jumlah": "net_jumlah",
            "avg_diskon": "persen_diskon",
            "total_weekend": "is_weekend",
            "total_ramadhan": "is_ramadhan"
        })

        # =========================================================
        # TAMBAH DEFAULT FEATURE
        # =========================================================
        if "is_holiday" not in df.columns:
            df["is_holiday"] = 0

        # =========================================================
        # SORT KRONOLOGIS
        # =========================================================
        df = df.sort_values(
            ["variasi_encoded", "tahun", "minggu_ke"]
        ).reset_index(drop=True)

        # =========================================================
        # FILTER HISTORIS PER PRODUK
        # =========================================================
        if weeks:
            df = (
                df.groupby("variasi_encoded")
                .tail(weeks)
                .reset_index(drop=True)
            )

        # =========================================================
        # LAG FEATURES
        # =========================================================
        df["lag_1"] = (
            df.groupby("variasi_encoded")["net_jumlah"]
            .shift(1)
        )

        df["lag_2"] = (
            df.groupby("variasi_encoded")["net_jumlah"]
            .shift(2)
        )

        # =========================================================
        # ROLLING MEAN
        # =========================================================
        df["rolling_mean_2"] = (
            df.groupby("variasi_encoded")["net_jumlah"]
            .transform(
                lambda x: x.shift(1).rolling(2).mean()
            )
        )

        # =========================================================
        # HANDLE NaN
        # =========================================================
        df[[
            "lag_1",
            "lag_2",
            "rolling_mean_2"
        ]] = (
            df.groupby("variasi_encoded")[[
                "lag_1",
                "lag_2",
                "rolling_mean_2"
            ]]
            .bfill()
            .fillna(0)
        )

        return df


    def save_prediction(
        self,
        forecast,
        start_week,
        start_year,
        model_versi="v1",
        id_buku=1
    ):

        with self._connect() as conn:

            for i, pred in enumerate(forecast):

                minggu = start_week + i
                tahun = start_year

                if minggu > 52:
                    minggu -= 52
                    tahun += 1

                conn.execute("""
                    INSERT INTO prediksi (
                        id_buku,
                        minggu_ke,
                        tahun,
                        prediksi,
                        model_versi
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    id_buku,
                    minggu,
                    tahun,
                    float(pred),
                    model_versi
                ))

            conn.commit()


    # ==================================================
    # LAPORAN
    # ==================================================
    def get_laporan_history(self):
        try:
            return self.fetchdf("""
                SELECT *
                FROM laporan_history
                ORDER BY created_at DESC
            """)
        except Exception:
            return pd.DataFrame(columns=[
                "nama_file",
                "format",
                "ukuran_kb",
                "created_at"
            ])


    def save_laporan_history(self, nama_file, file_format, ukuran_kb):
        self.execute("""
            INSERT INTO laporan_history (
                nama_file,
                format,
                ukuran_kb
            ) VALUES (?, ?, ?)
        """, (nama_file, file_format, ukuran_kb))

    def reset_database(self):
        import gc

        gc.collect()

        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except PermissionError:
            raise Exception(
                "Database sedang dipakai. Tutup Streamlit dulu."
            )

        self._init_db()  

    def get_buku_id_by_judul(self, judul_buku):
        """
        Mencari ID asli dari tabel buku berdasarkan judul/variasi.
        """
        row = self.fetchone(
            "SELECT id FROM buku WHERE LOWER(TRIM(judul)) = LOWER(TRIM(?)) LIMIT 1", 
            (judul_buku,)
        )
        return row["id"] if row else None