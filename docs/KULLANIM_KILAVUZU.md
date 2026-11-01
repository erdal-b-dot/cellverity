# ICC CTCF Ölçer 2 — Kullanım Kılavuzu

*Sürüm 2.0.0 · Erdal Balcan, Manisa Celal Bayar Üniversitesi · MIT lisansı · DOI: [10.5281/zenodo.23860021](https://doi.org/10.5281/zenodo.23860021)*

Kaynak kod ve indirmeler: https://github.com/erdal-b-dot/icc-ctcf-olcer · English guide: `USER_GUIDE.md`

---

## İçindekiler
1. [Program ne yapar?](#1-program-ne-yapar)
2. [Kurulum](#2-kurulum)
3. [Görüntüleriniz nasıl olmalı?](#3-goruntuleriniz-nasil-olmali)
4. [Hızlı başlangıç (5 dakika)](#4-hizli-baslangic-5-dakika)
5. [Pencerenin bölümleri](#5-pencerenin-bolumleri)
6. [Tek görüntü ölçmek — adım adım](#6-tek-goruntu-olcmek-adim-adim)
7. [Hücre sınırlarını elle düzeltmek](#7-hucre-sinirlarini-elle-duzeltmek)
8. [Bir klasörü toplu ölçmek](#8-bir-klasoru-toplu-olcmek)
9. [Sonuçlar, Excel ve otomatik kayıt](#9-sonuclar-excel-ve-otomatik-kayit)
10. [Grafik ve istatistik (gruplar arası karşılaştırma)](#10-grafik-ve-istatistik-gruplar-arasi-karsilastirma)
11. [Fiji köprüsü ve yöntem doğrulaması](#11-fiji-koprusu-ve-yontem-dogrulamasi)
12. [Uyarılar: ne anlama gelir, ne yapmalı?](#12-uyarilar-ne-anlama-gelir-ne-yapmali)
13. [Makale için: yöntem metni ve atıf](#13-makale-icin-yontem-metni-ve-atif)
14. [Sorun giderme](#14-sorun-giderme)
15. [Teknik ayrıntılar](#15-teknik-ayrintilar)

---

## 1. Program ne yapar?

Immunositokimya (ICC) floresan görüntülerinde **hücre başına CTCF** (Corrected Total Cell Fluorescence) ölçer:

> **CTCF = Integrated Density − (Hücre alanı × Background ortalaması)**
> (McCloy ve ark., 2014, *Cell Cycle* 13:1400–1412)

ImageJ'de elle yapılan iş akışını otomatikleştirir:

| ImageJ'de elle | Bu programda |
|---|---|
| Set Scale ile kalibrasyon | Ölçek çubuğu **ve üzerindeki değer** (20 µm, 50 µm) otomatik okunur |
| Her hücreyi Polygon ile çizmek | Hücreler FITC'den, değen hücreler DAPI çekirdeklerinden otomatik ayrılır |
| 3 background alanı çizip ölçmek | Hücrelerden uzak 3 kutu otomatik yerleşir (taşınabilir, elle eklenebilir) |
| Measure → Excel'e kopyalama → formül | Tablo, Excel, grup özeti, grafik ve istatistik tek tıkla |

**Ölçümler ImageJ/Fiji ile birebir aynıdır.** Aynı hücre sınırları verildiğinde Area, Mean, StdDev, Min, Max, IntDen ve RawIntDen değerleri Fiji'ninkiyle aynı çıkar (en büyük fark < 0.00001 %). Bunu programın içinden kendiniz de kontrol edebilirsiniz: **Fiji ▸ Fiji ile doğrula** ([Bölüm 11](#11-fiji-koprusu-ve-yontem-dogrulamasi)).

Görüntüleriniz bilgisayarınızdan dışarı **hiçbir yere gönderilmez**; program internetsiz çalışır.

**Dil:** Arayüz bilgisayarınızın diline göre Türkçe ya da İngilizce açılır. Değiştirmek için **Görünüm ▸ Dil / Language** (yeniden başlatınca geçerli olur). Excel çıktısı her zaman İngilizcedir.

---

## 2. Kurulum

### 2.1 Hazır program (önerilen — Python gerekmez)

| Bilgisayar | İndirilecek dosya | En düşük sistem |
|---|---|---|
| Apple Silicon Mac (M1/M2/M3/M4) | `ICC_CTCF_Olcer_2.0.0_mac_AppleSilicon.dmg` | macOS 12.3 |
| Intel Mac (ör. eski iMac) | `ICC_CTCF_Olcer_2.0.0_mac_Intel.dmg` | macOS 12.0 (Monterey) |
| Windows 10/11 (64-bit) | `ICC_CTCF_Olcer_2.0.0_Windows.zip` | Windows 10 |

> Mac'inizin işlemcisini öğrenmek için: Apple menüsü ▸ **Bu Mac Hakkında**. "Çip: Apple M…" yazıyorsa Apple Silicon, "İşlemci: Intel…" yazıyorsa Intel paketini kullanın.
> Monterey'de Apple Silicon paketi için **macOS 12.3 veya üstü** gerekir: Sistem Tercihleri ▸ Yazılım Güncelleme.

**Mac'te:**
1. `.dmg` dosyasına çift tıklayın → açılan pencerede **ICC CTCF Ölçer** simgesini yandaki **Uygulamalar** klasörüne sürükleyin. Sonra pencereyi kapatıp Finder kenar çubuğundaki diski çıkarın (⏏).
2. **İlk açılışta** çift tıklamayın: uygulamaya **sağ tıklayın ▸ Aç ▸ Aç**. (Program Apple'a ücretli imzalatılmadığı için macOS "tanınmayan geliştirici" uyarısı verir; bu bir kez yapılır.)
3. "Hasarlı, Çöp Sepeti'ne taşıyın" uyarısı çıkarsa (internetten indirilen dosyalarda olur), Terminal'de bir kez şunu çalıştırın:
   `xattr -cr "/Applications/ICC CTCF Ölçer.app"`

**Windows'ta:**
1. Zip'e sağ tıklayın ▸ **Tümünü ayıkla**. Klasörü örneğin `Belgeler` içine koyun (zip'in içinden çalıştırmayın).
2. `ICC CTCF Olcer.exe`'ye çift tıklayın. "Windows bilgisayarınızı korudu" çıkarsa **Ek bilgi ▸ Yine de çalıştır**.
3. Masaüstü kısayolu: exe'ye sağ tıklayın ▸ Gönder ▸ Masaüstü (kısayol oluştur).

**İndirme adresi:** https://github.com/erdal-b-dot/icc-ctcf-olcer/releases (en yeni sürüm en üstte).

**Başka bir bilgisayara aktarmak:** paket dosyasını paylaşım bağlantısı, USB bellek ya da e-postayla (≈100 MB) gönderin, ya da yukarıdaki indirme adresini paylaşın. Yeni paket üretmek: kaynak kod klasöründe `./build_mac.sh` (Mac) / `build_windows.bat` (Windows).

### 2.2 Geliştirici kurulumu (kaynak koddan)
Python ortamıyla çalıştırmak isterseniz (güncellemeleri `git pull` ile almak için):
- Mac: `./install_mac.sh`, sonra `./run_desktop.command`
- Windows: `install_windows.bat`, sonra `start_desktop.bat`

### 2.3 Fiji (isteğe bağlı ama önerilir)
Fiji köprüsü ([Bölüm 11](#11-fiji-koprusu-ve-yontem-dogrulamasi)) için Fiji'nin kurulu olması gerekir: https://imagej.net/software/fiji/downloads
Program Fiji'yi şu yerlerde kendisi arar: `İndirilenler/Fiji`, `Uygulamalar/Fiji`, ana klasör (`~/Fiji`, `C:\Fiji`). Başka yerdeyse: **Fiji ▸ Fiji konumunu seç…** (bir kez seçilir, hatırlanır).

### 2.4 Eski tarayıcı sürümü (v1)
v1 (tarayıcıda açılan Streamlit sürümü) aynen çalışmaya devam eder. v1 ile v2 aynı hücre sınırlarında aynı sayıları verir; ancak **çekirdek algılama yöntemi farklı** olduğu için değen hücrelerde sınırlar biraz farklı çizilir ([Bölüm 15](#15-teknik-ayrintilar)). Bir çalışmanın tüm görüntülerini **aynı sürümle** ölçün.

---

## 3. Görüntüleriniz nasıl olmalı?

Program ne kadar iyi olursa olsun, ölçümün geçerliliği görüntüye bağlıdır.

**Mutlaka:**
- **Ham, tek kanal görüntü.** Mikroskobun (cellSens vb.) doğrudan kaydettiği FITC görüntüsü. Photoshop'tan geçmiş, parlaklık/kontrast ayarlanmış ya da kanalları birleştirilmiş (**merge**) görüntüler CTCF için **kullanılamaz** — program bunları tanır ve uyarır.
- **Karşılaştırılan tüm görüntüler aynı ayarla çekilmiş olmalı:** aynı objektif, pozlama süresi, kazanç (gain), lamba gücü, beyaz dengesi.
- **Aynı objektif.** 20× ile 40× görüntüleri birbiriyle karşılaştırmayın — program karışık objektif görürse uyarır.
- **Doymuş (saturated) piksel olmamalı.** Program doymuş piksel sayısını her hücre için raporlar ("Doymuş px" sütunu).

**Önerilir:**
- **Aynı alanın DAPI görüntüsü.** Birbirine değen hücreleri doğru ayırmak için şart ([Uyarılar](#12-uyarilar-ne-anlama-gelir-ne-yapmali)).
- **Ölçek çubuğu görüntüde kalsın.** Program kalibrasyonu çubuktan okur (cellSens sağ alt köşe beyaz kutu).
- **TIFF** kaydı JPEG'den iyidir (JPEG kayıplıdır). Aynı çalışmada tüm görüntüler aynı formatta olmalı.

**Test edilen ekipman:** Olympus BX43 floresan mikroskop, Olympus DP74 renkli kamera, cellSens Entry yazılımı. **DP74 notu:** Bu renkli kamerada FITC sinyali sarı-yeşil, DAPI ise **turkuaz** görünür. Program FITC'yi **yeşil (G) kanalından** ölçer; FITC/DAPI ayrımını parlak piksellerin mavi/kırmızı oranından yapar.

---

## 4. Hızlı başlangıç (5 dakika)

> Denemek için örnek görüntüler: repodaki [`examples/`](https://github.com/erdal-b-dot/icc-ctcf-olcer/tree/main/examples) klasörü (beklenen sonuçlarıyla iki FITC + DAPI çifti, CC BY 4.0).

1. Programı açın.
2. Finder/Gezgin'de **FITC ve DAPI dosyalarını birlikte seçip** pencereye sürükleyin. Program hangisinin DAPI olduğunu rengine göre anlar.
3. Sağ panelde kontrol edin: **Kalibrasyon** (ör. 0.1449 µm/piksel, 20 µm, *etiketten okundu*), **Objektif**, **Hücre sayısı**, yeşil **"Hücre ayırma: DAPI çekirdekleri"** kutusu.
4. **Tüm hücreleri seç** (ya da ölçülecek hücrelere tıklayın — sarıya döner). Alttaki **Hücreler** sekmesinde CTCF görünür.
5. Sağ panelde **Grup / koşul** (ör. *Kontrol*) ve **Deney / tekrar** (ör. *1*) yazın → **➕ Sonuç tablosuna ekle** (⌘↩ / Ctrl+Enter).
6. Sonraki görüntü: **⌘W** ile kapatın, yenisini sürükleyin, grubu değiştirin, ekleyin.
7. Bitince: **Excel'e kaydet** (⌘E) ve **Grafik…** (⌘G).

Çok görüntü varsa 4–6. adımlar yerine **Klasörü toplu ölç** (⌘B) kullanın ([Bölüm 8](#8-bir-klasoru-toplu-olcmek)).

---

## 5. Pencerenin bölümleri

| Bölüm | İçerik |
|---|---|
| **Menüler** | Dosya · Sonuçlar · Fiji · Düzelt · Görünüm · Yardım |
| **1. araç çubuğu** | FITC aç · DAPI aç · Görüntüleri kapat · Sığdır/Yakınlaştır/Uzaklaştır · **Görüntü:** FITC / DAPI / Birleşik · Çekirdek sınırları |
| **2. araç çubuğu** | **Sınır düzeltme:** Seç · Böl · Birleştir · Sil · Çiz · Geri al · Yinele — **Sonuçlar:** tabloya ekle · toplu ölç · Excel · Grafik · Fiji ile doğrula |
| **Görüntü alanı** | Fare tekerleği: yakınlaştır · Sürükle: kaydır · Tıkla: hücre seç |
| **Sağ panel** | Dosyalar, ölçek çubuğu, kalibrasyon, objektif, sayılar, hücre ayırma göstergesi, hücre seçimi, background ayarları, sonuçlar (grup, deney), çizgi açıklaması, görüntü parlaklığı |
| **Alt sekmeler** | Hücreler · Background kutuları · Biriken sonuçlar · Grup özeti |

**Görüntüdeki çizgiler:**

| Çizgi | Anlamı |
|---|---|
| Gri, numaralı | Programın bulduğu hücre sınırı |
| **Sarı** | Seçili (ölçülen) hücre |
| **Mor** | DAPI'den bulunan çekirdek sınırı |
| **Kırmızı kare** (BG1, BG2…) | Background kutusu |

**Görüntü parlaklığı** kaydırıcısı ve **Görüntü: FITC/DAPI/Birleşik** seçimi **yalnızca ekranı** değiştirir; ölçüm her zaman ham FITC (yeşil kanal) verisinden yapılır.

---

## 6. Tek görüntü ölçmek — adım adım

### 6.1 Görüntüleri açmak
- **Sürükle-bırak** (en kolay): FITC + DAPI'yi birlikte sürükleyin.
- **FITC aç… (⌘O)** ve **DAPI aç… (⌘D)** düğmeleri.
- Yanlış düğmeyle açarsanız (ör. mavi dosyayı "FITC aç" ile) program sorar: *"Bu bir DAPI görüntüsüne benziyor, DAPI olarak açılsın mı?"*
- **Yeni bir FITC açıldığında önceki alanın DAPI'si otomatik kaldırılır** (başka alanın çekirdekleri yanlış ayırmaya yol açar). Yeni alanın DAPI'sini de açın.
- **Görüntüleri kapat (⌘W):** pencereyi boşaltır; biriken sonuçlar korunur.

### 6.2 Kalibrasyonu kontrol etmek
Sağ panelde **Kalibrasyon** satırı kaynağı da söyler:
- *etiketten okundu* — ölçek çubuğunun altındaki değer (20 µm, 50 µm) okundu. ✅
- *elle girildi* — **Ölçek çubuğu** kutusuna sizin yazdığınız değer.
- *etiket OKUNAMADI, varsayıldı* — kırmızı uyarı çıkar; görüntüdeki değeri **Ölçek çubuğu** kutusuna yazın.

> ⚠️ Ölçek değeri yanlışsa **alan ve IntDen kat kat yanlış** çıkar (ör. 50 µm yerine 20 µm: 6.25 kat). Bu yüzden her yeni görüntüde kalibrasyon satırına bir göz atın.

DP74 + cellSens için bilinen değerler: **20 µm = 138 px → 0.1449 µm/px (40×)**; **50 µm = 172 px → 0.2907 µm/px (20×)**.

### 6.3 Hücre ayırma göstergesi
| Gösterge | Anlamı | Ne yapmalı |
|---|---|---|
| 🟢 **DAPI çekirdekleri** | Değen hücreler çekirdeklere göre ayrıldı | — |
| 🟡 **Yalnızca şekil (değen hücre yok)** | DAPI yok ama gerek de yok | — |
| 🔴 **Yalnızca şekil — N değen hücre çifti** | Değen hücreler yalnız şekle göre bölündü (~%5 hata) | Aynı alanın DAPI'sini açın |
| 🔴 **DAPI bu FITC ile aynı alana ait görünmüyor** | Çekirdeklerin çoğu hücrelerin dışında | Doğru DAPI'yi açın (numaralar ardışık olsa bile alan farklı olabilir) |

### 6.4 Hücre seçmek
- Hücreye **tıklayın** → sarı olur, ölçülür; tekrar tıklayın → bırakılır.
- **Tüm hücreleri seç** / **Seçimi temizle**.
- Görüntü kenarında **kesilmiş** hücreleri ölçmeyin (alanları eksik ölçülür).

### 6.5 Background
- **Otomatik** (varsayılan): hücrelerden ≥ 40 piksel uzak, sinyal/debris içermeyen, hücrelere en yakın **3 kutu** (50×50 piksel). Boyut ve sayı sağ panelden değiştirilebilir.
- **Kutuları taşımak:** kutunun üzerine gelin (el imleci), basılı tutup sürükleyin. Bıraktığınız anda yeniden ölçülür. Otomatik bir kutuyu taşırsanız mod **Elle**'ye geçer, diğer kutular yerinde kalır.
- **Elle:** boş alana tıklayın → kutu eklenir; kutuya tıklayın → silinir. **Elle kutuları temizle**.
- Bir hücrenin üzerine taşan kutu kabul edilmez (eski yerine döner).
- Kutu başına değerler: alttaki **Background kutuları** sekmesi.

> ℹ️ **Background = 0 çıkıyorsa** kamera/cellSens koyu arka planı sıfıra kırpmıştır; CTCF = IntDen olur. Tüm görüntüler aynı ayarla çekildiyse karşılaştırma geçerlidir.

### 6.6 Sonuç tablosuna eklemek
- **Grup / koşul:** ör. *Kontrol*, *Ax 10 µM 24 sa*. Grafik ve istatistik bu etikete göre gruplar.
- **Deney / tekrar:** bağımsız deney (biyolojik tekrar) numarası: *1*, *2*, *3*… İstatistiği deney ortalamalarıyla yapmak için gerekir ([Bölüm 10](#10-grafik-ve-istatistik-gruplar-arasi-karsilastirma)).
- **➕ Sonuç tablosuna ekle (⌘↩).** Aynı görüntüyü yeniden eklerseniz eskisinin yerine geçer (iki kez sayılmaz).

---

## 7. Hücre sınırlarını elle düzeltmek

Otomatik sınırlar çoğu görüntüde iyidir; yoğun kümelerde, debris'te ya da sönük hücrelerde düzeltme gerekebilir. **2. araç çubuğu ▸ Sınır düzeltme**:

| Araç | Nasıl | Ne zaman |
|---|---|---|
| **Seç** | Normal mod | Hücre seçmek, kutu taşımak, kaydırmak |
| **Böl** | Yapışık hücrelerin üzerine **bir kenardan öbür kenara** çizgi çekin | İki (veya daha çok) hücre tek hücre sayıldıysa |
| **Birleştir** | Önce bir hücreye, sonra komşusuna tıklayın | Bir hücre ikiye bölündüyse |
| **Sil** | Bölgeye tıklayın | Debris ya da hücre olmayan bölge |
| **Çiz** | Hücre sınırını fareyle çizin; bırakınca kapanır | Kaçırılan hücre ya da kötü çizilmiş sınır (çizim, altındaki hücrelerin üzerine yazar) |
| **Geri al / Yinele** | ⌘Z / ⇧⌘Z (Windows: Ctrl+Z / Ctrl+Y), 30 adım | Her işlem geri alınabilir |

- Böl ve Çiz modlarında görüntüyü kaydırmak için **⌥ Option (Windows: Alt)** tuşuna basılı tutup sürükleyin.
- Bölme ve birleştirmede **toplam alan korunur**.
- Düzeltmeler Excel'de **Manual_edits** sütununa yazılır (ör. *birleştir 1+2; böl 1*).
- Ölçek değeri değiştirilince görüntü yeniden analiz edilir ve **düzeltmeler sıfırlanır** (altta uyarı çıkar). Önce kalibrasyonu, sonra düzeltmeleri yapın.

---

## 8. Bir klasörü toplu ölçmek

**Sonuçlar ▸ Klasörü toplu ölç… (⌘B)**

### 8.1 Önerilen klasör düzeni
```
Deneyler/
  Deney_1/
    Kontrol/      ← FITC + DAPI görüntüleri
    Uygulama1/
    Uygulama2/
  Deney_2/
    Kontrol/
    ...
```
- **Grup** = görüntünün bulunduğu klasörün adı; **Deney** = onun bir üstündeki klasörün adı.
- Tek bir deney klasörünü seçerseniz (ör. `Deney_1`) deney adı o klasörün adı olur.
- İkisi de ölçmeden önce tabloda değiştirilebilir.

### 8.2 FITC–DAPI eşleştirme
Her FITC, **aynı klasörde ±3 numara içindeki** DAPI'ler arasından, **çekirdeklerin hücrelerle gerçekten örtüştüğü** olanla eşleştirilir. Örtüşme **şansa göre düzeltilmiş** bir skordur (1 = bütün çekirdekler hücre içinde, 0 = rastgele yerleşimden farksız); eşleşme için ≥ 0.5 gerekir. Ham oran kullanılsaydı, hücrelerin alanın yarısını kapladığı kalabalık görüntülerde başka alana ait bir DAPI bile %50 örtüşürdü. Ardışık numara her zaman aynı alan demek değildir — program bunu görüntünün kendisinden kontrol eder.

| Durum | Anlamı |
|---|---|
| 🟢 **hazır** | Çift bulundu (Örtüşme sütununda yüzde) |
| 🟠 **DAPI yok** | Uygun DAPI bulunamadı; hücreler yalnız şekle göre ayrılacak |
| ⚪ **atlandı: kamera bilgisi yok** | Merge ya da yeniden kaydedilmiş görüntü |
| ⚪ **atlandı: işlenmiş görüntü** | Photoshop vb. ile kaydedilmiş |
| ⚪ **atlandı: FITC mi DAPI mi anlaşılamadı** | Renk belirsiz (ör. merge) |
| ⚪ **atlandı: eşleşmeyen DAPI** | Hiçbir FITC'ye ait olmayan DAPI |

### 8.3 Ölçüm
- İşaretli satırlar ölçülür; istemediklerinizin işaretini kaldırın.
- Her görüntüde **tüm hücreler** + **otomatik background** (sağ paneldeki kutu boyutu/sayısı).
- **Kenara değen (kesik) hücreler** varsayılan olarak hariç tutulur.
- Excel'de **Selection** sütunu: *manual click* ya da *batch: all cells, edge excluded*.
- Toplu ölçümden sonra şüpheli görüntüleri tek tek açıp kontrol etmeniz önerilir (özellikle yoğun kümeler).

---

## 9. Sonuçlar, Excel ve otomatik kayıt

### 9.1 Excel dosyasının sayfaları
| Sayfa | İçerik |
|---|---|
| **Cells** | Hücre başına tüm ölçümler ve bağlam bilgisi |
| **Group_summary** | Grup başına n, ortalama, SD, SEM, medyan, min, max (CTCF) |
| **Image_means** | Görüntü (alan) ortalamaları — GraphPad'e yapıştırmaya hazır |
| **Experiment_means** | Deney ortalamaları — yayın istatistiği için önerilen birim |
| **Background** | Kutu başına background ölçümleri |
| **Methods** | Formüller, yöntemler, atıf |
| **Validation**, **Validation_summary** | Elle (Fiji) vs otomatik karşılaştırma ve Bland–Altman özeti (varsa) |

### 9.2 Cells sayfasındaki önemli sütunlar
| Sütun | Anlamı |
|---|---|
| Area, Mean, StdDev, Min, Max, IntDen, RawIntDen | ImageJ ile aynı tanımlar |
| BG_Mean, CTCF, CTCF_per_Area | Background ortalaması, CTCF, CTCF/alan (= Mean − BG_Mean) |
| Saturated_px | Doymuş piksel sayısı (0 olmalı) |
| um_per_px, Scale_bar_um, Scale_source, Objective | Kalibrasyon ve kaynağı (label / user / default) |
| BG_mode, BG_box_px, BG_n | Background yöntemi |
| Segmentation, Nucleus_method, DAPI_overlap, Touching_pairs | Hücre ayırma bilgisi |
| Selection, Manual_edits | Hücrelerin nasıl seçildiği, elle düzeltmeler |
| Fiji_check | Fiji ile doğrulandıysa sonuç |
| App_version, Timestamp | Program sürümü, tarih |

### 9.3 Diğer çıktılar
- **CSV** (Türkçe karakterler Excel'de doğru açılır).
- **ROI görüntüsü (PNG):** işaretli sınırlar ve kutularla.
- **ImageJ/Fiji karşılaştırma paketi (ZIP):** ölçülen kanal (TIFF) + ROI'ler (RoiSet.zip) + talimat (`NASIL_KULLANILIR.txt` / `HOW_TO_USE.txt`, ölçek değeriyle).

### 9.4 Kaybetmemek için
- **Otomatik kayıt:** her eklemeden sonra `Belgeler/ICC CTCF Olcer/otomatik_kayit.xlsx`. Program çökse ya da elektrik gitse bile kaybolmaz; yeniden açınca *"devam edilsin mi?"* diye sorar.
- **Önceki sonuçları aç (Excel)…:** kaydettiğiniz bir Excel'i yükleyip ölçmeye devam edin (aynı görüntü iki kez sayılmaz).
- Kaydedilmemiş sonuçla programı kapatırsanız kaydetmek isteyip istemediğiniz sorulur.

---

## 10. Grafik ve istatistik (gruplar arası karşılaştırma)

**Sonuçlar ▸ Grafik ve istatistik… (⌘G)**

| Ayar | Seçenekler |
|---|---|
| **Kontrol grubu** | Dunnett testinin ve normalizasyonun referansı (adı *Kontrol/Control/ilaçsız* ile başlayan grup otomatik seçilir) |
| **Değişken** | CTCF · CTCF_per_Area · Mean · IntDen · Area |
| **İstatistik birimi** | Hücre · Görüntü ortalaması · **Deney ortalaması (önerilen)** |
| **Çoklu karşılaştırma** | **Dunnett** (her grup kontrole karşı) · Tukey HSD (tüm çiftler) |
| **Grafik tipi** | Bar (ortalama ± SEM) · Box · Violin — hepsinde tek tek noktalar |
| **Grup sırası** | Sürükleyerek değiştirin (kontrol hep başta, gri) |
| Normalize | Kontrol ortalaması = 1 |
| Yıldızlar | GraphPad gösterimi: ns, \* p<0.05, \*\* p<0.01, \*\*\* p<0.001, \*\*\*\* p<0.0001 |

**Testler:** 2 grup → Welch t-testi + Mann–Whitney U. 3+ grup → tek yönlü ANOVA + Kruskal–Wallis + Dunnett (veya Tukey).

### 10.1 Önemli: istatistik birimi (yalancı tekrar)
Aynı deneyden gelen hücreler birbirinden bağımsız değildir. Her hücreyi ayrı tekrar saymak **p değerini olduğundan küçük** gösterir (hakemlerin en sık yakaladığı hatalardan biri). Örnek (yapay veri, 3 deney × 3 görüntü × 6 hücre):

| Birim | n | Dunnett p (Uygulama vs Kontrol) |
|---|---|---|
| Hücre | 54 | 0.069 |
| Deney ortalaması | 3 | **0.62** |

**Öneri:** yayında istatistiği **bağımsız deney ortalamaları** (en az 3 deney) üzerinden yapın; hücre düzeyindeki noktaları grafikte gösterebilirsiniz. Program hücre düzeyinde test yaparsanız uyarır.

Dunnett p değerleri sayısal integrasyonla hesaplanır; program sabit tohum kullanır, **aynı veri her zaman aynı p'yi** verir.

Kaydet: grafik PNG (600 dpi), PDF, SVG; istatistik metni .txt.

---

## 11. Fiji köprüsü ve yöntem doğrulaması

**Fiji menüsü:**

### 11.1 Fiji ile doğrula (⌘⇧F)
Seçili hücreleri ve background kutularını **Fiji'nin kendi Measure motoruna arka planda** ölçtürür (Fiji penceresi açılmaz, ~5 saniye) ve sonuçları programınkilerle yan yana gösterir. Sonuç, görüntü sonuç tablosuna eklenince Excel'de **Fiji_check** sütununa yazılır (ör. *OK (1.54p99, max fark 3.3e-07 %)*). Seçim, kutu ya da sınır değişirse önceki doğrulama geçersiz sayılır.

### 11.2 Fiji'de aç
Fiji'yi arayüzüyle açar: görüntü, ölçek, ROI Manager'da tüm ROI'ler, Measure sonuçları. Dosyalar: `Belgeler/ICC CTCF Olcer/Fiji/<görüntü adı>/`.

### 11.3 Elle çizilmiş ROI'lerle karşılaştır (yöntem doğrulaması)
Programın otomatik sınırlarının elle çizime ne kadar yakın olduğunu ölçmek için (makale için önerilir):

1. Fiji'de FITC görüntüsünü açın. **Polygon** ya da **Freehand** aracıyla bir hücreyi çizin → **T** (ROI Manager'a ekle). Tüm hücreler için tekrarlayın.
2. ROI Manager ▸ **More » ▸ Save…** → `elle_RoiSet_<görüntü>.zip`
3. Programda aynı görüntüyü (ve DAPI'sini) açın → **Fiji ▸ Elle çizilmiş ROI'lerle karşılaştır…** → zip'i seçin.
4. Her elle ROI en çok örtüşen otomatik hücreyle eşleştirilir: alan farkı, CTCF farkı, **Dice** ve IoU (sınır örtüşmesi; 1 = tam).
5. **➕ Doğrulama tablosuna ekle.** 3–5 görüntü (ayrık + değen hücreler, farklı koşullar) için tekrarlayın.
6. **Fiji ▸ Yöntem doğrulama tablosu ve Bland–Altman…:** dağılım grafiği + Bland–Altman (yüzde fark), ortalama fark (bias), %95 uyum sınırları, Pearson r, Lin CCC, Dice.

**Öneri:** ≥ 30 hücre, ≥ 3 görüntü. İsterseniz aynı hücreleri birkaç saat sonra yeniden çizin (gözlemci içi değişkenlik): otomatik–elle farkı, elle–elle farkından büyük değilse yöntem en az elle ölçüm kadar güvenilirdir.

---

## 12. Uyarılar: ne anlama gelir, ne yapmalı?

### 12.1 Görüntü açarken
| Uyarı | Anlamı | Ne yapmalı |
|---|---|---|
| *Görüntü yazılımla işlenmiş görünüyor (Adobe Photoshop…)* | Dosya bir görüntü programında yeniden kaydedilmiş | Mikroskobun ham çıktısını kullanın |
| *Kamera bilgisi (EXIF) yok* | Merge ya da yeniden kaydedilmiş görüntü | Ham tek kanal FITC'yi kullanın |
| *… bir DAPI görüntüsüne benziyor, DAPI olarak açılsın mı?* | Dosya rengi düğmeyle uyuşmuyor | Genellikle **Evet** |
| *FITC ve DAPI görüntülerinin boyutları farklı; DAPI kullanılmadı* | İki dosya aynı çekim değil | Doğru DAPI'yi açın |
| *Yeni FITC açıldı; aynı alanın DAPI'sini açın* | Önceki alanın DAPI'si kaldırıldı | Yeni alanın DAPI'sini açın |

### 12.2 Kalibrasyon ve hücre ayırma
| Uyarı | Anlamı | Ne yapmalı |
|---|---|---|
| 🔴 *Ölçek çubuğunun değeri okunamadı; 20 µm varsayıldı* | Etiket okunamadı | Görüntüdeki değeri **Ölçek çubuğu** kutusuna yazın |
| *Ölçek çubuğu bulunamadı — piksel birimi* | Çubuk yok | Alan piksel² cinsinden; karşılaştırmalar yalnız aynı büyütmede geçerli |
| 🔴 *Hücre ayırma: yalnızca şekil — N değen hücre çifti* | DAPI yok, değen hücreler var | Aynı alanın DAPI'sini açın |
| 🔴 *DAPI bu FITC ile aynı alana ait görünmüyor* | Çekirdeklerin çoğu hücre dışında | Doğru DAPI'yi açın |
| *Yeniden analiz edildi: önceki elle düzeltmeler sıfırlandı* | Ölçek vb. değişti | Düzeltmeleri yeniden yapın |

### 12.3 Background
| Uyarı | Anlamı | Ne yapmalı |
|---|---|---|
| ℹ️ *Kutulardaki tüm pikseller 0* | Kamera siyah seviyesi kırpılmış; CTCF = IntDen | Tüm görüntüler aynı ayarla çekildiyse sorun değil |
| ⚠️ *Bazı kutularda sinyal/debris olabilir* | Kutuda parlak piksel var | Kutuyu sürükleyip temiz alana taşıyın |
| 🔴 *Background kutusu yok — CTCF hesaplanamaz* | Kutu yerleşecek boş alan yok / Elle modunda kutu yok | Kutu boyutunu küçültün ya da elle ekleyin |
| ⚠️ *Kutu bir hücreye taşıyor* | Kutu hücre üzerine konamaz | Biraz uzağa koyun |

### 12.4 Ölçüm tablosu
| Durum | Anlamı | Ne yapmalı |
|---|---|---|
| **Doymuş px > 0** | Hücrede kameranın üst sınırına ulaşmış pikseller var → CTCF olduğundan **düşük** | Pozlamayı düşürerek yeniden çekin ya da o hücreyi dışarıda bırakın |

### 12.5 İstatistik
| Uyarı | Anlamı | Ne yapmalı |
|---|---|---|
| ⚠️ *Her hücre ayrı tekrar sayıldı (yalancı tekrar riski)* | n = hücre sayısı | Yayında **Deney ortalaması** birimini kullanın |
| ⚠️ *Farklı objektifler karışık (20×, 40×)* | Gruplar farklı büyütmede çekilmiş | Yalnız aynı objektifle çekilmiş görüntüleri karşılaştırın |
| ⚠️ *Grup içi değişkenlik sıfır* | Aynı değerler tekrar ediyor (aynı görüntü iki kez?) | Tabloyu kontrol edin; test güvenilmez |
| ℹ️ *Grup başına 2 deney: test gücü düşük* | n < 3 | En az 3 bağımsız deney |
| *İstatistik için her grupta en az … gerekir* | Yetersiz veri | Daha çok görüntü/deney ekleyin |
| ⚠️ *Az hücre: r ve CCC anlamsız* (doğrulama) | Bland–Altman için az hücre | ≥ 30 hücre, ≥ 3 görüntü |

### 12.6 Toplu ölçüm ve Fiji
| Uyarı | Anlamı | Ne yapmalı |
|---|---|---|
| 🟠 *DAPI yok (en iyi aday %…)* | Örtüşen DAPI bulunamadı | Doğru DAPI'yi klasöre koyun ya da şekle göre ayırmayı kabul edin |
| ⚪ *atlandı: …* | Bkz. [8.2](#82-fitcdapi-eslestirme) | — |
| *Fiji bulunamadı* | Fiji kurulu değil / farklı yerde | Fiji ▸ Fiji konumunu seç… |
| ⚠️ *Fark var* (Fiji doğrulaması) | Program ile Fiji farklı ölçtü (beklenmez) | Kalibrasyonu kontrol edin; sorunu bildirin |

---

## 13. Makale için: yöntem metni ve atıf

**Örnek yöntem metni (İngilizce, kendi ayarlarınıza göre düzenleyin):**

> Corrected total cell fluorescence (CTCF) was quantified as CTCF = integrated density − (cell area × mean background fluorescence) (McCloy et al., 2014) using ICC CTCF Ölçer v2.0.0 (Balcan, 2026; https://doi.org/10.5281/zenodo.23860021), an open-source tool whose measurements are identical to ImageJ/Fiji for the same regions of interest (verified with Fiji 1.54p). Images were acquired on an Olympus BX43 fluorescence microscope with an Olympus DP74 camera (cellSens Entry); FITC fluorescence was measured on the green channel of the unprocessed images (40× objective, 0.145 µm/pixel; calibration read from the embedded scale bar). Cells were segmented from the FITC channel (Li threshold) and touching cells were separated by watershed seeded with DAPI-stained nuclei. Background was the mean of three 50 × 50 pixel cell-free regions per field. Cells touching the image border were excluded. Automatic boundaries were compared with manual Fiji tracing in n = … cells from … images (Bland–Altman bias …%, 95% limits of agreement … to …%; mean Dice …). Statistics were performed on the means of N = … independent experiments using one-way ANOVA followed by Dunnett's test versus control.

Excel'deki **Methods** sayfası ve **Cells** sayfasındaki *App_version, Nucleus_method, Scale_source, BG_box_px, BG_n, Selection, Manual_edits, Fiji_check* sütunları bu metni doldurmak için gereken bilgileri içerir.

**Atıf (kaynakçaya):**

> Balcan E. (2026). *ICC CTCF Ölçer: per-cell corrected total cell fluorescence (CTCF) quantification for immunocytochemistry images* (Version 2.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.23860021

| DOI | Ne zaman kullanılır |
|---|---|
| **10.5281/zenodo.23860021** | Makalede kullandığınız **bu sürüm** (2.0.0) — önerilen; tekrarlanabilirlik için sürüm belli olur |
| 10.5281/zenodo.23860020 | Programın **tüm sürümleri** (concept DOI; her zaman en yeni sürüme yönlendirir) |

Ölçümde kullanılan sürüm Excel'deki **App_version** sütununda yazar; yeni bir sürümle ölçtüyseniz o sürümün DOI'sini Zenodo sayfasından alın (https://doi.org/10.5281/zenodo.23860020 → "Versions").

Ayrıca CTCF yöntemi için: McCloy RA, Rogers S, Caldon CE, Lorca T, Castro A, Burgess A. (2014). Partial inhibition of Cdk1 in G2 phase overrides the SAC and decouples mitotic events. *Cell Cycle* 13(9):1400–1412. https://doi.org/10.4161/cc.28401
---

## 14. Sorun giderme

| Sorun | Çözüm |
|---|---|
| Mac: *"tanınmayan geliştirici"* | Uygulamaya sağ tık ▸ Aç ▸ Aç (bir kez) |
| Mac: *"hasarlı, Çöp Sepeti'ne taşıyın"* | Terminal: `xattr -cr "/Applications/ICC CTCF Ölçer.app"` |
| Mac (Apple Silicon, Monterey): açılmıyor | macOS'u 12.3 veya üstüne güncelleyin |
| Windows: *"bilgisayarınızı korudu"* | Ek bilgi ▸ Yine de çalıştır |
| Program açılırken uzun bekliyor | İlk açılışta yazı tipi önbelleği oluşturulur (bir kez, ~10–30 sn) |
| Hücre sayısı yanlış | Doğru düğmeyle mi açtınız (FITC/DAPI)? DAPI aynı alanın mı? Sınırları [Bölüm 7](#7-hucre-sinirlarini-elle-duzeltmek) ile düzeltin |
| Yoğun kümede tek "hücre" | **Böl** aracı |
| Çekirdekler (mor çizgi) yanlış | **Görüntü: DAPI** görünümüne geçip kontrol edin; DAPI aynı alanın mı? |
| Değerler v1'den biraz farklı | v2'nin çekirdek algılaması farklı (Nucleus_method). Çalışma boyunca tek sürüm kullanın |
| Excel kaydedilemiyor | Dosya Excel'de açıksa kapatıp yeniden deneyin |
| Program kapandı / çöktü | Yeniden açın → *"devam edilsin mi?"* → Evet (otomatik kayıt) |
| Fiji köprüsü çalışmıyor | Fiji ▸ Fiji konumunu seç… ; Fiji'yi bir kez kendiniz açıp kapatın (ilk kurulum güncellemeleri) |
| Arayüz yanlış dilde | Görünüm ▸ Dil / Language, sonra yeniden başlatın |

Soru ve hata bildirimi: https://github.com/erdal-b-dot/icc-ctcf-olcer/issues

---

## 15. Teknik ayrıntılar

**Ölçüm tanımları (ImageJ ile aynı):**
- Area = piksel sayısı × (µm/piksel)²
- IntDen = Area × Mean (kalibre birim); RawIntDen = piksellerin toplamı
- StdDev = örneklem standart sapması (n − 1)
- ROI kuralı: piksel merkezi çokgenin içindeyse dahil
- CTCF = IntDen − Area × BG_Mean; CTCF_per_Area = Mean − BG_Mean

**Kalibrasyon:** cellSens ölçek çubuğu (sağ alt beyaz kutu) uzunluğu piksel olarak ölçülür; önce çubuk bulunur (üstü ve altı beyaz ince siyah çizgi), kutu çubuğun beyaz kenar boşluğundan ölçülür, altındaki sayı rakam şablonlarıyla okunur. 3534 floresan görüntüde (yazarın arşivi 3233 + geliştirme seti 301; iki farklı cellSens kutu stili) tamamı doğru okundu. Objektif = kamera piksel boyutu (DP74: 5.86 µm) ÷ µm/piksel.

**Hücre segmentasyonu:** FITC (G kanalı) Gauss yumuşatma → Li eşiği → kapanış, delik doldurma, küçük nesne eleme (< 50 µm²) → DAPI çekirdekleri tohum olarak watershed (DAPI yoksa mesafe dönüşümü).

**Çekirdek algılama (Nucleus_method):**
| Yöntem | Sürüm | Açıklama |
|---|---|---|
| `otsu` | v1.0.0 | Otsu eşiği (DAPI'nin loş halesini de kapsar) |
| `bright_core` | v2 ilk | 3 sınıflı Otsu'nun üst eşiği (sönük çekirdekleri kaçırır) |
| **`local`** | **v2.0.0 varsayılan** | Otsu maskesi → yumuşatılmış DAPI tepelerinden watershed → her çekirdek kendi tepe parlaklığının yarısında kırpılır |

**Doğrulama sonuçları (2026-10-31 / 11-01):**
- Fiji 1.54p ile aynı ROI'lerde Area/Mean/StdDev/Min/Max/IntDen/RawIntDen birebir aynı (Image_392: 5 ROI; Image_286, background ≠ 0: 54 ROI; en büyük fark < 0.00001 %).
- Elle çizim (1 görüntü, 2 değen hücre — ön veri): Dice 0.943 / 0.938; CTCF farkı +2.3 % / +3.7 %.
- 20× yoğun kümeler (Image_286/287): 47 çekirdek, 51 hücre.

**Program dosyaları:** `core.py` (ölçüm), `batch.py` (toplu), `report.py` (Excel, grafik, istatistik), `fiji.py` (Fiji köprüsü), `desktop.py` (arayüz), `i18n.py` + `locales/` (diller), `tests/test_core.py` (doğrulama testleri).
