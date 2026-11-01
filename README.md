# ICC CTCF Ölçer

Immunositokimya (ICC) floresan görüntülerinde hücre başına **CTCF (Corrected Total Cell Fluorescence)** ölçümü
için yerel, tarayıcı tabanlı araç. ImageJ/Fiji'deki elle yapılan iş akışını otomatikleştirir; ölçüm tanımları
ImageJ ile birebir aynıdır (Fiji ile doğrulandı).

```
CTCF = Integrated Density − (Area of selected cell × Mean fluorescence of background)
```
(McCloy et al., 2014, *Cell Cycle* 13:1400–1412)

## Özellikler
- FITC (+ aynı alanın DAPI) görüntüsü yükleme; tek merge görüntü desteği
- Ölçek çubuğundan otomatik kalibrasyon (µm/piksel) ve objektif tahmini
- Otomatik hücre/çekirdek sayımı; birbirine değen hücrelerin DAPI çekirdeklerine göre ayrılması
- Tıklayarak hücre seçimi veya "Tüm hücreleri seç"
- Otomatik ya da elle background kutuları (boyut ve sayı ayarlanabilir)
- Hücre başına Area, Mean, StdDev, Min, Max, IntDen, RawIntDen, CTCF, doymuş piksel sayısı
- CSV / Excel (Cells, Group_summary, Background, Methods sayfaları), ROI görüntüsü
- Grafik (bar / box / violin; PNG 600 dpi, PDF, SVG) ve istatistik (Welch t, Mann–Whitney, ANOVA, Kruskal–Wallis, Tukey HSD)
- **ImageJ/Fiji karşılaştırma paketi:** ölçülen kanal (TIFF) + aynı ROI'ler (RoiSet.zip)
- **Elle çizim karşılaştırması:** Fiji'de çizilmiş RoiSet.zip yüklenir → Dice, IoU, alan ve CTCF farkı

## Kurulum

| Sistem | Kurulum | Başlatma |
|---|---|---|
| macOS 11+ (Big Sur, Monterey, …; Intel ve Apple Silicon) | Terminal: `./install_mac.sh` | Masaüstündeki **ICC CTCF Ölçer** |
| Windows 10/11 | `install_windows.bat` dosyasına çift tıklayın | Masaüstündeki **ICC CTCF Olcer** kısayolu |

Kurulum betikleri [uv](https://docs.astral.sh/uv/) ile Python 3.12 ortamını ve `requirements.txt`'teki sabit
sürümleri kurar (internet gerekir, ~300 MB). Uygulama tarayıcıda `http://localhost:8517` adresinde açılır;
görüntüler bilgisayardan dışarı gönderilmez. Önerilen tarayıcı: güncel Chrome / Edge / Firefox.

Durdurmak için: macOS `./stop.sh`; Windows'ta küçültülmüş "ICC CTCF Olcer sunucu" penceresini kapatın.

## İş akışı
1. Sol panelden FITC görüntüsünü ve **aynı alanın DAPI görüntüsünü** yükleyin.
2. Kalibrasyon, hücre ve çekirdek sayısı otomatik gelir. "Hücre ayırma" göstergesini kontrol edin.
3. Görüntüde hücreye tıklayarak seçin/bırakın veya **Tüm hücreleri seç**.
4. Background: otomatik veya elle tıklayarak kutu ekleme.
5. **Sonuç tablosuna ekle** → her görüntü için tekrarlayın (Grup etiketini değiştirerek).
6. CSV / Excel / grafik indirin. **Sekmeyi kapatmadan önce indirin**; tablo yalnızca açık oturumda tutulur.

## Ölçüm tanımları (ImageJ ile aynı)
- Area = piksel sayısı × (µm/piksel)²
- IntDen = Area × Mean (kalibre birim) · RawIntDen = Σ piksel değerleri
- StdDev = örneklem SD (n−1)
- CTCF = IntDen − Area × Mean_background; CTCF_per_Area = Mean − Mean_background
- ImageJ poligon kuralı: piksel merkezi poligon içindeyse dahil

## Notlar
- ⚠️ **Birbirine değen hücreler varsa aynı alanın DAPI görüntüsünü mutlaka yükleyin.** DAPI olmadan iki hücre
  arasındaki sınır yalnızca şekle göre çizilir (test: hücre başına ~%5 alan/CTCF farkı, Dice 0.97). Uygulama
  "Hücre ayırma" göstergesinde kullanılan modu ve değen hücre çiftlerini gösterir; sonuç tablosuna `Segmentation`
  ve `Touching_pairs` sütunları olarak yazılır.
- Renkli kamera (ör. Olympus DP74) görüntülerinde FITC için varsayılan ölçüm kanalı Yeşil (G)'dir. ImageJ'de RGB
  görüntüyü doğrudan ölçtüyseniz uyum için "ImageJ RGB→8-bit (R+G+B)/3" seçin.
- Karşılaştırılan tüm görüntüler aynı pozlama/kazanç ayarıyla, işlenmemiş (Photoshop'suz) çekilmiş olmalıdır.
- Background = 0 çıkıyorsa kamera siyah seviyesi kırpılmıştır; CTCF ≈ IntDen olur.

## Doğrulama
- **Fiji ile hesaplama eşdeğerliği:** aynı ROI'lerle Area, Mean, StdDev, Min, Max, IntDen birebir aynı (Fiji, 2026-10-31).
- **Elle çizimle uyum (ön veri, 1 görüntü, 2 değen hücre):** Dice 0.92–0.94; CTCF farkı −1.9 % ve +8.0 %.
  Fark esas olarak değen hücreler arasındaki bölme çizgisinden kaynaklanır.

## Dosyalar
- `core.py` — görüntü işleme ve ölçüm (arayüzden bağımsız)
- `app.py` — Streamlit arayüzü
- `install_mac.sh`, `start.sh`, `stop.sh`, `run.command` — macOS
- `install_windows.bat`, `start_windows.bat` — Windows
- `desktop.py` — **v2.0 masaüstü arayüzü (geliştiriliyor)**: `./run_desktop.command` (Mac) / `start_desktop.bat` (Windows)
- `report.py` — biriken sonuçlar, Excel/CSV, grafik ve istatistik (v2)
- `requirements-desktop.txt` — PySide6 6.9.3 (macOS 12 Monterey'i destekleyen son sürüm)
- `tests/test_core.py` — doğrulama testi (Fiji ile doğrulanmış değerler); `.venv/bin/python tests/test_core.py`

## Atıf
Bu aracı bir yayında kullanırsanız `CITATION.cff` dosyasındaki bilgilerle atıf yapın.
