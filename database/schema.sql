-- database/schema.sql

CREATE TABLE IF NOT EXISTS buku (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,

    -- dari excel
    judul       TEXT NOT NULL,         -- nama produk
    kategori    TEXT NOT NULL,         -- nama variasi

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
    rmse             REAL NOT NULL,
    mae              REAL NOT NULL,
    r2               REAL NOT NULL,
    mape             REAL NOT NULL,
    hyperparameter   TEXT NOT NULL,
    file_path        TEXT NOT NULL,
    status           TEXT DEFAULT 'archive',
    catatan          TEXT
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