# services/report_service.py
import io
import pandas as pd
from datetime import datetime


def _load_reportlab():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, Image)
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError as exc:
        raise ImportError(
            "Module 'reportlab' tidak ditemukan. "
            "Install package ini dengan `pip install -r requirements.txt`."
        ) from exc

    return A4, colors, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, getSampleStyleSheet


class ReportService:
    """
    Membuat laporan dalam format PDF, CSV, dan XLSX.
    Menerima data dari db_service dan hasil prediksi XGBoost.
    """

    def __init__(self, db_service):
        self.db = db_service

    # ── PDF ────────────────────────────────────────────────────────────
    def buat_pdf_prediksi(self,
                           minggu: int,
                           forecast: list,
                           metrics: dict,
                           stok_kritis: pd.DataFrame) -> bytes:
        """
        Generate laporan prediksi mingguan sebagai bytes PDF.
        Kembalikan bytes agar langsung dipakai st.download_button.
        """
        buf = io.BytesIO()
        A4, colors, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, getSampleStyleSheet = _load_reportlab()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                 topMargin=40, bottomMargin=40,
                                 leftMargin=50, rightMargin=50)
        styles = getSampleStyleSheet()
        elems  = []

        # Header
        elems.append(Paragraph(
            f"<b>Creatroka</b> — Laporan Prediksi Permintaan Mingguan",
            styles['Title']))
        elems.append(Paragraph(
            f"Periode: Minggu ke-{minggu} · Model XGBoost v3 · "
            f"Dibuat: {datetime.now().strftime('%d %B %Y')}",
            styles['Normal']))
        elems.append(Spacer(1, 14))

        # Ringkasan metrik
        elems.append(Paragraph("<b>1. Metrik Evaluasi Model</b>", styles['Heading2']))
        metric_data = [
            ['RMSE', 'MAE', 'R²', 'MAPE'],
            [str(metrics['rmse']), str(metrics['mae']),
             str(metrics['r2']),   f"{metrics['mape']}%"]
        ]
        t = Table(metric_data, colWidths=[110]*4)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1D9E75')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f0')]),
        ]))
        elems.append(t)
        elems.append(Spacer(1, 14))

        # Tabel forecast
        elems.append(Paragraph("<b>2. Forecast 4 Minggu ke Depan</b>", styles['Heading2']))
        fc_data = [['Minggu', 'Prediksi', 'Batas Bawah', 'Batas Atas']]
        for i, pred in enumerate(forecast):
            margin = round(pred * 0.04 * (i+1))
            fc_data.append([
                f"M-{minggu+i+1}",
                str(round(pred)),
                str(round(pred - margin)),
                str(round(pred + margin))
            ])
        t2 = Table(fc_data, colWidths=[100, 110, 110, 110])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#534AB7')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f0')]),
        ]))
        elems.append(t2)
        elems.append(Spacer(1, 14))

        # Tabel stok kritis
        elems.append(Paragraph("<b>3. Rekomendasi Restock Mendesak</b>", styles['Heading2']))
        sk_data = [['Judul Buku', 'Stok', 'ROP', 'Restock', 'Status']]
        for _, r in stok_kritis.iterrows():
            sk_data.append([
                r['judul'], str(r['stok']),
                str(r['reorder_point']),
                f"+{r['jumlah_restock']}",
                r['status'].upper()
            ])
        t3 = Table(sk_data, colWidths=[180, 60, 60, 70, 60])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EF9F27')),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN',      (0,1), (-1,-1), 'CENTER'),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f0')]),
        ]))
        elems.append(t3)

        doc.build(elems)
        return buf.getvalue()

    # ── CSV ────────────────────────────────────────────────────────────
    def buat_csv_penjualan(self, periode: str = 'minggu_ini') -> bytes:
        df = self.db.get_penjualan(periode=periode)
        return df.to_csv(index=False).encode('utf-8')

    # ── XLSX ───────────────────────────────────────────────────────────
    def buat_xlsx_prediksi(self,
                            forecast: list,
                            stok: pd.DataFrame) -> bytes:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            pd.DataFrame({
                'minggu':   [f"M+{i+1}" for i in range(len(forecast))],
                'prediksi': [round(f) for f in forecast]
            }).to_excel(writer, sheet_name='Forecast', index=False)

            stok[['judul','stok','safety_stock',
                  'reorder_point','jumlah_restock','status']
                ].to_excel(writer, sheet_name='Rekomendasi Stok', index=False)
        return buf.getvalue()

    # ── Simpan riwayat ─────────────────────────────────────────────────
    def simpan_riwayat(self, nama: str, format: str, ukuran_kb: int):
        self.db.execute("""
            INSERT INTO laporan_history (nama, format, ukuran_kb, status)
            VALUES (?, ?, ?, 'selesai')
        """, (nama, format, ukuran_kb))