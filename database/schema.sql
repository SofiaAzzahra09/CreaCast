-- database/schema.sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    nama TEXT,
    role TEXT,
    foto BLOB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tambahkan satu user default jika tabel kosong
INSERT OR IGNORE INTO users (id, username, password, nama, role) 
VALUES (1, 'admin', 'admin123', 'Administrator', 'Admin');


-- ==========================================
-- BUKU
-- ==========================================
CREATE TABLE IF NOT EXISTS buku (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judul TEXT NOT NULL,
    kategori TEXT NOT NULL,

    penulis TEXT DEFAULT '-',
    penerbit TEXT DEFAULT '-',
    isbn TEXT DEFAULT '-',

    harga INTEGER NOT NULL DEFAULT 0,
    stok INTEGER NOT NULL DEFAULT 0,
    stok_min INTEGER NOT NULL DEFAULT 15,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- RAW DATA
-- ==========================================
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

-- ==========================================
-- CLEANED DATA
-- ==========================================
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

-- ==========================================
-- WEEKLY SALES
-- ==========================================
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

-- ==========================================
-- MODEL REGISTRY
-- ==========================================
CREATE TABLE IF NOT EXISTS model_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    versi TEXT NOT NULL UNIQUE,
    tanggal_training TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    jumlah_data INTEGER NOT NULL,

    mse REAL NOT NULL,
    rmse REAL NOT NULL,
    mae REAL NOT NULL,
    r2 REAL NOT NULL,

    hyperparameter TEXT NOT NULL,
    file_path TEXT NOT NULL,

    status TEXT DEFAULT 'nonaktif', -- aktif/nonaktif

    catatan TEXT
);

-- ==========================================
-- PREDIKSI
-- simpan hasil forecast per model
-- ==========================================
CREATE TABLE IF NOT EXISTS prediksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    id_buku INTEGER,

    model_versi TEXT NOT NULL,
    minggu_ke INTEGER NOT NULL,
    tahun INTEGER NOT NULL,
    prediksi REAL NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(model_versi)
        REFERENCES model_registry(versi),

    FOREIGN KEY(id_buku)
        REFERENCES buku(id)
);

-- ==========================================
-- LAPORAN
-- ==========================================
CREATE TABLE IF NOT EXISTS laporan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_file TEXT,
    format TEXT,
    ukuran_kb INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- INDEX
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_weekly_sales
ON weekly_sales(tahun, minggu_ke);

CREATE INDEX IF NOT EXISTS idx_model_registry
ON model_registry(versi);

CREATE INDEX IF NOT EXISTS idx_prediksi_model
ON prediksi(model_versi);