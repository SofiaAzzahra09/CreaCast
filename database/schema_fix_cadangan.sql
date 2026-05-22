-- database/schema.sql

CREATE TABLE IF NOT EXISTS buku (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,

    -- dari excel
    judul       TEXT NOT NULL,         -- nama variasi
    kategori    TEXT NOT NULL,         -- nama produk

    -- default sistem
    penulis     TEXT DEFAULT '-',
    penerbit    TEXT DEFAULT '-',
    isbn        TEXT DEFAULT '-',

    harga       INTEGER NOT NULL DEFAULT 0,   -- harga awal
    stok        INTEGER NOT NULL DEFAULT 0,   -- jumlah
    stok_min    INTEGER NOT NULL DEFAULT 15,

    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS penjualan (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_buku         INTEGER NOT NULL REFERENCES buku(id),
    minggu_ke       INTEGER NOT NULL,
    tahun           INTEGER NOT NULL,
    jumlah_terjual  INTEGER NOT NULL,
    harga_satuan    INTEGER NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_registry (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    versi            TEXT NOT NULL UNIQUE,
    tanggal_training TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    jumlah_data      INTEGER NOT NULL,
    mse              REAL NOT NULL,
    rmse             REAL NOT NULL,
    mae              REAL NOT NULL,
    r2               REAL NOT NULL,
    hyperparameter   TEXT NOT NULL,
    file_path        TEXT NOT NULL,
    status           TEXT DEFAULT 'archive',
    catatan          TEXT
);

CREATE TABLE IF NOT EXISTS raw_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    no_pesanan TEXT,
    status_pesanan TEXT,
    status_pembatalan TEXT,

    nama_produk TEXT,
    nama_variasi TEXT,

    harga_awal TEXT,
    harga_setelah_diskon TEXT,
    jumlah TEXT,
    returned_quantity TEXT,

    waktu_pesanan_dibuat TEXT,
    waktu_pesanan_selesai TEXT,

    metode_pembayaran TEXT,
    provinsi TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cleaned_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    no_pesanan TEXT,

    nama_produk TEXT,
    nama_variasi TEXT,
    variasi_encoded INTEGER,

    jumlah INTEGER,
    returned_quantity INTEGER,
    net_jumlah INTEGER,

    harga_awal INTEGER,
    harga_setelah_diskon INTEGER,
    persen_diskon REAL,

    tanggal_transaksi DATETIME,
    bulan TEXT,

    is_weekend INTEGER,
    is_ramadhan INTEGER,
    ramadhan_week INTEGER,

    product_age_week INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weekly_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nama_variasi TEXT,
    variasi_encoded INTEGER,

    tahun INTEGER,
    minggu_ke INTEGER,

    total_net_jumlah INTEGER,
    avg_diskon REAL,

    total_weekend INTEGER,
    total_ramadhan INTEGER,
    ramadhan_week INTEGER,

    product_age_week INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lag_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nama_variasi TEXT,
    minggu_ke INTEGER,
    tahun INTEGER,

    lag_1 INTEGER,
    lag_2 INTEGER,
    rolling_mean_2 REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prediksi (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_buku     INTEGER REFERENCES buku(id),
    minggu_ke   INTEGER NOT NULL,
    tahun       INTEGER NOT NULL,
    prediksi    REAL NOT NULL,
    model_versi TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS laporan_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nama        TEXT NOT NULL,
    format      TEXT NOT NULL,
    ukuran_kb   INTEGER,
    status      TEXT DEFAULT 'selesai',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_penjualan_buku
ON penjualan(id_buku, tahun, minggu_ke);

CREATE TABLE IF NOT EXISTS laporan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_file TEXT,
    format TEXT,
    ukuran_kb INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);