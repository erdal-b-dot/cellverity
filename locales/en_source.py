"""İngilizce arayüz çevirileri (kaynak: Türkçe metin → İngilizce). `python locales/en_source.py` → en.json.
Yer tutucular ({0}, {1:.3f} …) iki dilde de aynı olmalıdır; tests/test_core.py bunu denetler."""
import json
from pathlib import Path

EN = {
    # ---- genel / dosya
    "Görüntüler (*.jpg *.jpeg *.tif *.tiff *.png)": "Images (*.jpg *.jpeg *.tif *.tiff *.png)",
    "Birleşik (FITC + DAPI)": "Merged (FITC + DAPI)",
    "Hücre": "Cell",
    "Doymuş px": "Saturated px",
    "Görüntü": "Image",
    "Alan": "Area",
    "Alan ({0})": "Area ({0})",
    "Kutu": "Box",
    "Piksel": "Pixels",
    "Grup": "Group",
    "Deney": "Experiment",
    "Objektif": "Objective",
    "Ortalama": "Mean",
    "Medyan": "Median",
    "Kalibrasyon": "Calibration",
    "Ölç": "Measure",
    "Örtüşme": "Overlap",
    "Durum": "Status",
    "Sınır düzeltme aracı — tıklayın: Seç, Böl, Birleştir, Sil, Çiz": "Boundary editing tool — click: Select, Split, Merge, Delete, Draw",
    "Sınır düzeltme: {0}": "Boundary editing: {0}",
    "Excel…": "Excel…",
    "Toplu ölç…": "Batch…",
    "Tabloya ekle": "Add to table",
    "Çekirdekler": "Nuclei",
    "Sığdır": "Fit",
    "Tema": "Theme",
    "Koyu (varsayılan)": "Dark (default)",
    "Sistem (açık)": "System (light)",
    "Tema, program yeniden açıldığında uygulanır.": "The theme is applied when the program is restarted.",
    "Güncellemeleri denetle…": "Check for updates…",
    "Açılışta güncellemeleri denetle": "Check for updates at startup",
    "Program açılırken (günde en çok bir kez) GitHub'a yalnızca 'en son sürüm hangisi?' diye sorar; görüntü ya da veri gönderilmez.":
        "At startup (at most once a day) the program only asks GitHub 'which is the latest version?'; no images or data are sent.",
    "Güncelleme denetlenemedi (internet bağlantısı yok ya da GitHub yanıt vermedi).\n\nSürümler: {0}\n\n{1}":
        "Could not check for updates (no internet connection or GitHub did not respond).\n\nReleases: {0}\n\n{1}",
    "Güncel sürümü kullanıyorsunuz ({0} {1}). Yayımlanmış en son sürüm: {2}.": "You are using the current version ({0} {1}). Latest released version: {2}.",
    "Yeni sürüm var": "New version available",
    "<b>{0} {1}</b> yayımlandı (kullandığınız: {2}).<br><br>Yeni sürümü indirip kurun; ayarlarınız korunur. Yayın için ölçümlerde güncel sürümü kullanmanız önerilir.":
        "<b>{0} {1}</b> has been released (you are using {2}).<br><br>Download and install the new version; your settings are kept. Using the current version for measurements intended for publication is recommended.",
    "İndir": "Download",
    "Bu sürümü atla": "Skip this version",
    "Daha sonra": "Later",
    "ℹ️ {0}/{1} görüntünün pozlama süresi dosyada yazmıyor (ör. PNG ya da yeniden kaydedilmiş görüntü); program bunların aynı ayarla çekildiğini doğrulayamıyor — karşılaştırılan görüntülerin aynı pozlama, kazanç ve lamba ayarıyla çekildiğinden emin olun.":
        "ℹ️ The exposure time of {0}/{1} images is not stored in the file (e.g. PNG or a re-saved image); the program cannot verify that they were acquired with the same settings — make sure the compared images share the same exposure, gain and lamp settings.",
    "Hakkında / sürüm bilgisi…": "About / version info…",
    "Bilgileri kopyala": "Copy info",
    "<span style='color:{warn}'>Geliştirme sürümü: henüz yayımlanmadı ve DOI'si yok. Yayın için ölçümlerde yayımlanmış bir sürüm kullanın.</span>":
        "<span style='color:{warn}'>Development build: not yet released and has no DOI. For publications, measure with a released version.</span>",
    "Bu sürümün DOI'si: Zenodo sayfasında (Versions)": "DOI of this version: see the Zenodo page (Versions)",
    "Sürüm bilgisi panoya kopyalandı (hata bildirirken yapıştırın).": "Version info copied to the clipboard (paste it when reporting a problem).",
    "kaynak kod": "source code",
    "kaynak kod, commit {0}": "source code, commit {0}",
    "Bu sürümün DOI'si: <a href='https://doi.org/{0}'>{0}</a>": "DOI of this version: <a href='https://doi.org/{0}'>{0}</a>",
    "<b>{0} {1}</b> — eski adı ICC CTCF Ölçer<br>İmmünositokimya görüntülerinde doğrulanabilir hücre başına floresan (CTCF) ölçümü.<br><br>{2}<br>Tüm sürümler: <a href='https://doi.org/{3}'>{3}</a><br><br>Derleme: {4}<br>Sistem: {5}<br><br>CTCF = IntDen − (Area × Mean background) — McCloy et al., 2014, <i>Cell Cycle</i><br>Ölçümler ImageJ/Fiji ile birebir aynıdır.<br>© 2026 Erdal Balcan, Manisa Celal Bayar Üniversitesi — MIT lisansı":
        "<b>{0} {1}</b> — formerly ICC CTCF Ölçer<br>Verifiable per-cell fluorescence (CTCF) quantification for immunocytochemistry images.<br><br>{2}<br>All versions: <a href='https://doi.org/{3}'>{3}</a><br><br>Build: {4}<br>System: {5}<br><br>CTCF = IntDen − (Area × Mean background) — McCloy et al., 2014, <i>Cell Cycle</i><br>Measurements are identical to ImageJ/Fiji.<br>© 2026 Erdal Balcan, Manisa Celal Bayar University — MIT License",
    "Kalibrasyon (µm/piksel)": "Calibration (µm/pixel)",
    " µm/piksel": " µm/pixel",
    " µm (kamera pikseli)": " µm (camera pixel)",
    "Olympus DP74: 5.86 µm. Kameranızın teknik belgesinde 'pixel size' olarak yazar.": "Olympus DP74: 5.86 µm. Listed as 'pixel size' in your camera's specifications.",
    "µm/piksel": "µm/pixel",
    "ya da objektif": "or objective",
    "kamera piksel boyutu": "camera pixel size",
    "Uygula": "Apply",
    "Piksel biriminde ölç": "Measure in pixels",
    "Kalibrasyonsuz devam eder: alanlar piksel², boyut filtreleri piksel cinsinden (hücreler parçalanabilir). Yalnızca aynı ayarla çekilmiş görüntüleri kendi aralarında karşılaştırmak için.":
        "Continues without calibration: areas in pixels², size filters in pixels (cells may be fragmented). Only for comparing images acquired with identical settings among themselves.",
    "Piksel boyutunu girin ya da objektif ve kamera piksel boyutundan hesaplatın (kamera piksel boyutu ÷ objektif büyütmesi; ara büyütme/adaptör varsa ona da bölün).":
        "Enter the pixel size or let it be calculated from the objective and the camera pixel size (camera pixel size ÷ objective magnification; also divide by any intermediate magnification/adapter).",
    "Kalibrasyonu elle gir (µm/piksel)…": "Enter calibration manually (µm/pixel)…",
    "Ölçek bulunamadı — piksel birimi": "No scale found — pixel units",
    "⚠️ Kalibrasyon yok: alanlar piksel², boyut filtreleri piksel cinsinden; hücreler parçalanabilir. Düzelt ▸ Kalibrasyonu elle gir.":
        "⚠️ No calibration: areas in pixels², size filters in pixels; cells may be fragmented. Edit ▸ Enter calibration manually.",
    "<b>Bu görüntüde ölçek bulunamadı</b>: üzerinde ölçek çubuğu yok ve dosyada piksel boyutu bilgisi (meta veri) yok.<br><br>Kalibrasyon olmadan alan µm² yerine piksel² olur ve hücre/çekirdek boyut filtreleri yanlış ölçekte çalışır; hücreler parçalanabilir.<br><br>":
        "<b>No scale found in this image</b>: there is no scale bar on it and no pixel-size information (metadata) in the file.<br><br>Without calibration, areas are in pixels² instead of µm² and the cell/nucleus size filters work at the wrong scale; cells may be fragmented.<br><br>",
    "Kalibrasyonsuz (piksel biriminde) devam ediliyor.": "Continuing without calibration (pixel units).",
    "{0:.4f} µm/piksel  (dosya meta verisinden: {1})": "{0:.4f} µm/pixel  (from file metadata: {1})",
    "{0:.4f} µm/piksel  (elle girildi)": "{0:.4f} µm/pixel  (entered manually)",
    "⚠️ Ölçek çubuğu ({0:.4f} µm/piksel) ile dosyanın meta verisi ({1:.4f} µm/piksel) %{2:.0f} farklı. Görüntü yeniden boyutlandırılmış ya da çubuk yanlış okunmuş olabilir; doğru değeri Düzelt ▸ Kalibrasyonu elle gir ile verin.":
        "⚠️ The scale bar ({0:.4f} µm/pixel) and the file metadata ({1:.4f} µm/pixel) differ by {2:.0f} %. The image may have been resized or the bar misread; enter the correct value with Edit ▸ Enter calibration manually.",
    "⚠️ {0} görüntü kalibrasyonsuz ölçüldü (ölçek çubuğu ve dosya meta verisi yok): alanları piksel², boyut filtreleri piksel cinsinden. Bu görüntüleri tek tek açıp Düzelt ▸ Kalibrasyonu elle gir ile µm/piksel verin.":
        "⚠️ {0} images were measured without calibration (no scale bar and no file metadata): their areas are in pixels² and size filters in pixels. Open them one by one and enter µm/pixel with Edit ▸ Enter calibration manually.",
    "ör. p53": "e.g. p53",
    "Bu görüntüde ölçülen protein / hedef. Birden çok protein ölçüldüyse Sonuçlar ▸ Protein paneli\nher proteini aynı deneydeki kendi kontrolüne oranlayarak yan yana gösterir.":
        "Protein / target measured in this image. If several proteins were measured, Results ▸ Protein panel\nshows them side by side, each normalised to its own control in the same experiment.",
    "Protein / hedef": "Protein / target",
    "Protein / hedef:": "Protein / target:",
    "Klasör düzeni Protein/Deney/Grup/görüntü ise protein klasör adından okunur; değilse buraya yazılan ad tüm görüntülere verilir.":
        "With a Protein/Experiment/Group/image folder layout the protein is read from the folder name; otherwise the name entered here is given to all images.",
    "Protein paneli": "Protein panel",
    "Protein paneli…": "Protein panel…",
    "Protein": "Protein",
    "Farklı proteinler farklı antikorlarla ölçüldüğü için ham değerleri karşılaştırılamaz. Her protein, <b>aynı deneydeki kendi kontrolüne</b> oranlanır; proteinler farklı hücrelerde ölçülmüş olabilir. n = bağımsız deney.":
        "Different proteins are measured with different antibodies, so their raw values cannot be compared. Each protein is normalised to <b>its own control in the same experiment</b>; the proteins may have been measured in different cells. n = independent experiments.",
    "Grafik ve istatistik tek bir protein için yapılır; proteinleri yan yana görmek için Sonuçlar ▸ Protein paneli.":
        "Plots and statistics are for one protein at a time; to see proteins side by side use Results ▸ Protein panel.",
    "<b>Grup sırası</b> (sürükleyerek değiştirin)": "<b>Group order</b> (drag to change)",
    "Test: log2(kat değişimi) = 0, tek örneklem t (oran eşleştirilmiş t-testi); her proteinde gruplar arası Holm düzeltmesi. n = bağımsız deney.":
        "Test: log2(fold change) = 0, one-sample t (ratio paired t test); Holm correction across groups within each protein. n = independent experiments.",
    "ℹ️ Deney etiketi boş olan hücreler panele alınmadı (kat değişimi aynı deneyin kontrolüne göre hesaplanır).":
        "ℹ️ Cells without an experiment label were left out of the panel (fold change is computed against the control of the same experiment).",
    "test yok (n < 2)": "no test (n < 2)",
    "ℹ️ Bazı karşılaştırmalarda 3'ten az bağımsız deney var: test gücü düşük; en az 3 deney önerilir.":
        "ℹ️ Some comparisons have fewer than 3 independent experiments: low test power; at least 3 experiments are recommended.",
    "Panel için Protein ve Deney etiketli, kontrol grubu içeren veri gerekir.":
        "The panel needs data labelled with Protein and Experiment that include a control group.",
    "Protein paneli — {0}, kontrol = {1}. Her protein, aynı deneydeki kendi kontrolüne oranlandı (kat değişimi); ham değerler proteinler arasında karşılaştırılamaz (farklı antikorlar).":
        "Protein panel — {0}, control = {1}. Each protein was normalised to its own control in the same experiment (fold change); raw values cannot be compared between proteins (different antibodies).",
    "Kat değişimi (kontrol = 1) — {0}": "Fold change (control = 1) — {0}",
    "ℹ️ {0} / deney {1}: kontrol grubu ({2}) yok ya da değeri ≤ 0 → bu deney atlandı.":
        "ℹ️ {0} / experiment {1}: no control group ({2}) or its value is ≤ 0 → this experiment was skipped.",
    "Çekirdek / sitoplazma (N/C)": "Nucleus / cytoplasm (N/C)",
    "Kenar halkası": "Edge ring",
    "Çekirdek kenarında dışarıda bırakılan halka: çekirdek bu kadar daraltılır, sitoplazma bu kadar uzaktan başlar. FITC ve DAPI ayrı çekildiği için kenardaki kaymaya karşı korur. 0 = halka yok.":
        "Ring left out at the nuclear edge: the nucleus is shrunk by this distance and the cytoplasm starts this far away. Guards against edge misregistration, since FITC and DAPI are acquired separately. 0 = no ring.",
    "DAPI görüntüsü varsa her hücrede çekirdek ve sitoplazma ayrı ölçülür (N/C sütunu). Sitoplazması hücre alanının %20'sinden küçük hücreler N/C analizinden çıkarılır.":
        "With a DAPI image, the nucleus and the cytoplasm of every cell are measured separately (N/C column). Cells whose cytoplasm is smaller than 20 % of the cell area are left out of the N/C analysis.",
    "ince sitoplazma (yalnızca N/C güvenilmez)": "thin cytoplasm (only N/C unreliable)",
    "ℹ️ {0} hücre ince sitoplazma nedeniyle (ölçülen sitoplazma < hücre alanının %{1:.0f}'si) {2} analizinden çıkarıldı; tüm hücre CTCF'leri geçerli (Excel: NC_flag).":
        "ℹ️ {0} cells were left out of the {2} analysis because of thin cytoplasm (measured cytoplasm < {1:.0f} % of the cell area); their whole-cell CTCF values remain valid (Excel: NC_flag).",
    "<br>Çekirdek/sitoplazma bölmeleri (Nuc_/Cyto_): Fiji etiket görüntülerinden kendi seçimini oluşturup ölçtü; N/C oranı Fiji'nin değerlerinden yeniden hesaplandı.":
        "<br>Nuclear/cytoplasmic compartments (Nuc_/Cyto_): Fiji created its own selections from the label images and measured them; the N/C ratio was recalculated from Fiji's values.",
    "Kontrol": "Control",
    "FITC ve DAPI görüntülerini buraya sürükleyin\nveya  Dosya ▸ FITC aç  (⌘O / Ctrl+O)":
        "Drag FITC and DAPI images here\nor  File ▸ Open FITC  (⌘O / Ctrl+O)",
    "Hücre sayısı": "Cell count",
    "Çekirdek sayısı": "Nucleus count",
    "otomatik (etiketten)": "automatic (from label)",
    "Ölçek çubuğunun altında yazan değer. 'otomatik' = program etiketi okur.\nYanlış okunduysa buraya doğru değeri yazın.":
        "The value printed under the scale bar. 'automatic' = read from the label.\nIf it was read wrongly, type the correct value here.",
    "<b>Ölçek çubuğu</b>": "<b>Scale bar</b>",
    # ---- sağ panel
    "Hücre seçimi": "Cell selection",
    "Hücreye tıklayarak seçin / bırakın.": "Click a cell to select / deselect it.",
    "Tüm hücreleri seç": "Select all cells",
    "Seçimi temizle": "Clear selection",
    "Seçili: —": "Selected: —",
    "Seçili: {0} / {1} hücre": "Selected: {0} / {1} cells",
    "Otomatik": "Automatic",
    "Elle": "Manual",
    "Kutu boyutu (kare)": "Box size (square)",
    "Otomatik kutu sayısı": "Number of automatic boxes",
    "Kutuları fareyle sürükleyerek taşıyabilirsiniz (otomatik kutu taşınırsa 'Elle'ye geçilir). Elle: boş alana tıklayın → kutu eklenir; kutuya tıklayın → silinir.":
        "Drag boxes with the mouse to move them (moving an automatic box switches to 'Manual'). Manual: click an empty area → a box is added; click a box → it is removed.",
    "Elle kutuları temizle": "Clear manual boxes",
    "Background ortalaması: —": "Background mean: —",
    "Background ortalaması: <b>{0:.3f}</b>  (n = {1} kutu, {2}×{3} px)": "Background mean: <b>{0:.3f}</b>  (n = {1} boxes, {2}×{3} px)",
    "<br><span style='color:{warn}'>⚠️ Bazı kutularda sinyal/debris olabilir.</span>":
        "<br><span style='color:{warn}'>⚠️ Some boxes may contain signal/debris.</span>",
    "<br><span style='color:{info}'>ℹ️ Kutulardaki tüm pikseller 0: kamera siyah seviyesi kırpılmış (Fiji'de de 0). Bu durumda CTCF = IntDen olur; tüm görüntüler aynı ayarla çekildiyse sorun değildir. Ayrıntı: alttaki 'Background kutuları' sekmesi.</span>":
        "<br><span style='color:{info}'>ℹ️ All pixels in the boxes are 0: the camera black level is clipped (also 0 in Fiji). CTCF then equals IntDen; this is fine if all images were acquired with the same settings. Details: 'Background boxes' tab below.</span>",
    "<span style='color:{bad}'>Background kutusu yok — CTCF hesaplanamaz.</span>":
        "<span style='color:{bad}'>No background box — CTCF cannot be computed.</span>",
    " Görüntüye tıklayarak kutu ekleyin.": " Click the image to add a box.",
    " Kutu boyutunu küçültün.": " Reduce the box size.",
    "Sonuçlar": "Results",
    "Bu görüntünün ait olduğu grup/koşul, ör. 'CD44 ilaçsız', 'Ax 10 µM 24 sa'.\nGrafik ve istatistik bu etikete göre gruplanır.":
        "Group/condition of this image, e.g. 'Control', 'Drug 10 µM 24 h'.\nPlots and statistics are grouped by this label.",
    "Grup / koşul": "Group / condition",
    "Deney / tekrar": "Experiment / replicate",
    "Bağımsız deney (biyolojik tekrar) numarası/adı, ör. 1, 2, 3 ya da 'Deney_1'.\nİstatistiği deney ortalamaları üzerinden yapmak için gerekir.":
        "Independent experiment (biological replicate) number/name, e.g. 1, 2, 3 or 'Exp_1'.\nRequired for statistics on experiment means.",
    "➕ Sonuç tablosuna ekle": "➕ Add to results table",
    "Seçili hücrelerin ölçümlerini biriken tabloya ekler (⌘↩ / Ctrl+Enter).\nAynı görüntü yeniden eklenirse eskisinin yerine geçer.":
        "Adds the measurements of the selected cells to the results table (⌘↩ / Ctrl+Enter).\nRe-adding the same image replaces its previous entry.",
    "Biriken: 0 hücre": "Collected: 0 cells",
    "Biriken: <b>{0}</b> hücre, {1} görüntü, {2} grup": "Collected: <b>{0}</b> cells, {1} images, {2} groups",
    "  <span style='color:{warn}'>(kaydedilmedi)</span>": "  <span style='color:{warn}'>(not saved)</span>",
    "Excel'e kaydet…": "Save to Excel…",
    "Grafik…": "Plot…",
    "<b>Çizgiler</b><br><span style='color:#9a9a9a'>━</span> hücre sınırı (numaralı)<br><span style='color:#d4b000'>━</span> seçili hücre (ölçülür)<br><span style='color:#ff00ff'>━</span> çekirdek sınırı (DAPI'den)<br><span style='color:#ff3c3c'>□</span> background kutusu":
        "<b>Outlines</b><br><span style='color:#9a9a9a'>━</span> cell boundary (numbered)<br><span style='color:#d4b000'>━</span> selected cell (measured)<br><span style='color:#ff00ff'>━</span> nucleus boundary (from DAPI)<br><span style='color:#ff3c3c'>□</span> background box",
    "<b>Görüntü parlaklığı</b> (yalnız ekran; ölçümü etkilemez)": "<b>Display brightness</b> (screen only; does not affect measurement)",
    "⚠️ Birbirine değen hücreler varsa aynı alanın DAPI görüntüsünü mutlaka yükleyin.":
        "⚠️ If cells touch each other, always load the DAPI image of the same field.",
    "🧬 <b>Hücre ayırma: DAPI çekirdekleri</b>": "🧬 <b>Cell separation: DAPI nuclei</b>",
    "⚠️ <b>Hücre ayırma: yalnızca şekil</b> — {0} değen hücre çifti var; DAPI yükleyin.":
        "⚠️ <b>Cell separation: shape only</b> — {0} touching cell pairs; load the DAPI image.",
    "ℹ️ <b>Hücre ayırma: yalnızca şekil</b> (değen hücre yok)": "ℹ️ <b>Cell separation: shape only</b> (no touching cells)",
    "⚠️ <b>DAPI bu FITC ile aynı alana ait görünmüyor</b> — çekirdeklerin %{0:.0f}'i hücrelerin dışında kalıyor. Aynı alanın DAPI görüntüsünü açın (dosya numaraları ardışık olsa bile alan farklı olabilir).":
        "⚠️ <b>This DAPI image does not seem to belong to the same field as the FITC image</b> — {0:.0f}% of the nuclei lie outside the cells. Open the DAPI image of the same field (consecutive file numbers can still be different fields).",
    "{0:.4f} µm/piksel  (çubuk {1} px = {2:g} µm, {3})": "{0:.4f} µm/pixel  (bar {1} px = {2:g} µm, {3})",
    "etiketten okundu": "read from label",
    "elle girildi": "entered manually",
    "etiket OKUNAMADI, varsayıldı": "label NOT READ, assumed",
    "Ölçek çubuğu bulunamadı — piksel birimi": "No scale bar found — pixel units",
    "{0}×  (hesaplanan {1:.1f}×)": "{0}×  (computed {1:.1f}×)",
    "— (DAPI yok)": "— (no DAPI)",
    "— (yeni FITC açıldı; aynı alanın DAPI'sini açın)": "— (new FITC opened; open the DAPI of the same field)",
    " (elle düzeltildi)": " (manually corrected)",
    "⚠️ Ölçek çubuğunun değeri okunamadı; 20 µm varsayıldı. Görüntünün sağ alt köşesindeki değere bakıp yukarıdaki 'Ölçek çubuğu' kutusuna yazın — yanlış değer alan ve IntDen'i kat kat değiştirir.":
        "⚠️ The scale bar value could not be read; 20 µm was assumed. Check the value in the lower right corner of the image and type it into the 'Scale bar' box above — a wrong value changes area and IntDen several-fold.",
    # ---- pencere, menüler, araç çubukları
    "Görüntü bilgisi ve ayarlar": "Image information and settings",
    "Hücreler": "Cells",
    "Background kutuları": "Background boxes",
    "Background kutuları ({0})": "Background boxes ({0})",
    "Biriken sonuçlar (0)": "Collected results (0)",
    "Biriken sonuçlar ({0})": "Collected results ({0})",
    "Grup özeti (CTCF)": "Group summary (CTCF)",
    "CTCF ölçümü  —  CTCF = IntDen − (Alan × background ortalaması)": "CTCF measurement  —  CTCF = IntDen − (Area × mean background)",
    "Hazır — görüntü açın veya sürükleyin.": "Ready — open or drag images.",
    "FITC aç…": "Open FITC…",
    "Ölçülecek yeşil (FITC) görüntüyü açar. Yeni FITC açılınca eski DAPI kaldırılır.":
        "Opens the green (FITC) image to be measured. Opening a new FITC removes the previous DAPI.",
    "DAPI aç…": "Open DAPI…",
    "Aynı alanın mavi (DAPI) görüntüsünü açar; değen hücreleri çekirdeklere göre ayırmak için.":
        "Opens the blue (DAPI) image of the same field, used to separate touching cells by their nuclei.",
    "Görüntüleri kapat": "Close images",
    "Açık FITC ve DAPI görüntülerini kapatır (⌘W / Ctrl+W).": "Closes the open FITC and DAPI images (⌘W / Ctrl+W).",
    "Pencereye sığdır": "Fit to window",
    "Yakınlaştır": "Zoom in",
    "Uzaklaştır": "Zoom out",
    "Çekirdek sınırları": "Nucleus outlines",
    "DAPI'den bulunan çekirdeklerin sınırlarını mavi çizgiyle gösterir/gizler.\nProgram değen hücreleri bu çekirdeklere göre ayırır. Ölçümü etkilemez.":
        "Shows/hides the outlines of the nuclei found in DAPI.\nTouching cells are separated using these nuclei. Does not affect measurement.",
    "Ekranda hangi görüntünün gösterileceği. Ölçüm her zaman FITC'den yapılır.":
        "Which image is shown on screen. Measurement is always done on FITC.",
    "Sonuç tablosuna ekle": "Add to results table",
    "Excel olarak kaydet…": "Save as Excel…",
    "CSV olarak kaydet…": "Save as CSV…",
    "Grafik ve istatistik…": "Plot and statistics…",
    "ROI görüntüsü (PNG)…": "ROI image (PNG)…",
    "ImageJ/Fiji karşılaştırma paketi (ZIP)…": "ImageJ/Fiji comparison package (ZIP)…",
    "Biriken sonuçları sıfırla…": "Reset collected results…",
    "Klasörü toplu ölç…": "Batch-measure folder…",
    "Bir klasördeki tüm FITC/DAPI çiftlerini bulur ve hepsini ölçer.": "Finds all FITC/DAPI pairs in a folder and measures them all.",
    "Önceki sonuçları aç (Excel)…": "Open previous results (Excel)…",
    "Fiji ile doğrula": "Verify with Fiji",
    "Seçili hücreleri ve background kutularını Fiji'nin kendi 'Measure' motoruna arka planda ölçtürür ve sonuçları programınkilerle yan yana koyar.":
        "Has Fiji's own 'Measure' engine measure the selected cells and background boxes in the background and shows the results side by side with the program's.",
    "Fiji'de aç (görüntü + ROI'ler + Measure)": "Open in Fiji (image + ROIs + Measure)",
    "Fiji'de elle çizilmiş ROI'lerle karşılaştır (RoiSet.zip)…": "Compare with ROIs traced manually in Fiji (RoiSet.zip)…",
    "Yöntem doğrulama tablosu ve Bland–Altman…": "Method validation table and Bland–Altman…",
    "Fiji konumunu seç…": "Choose Fiji location…",
    "Dosya": "File",
    "Düzelt": "Edit",
    "Görünüm": "View",
    "Yardım": "Help",
    "Araçlar": "Tools",
    "Sınır düzeltme": "Boundary editing",
    " Görüntü: ": " Display: ",
    " Sınır düzeltme: ": " Boundary editing: ",
    " Sonuçlar: ": " Results: ",
    "Çıkış": "Quit",
    "Kullanım kılavuzu": "User guide",
    "Hakkında": "About",
    "Seç": "Select",
    "Böl": "Split",
    "Birleştir": "Merge",
    "Sil": "Delete",
    "Çiz": "Draw",
    "Geri al": "Undo",
    "Yinele": "Redo",
    "Hücreye tıklayarak seçin/bırakın; kutuları sürükleyin; görüntüyü sürükleyerek kaydırın.":
        "Click cells to select/deselect; drag boxes; drag the image to pan.",
    "Yapışık hücrelerin üzerine ayırma çizgisi çekin → hücre çizgiden bölünür.\nKaydırmak için ⌥ (Option/Alt) tuşuyla sürükleyin.":
        "Draw a dividing line across touching cells → the cell is split along the line.\nTo pan, drag with ⌥ (Option/Alt).",
    "Önce bir hücreye, sonra birleşeceği komşusuna tıklayın.": "Click one cell, then the neighbour to merge it with.",
    "Hücre olmayan (debris) ya da yanlış bulunmuş bölgeye tıklayın.": "Click a region that is not a cell (debris) or was detected wrongly.",
    "Programın kaçırdığı/yanlış çizdiği hücrenin sınırını fareyle çizin (bırakınca kapanır).\nÇizilen alan diğer hücrelerin üzerine yazar. Kaydırmak için ⌥ ile sürükleyin.":
        "Draw the boundary of a missed or badly outlined cell with the mouse (it closes when released).\nThe drawn area overrides other cells. To pan, drag with ⌥.",
    "Ayırma çizgisini hücrenin bir kenarından öbürüne çekin.": "Draw the dividing line from one edge of the cell to the other.",
    "Birleştirilecek iki hücreye sırayla tıklayın.": "Click the two cells to merge, one after the other.",
    "Silinecek bölgeye tıklayın.": "Click the region to delete.",
    "Hücre sınırını fareyle çizin; bırakınca kapanır.": "Draw the cell boundary with the mouse; it closes when released.",
    "✓ {0}  (geri almak için ⌘Z / Ctrl+Z)": "✓ {0}  (⌘Z / Ctrl+Z to undo)",
    "{0} elle düzeltme": "{0} manual edits",
    "Bir hücrenin içine tıklayın.": "Click inside a cell.",
    "Hücre {0} seçildi — şimdi birleşeceği komşu hücreye tıklayın.": "Cell {0} selected — now click the neighbouring cell to merge with.",
    "Çizgi hiçbir hücreyi ikiye ayırmadı — hücrenin bir kenarından öbür kenarına kadar çekin.":
        "The line did not split any cell — draw it from one edge of the cell to the other.",
    "Çizilen alan çok küçük.": "The drawn area is too small.",
    "Yeniden analiz edildi: önceki elle düzeltmeler sıfırlandı.": "Re-analysed: previous manual edits were reset.",
    "Boş alana tıklandı. Elle background için sağ panelde 'Elle' seçin.": "Empty area clicked. For manual background, choose 'Manual' in the right panel.",
    "⚠️ Kutu bir hücreye taşıyor — biraz daha uzağa tıklayın.": "⚠️ The box overlaps a cell — click a bit further away.",
    "⚠️ Kutu bir hücreye taşıyor — eski yerine döndü.": "⚠️ The box overlaps a cell — moved back.",
    "Otomatik kutu taşındı → Background 'Elle' moduna geçti.": "Automatic box moved → background switched to 'Manual'.",
    # ---- açma ve analiz
    "{0} görüntüsü aç": "Open {0} image",
    "Hücreler algılanıyor…": "Detecting cells…",
    "Analiz başarısız.": "Analysis failed.",
    "Analiz sırasında hata:\n{0}": "Error during analysis:\n{0}",
    "{0} hücre bulundu. Ölçmek için hücrelere tıklayın veya 'Tüm hücreleri seç'.": "{0} cells found. Click cells to measure them, or 'Select all cells'.",
    "Görüntüler kapatıldı — yeni FITC ve DAPI çiftini sürükleyin.": "Images closed — drag a new FITC and DAPI pair.",
    "yeşil": "green",
    "mavi": "blue",
    "{0} bir {1} görüntüsüne benziyor ({2} baskın), ama {3} olarak açılıyor.\n\n{4} olarak açılsın mı?":
        "{0} looks like a {1} image ({2} dominant) but is being opened as {3}.\n\nOpen it as {4}?",
    "DAPI yüklendi — şimdi FITC görüntüsünü açın.": "DAPI loaded — now open the FITC image.",
    "FITC ve DAPI görüntülerinin boyutları farklı; DAPI kullanılmadı.": "The FITC and DAPI images differ in size; DAPI was not used.",
    "{0} açılamadı:\n{1}": "Could not open {0}:\n{1}",
    "{0}: kamera bilgisi (EXIF) yok.\n\nBu genellikle birleştirilmiş (merge) ya da başka programda yeniden kaydedilmiş bir görüntü demektir. CTCF için mikroskobun doğrudan kaydettiği tek kanal FITC görüntüsünü kullanın.":
        "{0}: no camera information (EXIF).\n\nThis usually means a merged image or one re-saved by another program. For CTCF, use the single-channel FITC image saved directly by the microscope software.",
    "Görüntü yazılımla işlenmiş görünüyor: {0}.\nParlaklık/kontrast ayarı yapılmış görüntülerde CTCF güvenilir değildir.":
        "The image appears to have been processed with software: {0}.\nCTCF is not reliable on images with adjusted brightness/contrast.",
    # ---- sonuçlar ve dışa aktarım
    "Önce hücre seçin (tıklayın veya 'Tüm hücreleri seç').": "Select cells first (click, or 'Select all cells').",
    "{0} hücre '{1}' grubuna eklendi": "{0} cells added to group '{1}'",
    " (bu görüntünün önceki ölçümünün yerine).": " (replacing this image's previous measurement).",
    "Otomatik kayıt yapılamadı: {0}": "Autosave failed: {0}",
    "Önceki sonuçları aç (Excel)": "Open previous results (Excel)",
    "{0} okunamadı:\n{1}\n\nBu programın kaydettiği Excel olmalı ('Cells' sayfası).": "Could not read {0}:\n{1}\n\nIt must be an Excel file saved by this program ('Cells' sheet).",
    "{0}: {1} hücre yüklendi — eklemeye devam edebilirsiniz.": "{0}: {1} cells loaded — you can continue adding.",
    "Son oturumdan otomatik kaydedilmiş {0} hücrelik sonuç var ({1}).\n\nKaldığınız yerden devam edilsin mi?":
        "There are autosaved results for {0} cells from the last session ({1}).\n\nContinue where you left off?",
    "Excel olarak kaydet": "Save as Excel",
    "CSV olarak kaydet": "Save as CSV",
    "Kaydedilemedi:\n{0}\n\nDosya Excel'de açıksa kapatıp yeniden deneyin.": "Could not save:\n{0}\n\nIf the file is open in Excel, close it and try again.",
    "Kaydedildi: {0}": "Saved: {0}",
    "ROI görüntüsünü kaydet": "Save ROI image",
    "ImageJ paketi için önce hücre seçin.": "Select cells first for the ImageJ package.",
    "ImageJ/Fiji paketini kaydet": "Save ImageJ/Fiji package",
    "Kaydedildi: {0}\n\nFiji'de: TIFF'i açın → Analyze ▸ Set Scale: {1} piksel = {2:g} µm → ROI Manager ▸ Open: RoiSet.zip → Measure.\nAyrıntılar ZIP içindeki NASIL_KULLANILIR.txt dosyasında.":
        "Saved: {0}\n\nIn Fiji: open the TIFF → Analyze ▸ Set Scale: {1} pixels = {2:g} µm → ROI Manager ▸ Open: RoiSet.zip → Measure.\nDetails in NASIL_KULLANILIR.txt / HOW_TO_USE.txt inside the ZIP.",
    "Biriken {0} hücrelik tablo silinsin mi?": "Delete the collected table of {0} cells?",
    "\n\nKaydedilmemiş sonuçlar kaybolur.": "\n\nUnsaved results will be lost.",
    "Kaydedilmemiş {0} hücrelik sonuç var.\n\nÇıkmadan önce Excel'e kaydetmek ister misiniz?":
        "There are unsaved results for {0} cells.\n\nSave them to Excel before quitting?",
    # ---- toplu ölçüm
    "Klasörü toplu ölç": "Batch-measure folder",
    "Klasördeki görüntüler FITC/DAPI olarak tanınır; her FITC, aynı klasördeki yakın numaralı DAPI'ler arasından <b>gerçekten aynı alana ait olanla</b> (şansa göre düzeltilmiş çekirdek–hücre örtüşmesi ≥ 0.5) eşleştirilir. Grup = alt klasör adı; deney = onun üstündeki klasör (ör. Deney_1/Kontrol/…) — ikisini de tabloda değiştirebilirsiniz. Her görüntüde tüm hücreler ve otomatik background ölçülür; sağ paneldeki kutu boyutu/sayısı kullanılır.":
        "Images in the folder are recognised as FITC/DAPI; each FITC is paired with the nearby-numbered DAPI in the same folder that <b>really belongs to the same field</b> (chance-corrected nucleus–cell overlap ≥ 0.5). Group = subfolder name; experiment = the folder above it (e.g. Exp_1/Control/…) — both can be edited in the table. All cells and automatic background are measured in each image, using the box size/number from the right panel.",
    "Klasör seç…": "Choose folder…",
    "Alt klasörler dahil": "Include subfolders",
    "Görüntü kenarına değen (kesik) hücreleri hariç tut": "Exclude cells touching the image border (cut off)",
    "Kenarda kesilmiş hücrenin alanı ve IntDen'i eksik ölçülür; genellikle hariç tutulur.":
        "Area and IntDen of a cell cut off at the border are underestimated; such cells are usually excluded.",
    "Seçilenleri ölç ve tabloya ekle": "Measure selected and add to table",
    "Kapat": "Close",
    "Görüntü klasörünü seçin": "Choose the image folder",
    "Okunuyor: {0}": "Reading: {0}",
    "Eşleştiriliyor: {0}": "Pairing: {0}",
    "Ölçülüyor: {0}": "Measuring: {0}",
    "<b>{0}</b> çift hazır · <span style='color:{warn}'>{1} FITC'nin DAPI'si bulunamadı</span> (yalnız şekle göre ayrılır) · <span style='color:{info}'>{2} dosya atlandı</span> (merge, işlenmiş, eşleşmeyen DAPI). Ölçülmesini istemediklerinizin işaretini kaldırın.":
        "<b>{0}</b> pairs ready · <span style='color:{warn}'>no DAPI found for {1} FITC</span> (separated by shape only) · <span style='color:{info}'>{2} files skipped</span> (merged, processed, unpaired DAPI). Untick the ones you do not want measured.",
    "Bitti: {0} hücre biriken tabloya eklendi.": "Done: {0} cells added to the results table.",
    "\n\nÖlçülemeyenler:\n": "\n\nCould not be measured:\n",
    "hazır": "ready",
    "DAPI yok": "no DAPI",
    " (en iyi aday %{0:.0f})": " (best candidate {0:.0f}%)",
    "atlandı: {0}": "skipped: {0}",
    "açılamadı ({0})": "could not open ({0})",
    "işlenmiş görüntü ({0})": "processed image ({0})",
    "kamera bilgisi yok (merge/yeniden kaydedilmiş)": "no camera information (merged/re-saved)",
    "FITC mi DAPI mi anlaşılamadı": "could not tell FITC from DAPI",
    "eşleşmeyen DAPI": "unpaired DAPI",
    # ---- Fiji
    "Fiji bulunamadı. Bir sonraki pencerede Fiji klasörünü (ya da Fiji.app'i) seçin.\n\nFiji yüklü değilse: https://imagej.net/software/fiji/downloads":
        "Fiji was not found. In the next window, choose the Fiji folder (or Fiji.app).\n\nIf Fiji is not installed: https://imagej.net/software/fiji/downloads",
    "Fiji klasörünü seçin (Fiji / Fiji.app)": "Choose the Fiji folder (Fiji / Fiji.app)",
    "{0} içinde Fiji başlatıcısı bulunamadı.": "No Fiji launcher found in {0}.",
    "Fiji: {0}": "Fiji: {0}",
    "Fiji arka planda ölçüyor ({0} hücre + {1} kutu)…": "Fiji is measuring in the background ({0} cells + {1} boxes)…",
    "Fiji ölçümü başarısız.": "Fiji measurement failed.",
    "Fiji ölçümü başarısız (çıkış kodu {0}).\n{1}": "Fiji measurement failed (exit code {0}).\n{1}",
    "✅ Birebir aynı": "✅ Identical",
    "⚠️ Fark var": "⚠️ Difference found",
    "<b>{0}</b> — {1} ROI ({2} hücre, {3} background kutusu), Fiji {4}. En büyük fark: <b>{5:.2g} %</b>":
        "<b>{0}</b> — {1} ROIs ({2} cells, {3} background boxes), Fiji {4}. Largest difference: <b>{5:.2g} %</b>",
    ", eşleşmeyen ROI: {0}": ", unmatched ROIs: {0}",
    "<br>Fiji, programın dışa aktardığı TIFF ve RoiSet.zip'i kendi <i>Measure</i> motoruyla ölçtü (Area, Mean, StdDev, Min, Max, IntDen, RawIntDen). Bu sonuç, görüntü sonuç tablosuna eklendiğinde Excel'de <i>Fiji_check</i> sütununa yazılır.":
        "<br>Fiji measured the TIFF and RoiSet.zip exported by the program with its own <i>Measure</i> engine (Area, Mean, StdDev, Min, Max, IntDen, RawIntDen). When the image is added to the results table, this result is written to the <i>Fiji_check</i> column in Excel.",
    "Fiji doğrulaması: {0}": "Fiji verification: {0}",
    "Fiji doğrulaması": "Fiji verification",
    "Fiji açılıyor: {0} hücre + {1} kutu, ölçek {2} px = {3:g} µm. Dosyalar: {4}": "Opening Fiji: {0} cells + {1} boxes, scale {2} px = {3:g} µm. Files: {4}",
    "Önce FITC (ve DAPI) görüntüsünü açın.": "Open the FITC (and DAPI) image first.",
    "Fiji'de elle çizilmiş ROI'ler (RoiSet.zip / .roi)": "ROIs traced manually in Fiji (RoiSet.zip / .roi)",
    "ROI dosyası okunamadı:\n{0}": "Could not read the ROI file:\n{0}",
    "Dosyada hücre ROI'si bulunamadı.": "No cell ROIs found in the file.",
    "Doğrulama tablosu: {0} hücre, {1} görüntü.": "Validation table: {0} cells, {1} images.",
    "<b>{0} elle çizilmiş ROI</b> ↔ otomatik hücreler (aynı background: {1:.3f}). Ortalama Dice {2:.3f}; CTCF farkı ortalama {3:+.1f} %.<br>Birden çok görüntüde yapıp <b>doğrulama tablosuna ekleyin</b> → Bland–Altman analizi.":
        "<b>{0} manually traced ROIs</b> ↔ automatic cells (same background: {1:.3f}). Mean Dice {2:.3f}; mean CTCF difference {3:+.1f} %.<br>Repeat for several images and <b>add them to the validation table</b> → Bland–Altman analysis.",
    "Elle vs otomatik": "Manual vs automatic",
    "➕ Doğrulama tablosuna ekle": "➕ Add to validation table",
    "Doğrulama tablosu boş. Fiji ▸ 'Elle çizilmiş ROI'lerle karşılaştır' ile görüntü ekleyin.":
        "The validation table is empty. Add images with Fiji ▸ 'Compare with ROIs traced manually'.",
    "Yöntem doğrulaması (elle vs otomatik)": "Method validation (manual vs automatic)",
    "Kaydet (Excel)…": "Save (Excel)…",
    "Grafiği kaydet (PNG 600 dpi)…": "Save plot (PNG 600 dpi)…",
    "Kaydet": "Save",
    "Kılavuz bulunamadı: {0}": "User guide not found: {0}",
    "<b>{0} {1}</b><br>Immunositokimya görüntülerinde CTCF ölçümü.<br><br>CTCF = IntDen − (Area × Mean background)<br>McCloy et al., 2014, <i>Cell Cycle</i><br><br>Ölçümler ImageJ/Fiji ile birebir aynıdır.<br>Atıf: <a href='https://doi.org/10.5281/zenodo.23860020'>doi:10.5281/zenodo.23860020</a> (v2.0.0: 10.5281/zenodo.23860021)<br>© Erdal Balcan, MIT lisansı":
        "<b>{0} {1}</b><br>Per-cell CTCF measurement in immunocytochemistry images.<br><br>CTCF = IntDen − (Area × Mean background)<br>McCloy et al., 2014, <i>Cell Cycle</i><br><br>Measurements are identical to ImageJ/Fiji.<br>Cite: <a href='https://doi.org/10.5281/zenodo.23860020'>doi:10.5281/zenodo.23860020</a> (v2.0.0: 10.5281/zenodo.23860021)<br>© Erdal Balcan, MIT license",
    # ---- grafik ve istatistik
    "Grafik ve istatistik": "Plot and statistics",
    "Kontrol grubu": "Control group",
    "Dunnett testinde ve normalizasyonda referans alınan grup (GraphPad'deki 'control column').":
        "Reference group for Dunnett's test and normalisation (the 'control column' in GraphPad).",
    "Değişken": "Variable",
    "İstatistik birimi": "Statistical unit",
    "Testte n neyi sayıyor? Hücreler aynı deneyden geldiği için bağımsız değildir;\nyayın için bağımsız deney ortalamaları önerilir.":
        "What does n count in the test? Cells from the same experiment are not independent;\nmeans of independent experiments are recommended for publication.",
    "Çoklu karşılaştırma": "Multiple comparisons",
    "Grafik tipi": "Plot type",
    "<b>Grup sırası</b> (sürükleyerek değiştirin; kontrol hep başta)": "<b>Group order</b> (drag to reorder; control always first)",
    "Kontrole göre normalize et (kontrol = 1)": "Normalise to control (control = 1)",
    "Anlamlılık yıldızlarını göster": "Show significance asterisks",
    "Grafiği {0} olarak kaydet": "Save plot as {0}",
    "İstatistik metni": "Statistics text",
    "İstatistik sonucunu .txt olarak kaydet": "Save the statistics as .txt",
    "Grafiği kaydet": "Save plot",
    "İstatistik metnini kaydet": "Save statistics text",
    "Değişken: {0}\nİstatistik birimi: {1}\nKontrol: {2}\n\n": "Variable: {0}\nStatistical unit: {1}\nControl: {2}\n\n",
    "Bar (ortalama ± SEM) + noktalar": "Bar (mean ± SEM) + points",
    "Box + noktalar": "Box + points",
    "Violin + noktalar": "Violin + points",
    "Hücre (her hücre bir değer)": "Cell (each cell one value)",
    "Görüntü ortalaması (her alan bir değer)": "Image mean (each field one value)",
    "Deney ortalaması (her bağımsız deney bir değer) — önerilen": "Experiment mean (each independent experiment one value) — recommended",
    "Her grup kontrole karşı (Dunnett)": "Each group vs control (Dunnett)",
    "Tüm gruplar birbirine karşı (Tukey HSD)": "All pairs (Tukey HSD)",
    "hücre": "cells",
    "görüntü": "images",
    "deney": "experiments",
    "İstatistik için en az iki grup gerekir.": "Statistics require at least two groups.",
    "İstatistik için her grupta en az {0} {1} gerekir.": "Statistics require at least {0} {1} per group.",
    "Welch t-testi: {0} ({1})": "Welch's t-test: {0} ({1})",
    "Mann–Whitney U: {0} ({1})": "Mann–Whitney U: {0} ({1})",
    "Tek yönlü ANOVA: {0} ({1})": "One-way ANOVA: {0} ({1})",
    "Kruskal–Wallis: {0} ({1})": "Kruskal–Wallis: {0} ({1})",
    "Dunnett (kontrol = {0}):": "Dunnett (control = {0}):",
    "Tukey HSD (tüm çiftler):": "Tukey HSD (all pairs):",
    "⚠️ Grup içi değişkenlik sıfır ({0}): aynı değerler tekrar ediyor (aynı görüntü iki kez mi eklendi?). Test sonucu güvenilmez.":
        "⚠️ Zero within-group variability ({0}): identical values repeat (was the same image added twice?). The test result is not reliable.",
    "ℹ️ Grup başına {0} {1}: test gücü düşük; en az 3 bağımsız deney önerilir.":
        "ℹ️ {0} {1} per group: low statistical power; at least 3 independent experiments are recommended.",
    "⚠️ Her hücre ayrı tekrar sayıldı (yalancı tekrar riski). Yayın için 'Deney ortalaması' düzeyini kullanın.":
        "⚠️ Each cell was counted as a replicate (risk of pseudoreplication). Use the 'Experiment mean' level for publication.",
    "⚠️ Farklı objektifler karışık ({0}) — {1}. Büyütme farkı floresan yoğunluğunu ve alanı etkiler; yalnızca aynı objektifle çekilmiş görüntüleri karşılaştırın.":
        "⚠️ Different objectives are mixed ({0}) — {1}. Magnification affects fluorescence intensity and area; compare only images acquired with the same objective.",
    "Deney sütunu yok": "No experiment column",
    "Görüntü sütunu yok": "No image column",
    "{0}: bu düzey için tabloda 'Experiment' (deney) bilgisi gerekli.": "{0}: this level requires 'Experiment' information in the table.",
    "Bland–Altman için en az 2 eşleşmiş hücre gerekir (yayın için ≥ 30 hücre, ≥ 3 görüntü önerilir).":
        "Bland–Altman requires at least 2 matched cells (≥ 30 cells and ≥ 3 images are recommended for publication).",
    "n = {0} hücre, {1} görüntü\n{2}: ortalama fark (otomatik − elle) = {3:+.1f} %\n%95 uyum sınırları: {4:+.1f} % … {5:+.1f} %\nPearson r = {6:.3f} · Lin CCC = {7:.3f}\nDice (sınır örtüşmesi): ortalama {8:.3f}, en düşük {9:.3f}":
        "n = {0} cells, {1} images\n{2}: mean difference (automatic − manual) = {3:+.1f} %\n95% limits of agreement: {4:+.1f} % … {5:+.1f} %\nPearson r = {6:.3f} · Lin's CCC = {7:.3f}\nDice (boundary overlap): mean {8:.3f}, minimum {9:.3f}",
    "\n\n⚠️ Az hücre: r ve CCC bu kadar küçük örneklemde anlamsızdır. Yayın için ≥ 30 hücre, ≥ 3 görüntü (ayrık ve değen hücreler) önerilir.":
        "\n\n⚠️ Few cells: r and CCC are meaningless for such a small sample. ≥ 30 cells and ≥ 3 images (separate and touching cells) are recommended for publication.",
    "Hata:\n{0}": "Error:\n{0}",
    "<b>Kaydet</b>": "<b>Save</b>",
    "%{0:.0f}": "{0:.0f}%",
    "Satırın üzerine gelin: hücrenin önizlemesi. Tıklayın: görüntüyü açar ve hücreyi seçer (sınır düzeltme, Fiji doğrulaması için).":
        "Hover over a row: preview of the cell. Click: opens the image and selects the cell (for boundary editing and Fiji verification).",
    "<b>{0}</b> · hücre {1} · CTCF {2:,.0f}<br><i>Tıklayın: görüntüyü açar</i>": "<b>{0}</b> · cell {1} · CTCF {2:,.0f}<br><i>Click to open the image</i>",
    "Görüntü bulunamadı (taşınmış ya da disk bağlı değil):\n{0}": "Image not found (moved, or the disk is not connected):\n{0}",
    "{0} açıldı: tablodaki {1} hücre seçili, hücre {2} ortada. Düzeltip 'Sonuç tablosuna ekle' derseniz eski satırların yerine geçer.":
        "{0} opened: {1} cells from the table selected, cell {2} centred. After editing, 'Add to results table' replaces the earlier rows.",
    " · pozlama {0}": " · exposure {0}",
    "⚠️ Görüntüler farklı pozlama süreleriyle çekilmiş ({0}). Floresan sinyali pozlamayla orantılı arttığı için bu görüntülerin CTCF değerleri birbiriyle karşılaştırılamaz; aynı pozlama, kazanç ve lamba ayarıyla çekilmiş görüntüleri karşılaştırın.":
        "⚠️ The images were acquired with different exposure times ({0}). Fluorescence signal increases with exposure, so CTCF values of these images cannot be compared with each other; compare only images acquired with the same exposure, gain and lamp settings.",
    "Pozlama": "Exposure",
    "⚠️ Bu klasörde farklı pozlama süreleri var ({0}). Farklı pozlamayla çekilmiş görüntülerin CTCF değerleri karşılaştırılamaz; yalnızca aynı ayarla çekilenleri işaretli bırakın.":
        "⚠️ This folder contains different exposure times ({0}). CTCF values of images acquired with different exposures cannot be compared; keep only those acquired with the same settings ticked.",
    # ---- kalite kontrol / dışlama
    "Kalite kontrolünden kalanları dışla": "Exclude cells failing quality control",
    "Doymuş pikselli, çekirdeksiz, çok çekirdekli, çekirdeği kısmi (hücre parçası) ya da piknotik çekirdekli hücreler 'Tüm hücreleri seç'te seçilmez ve gerekçesiyle Excel'in Excluded_cells sayfasına yazılır. Turuncu çizgiyle gösterilir.":
        "Cells with saturated pixels, no nucleus, several nuclei, only part of a nucleus (cell fragment) or a pyknotic nucleus are not selected by 'Select all cells' and are written with their reason to the Excluded_cells sheet in Excel. They are outlined in orange.",
    "Sağ tık: hücreyi gerekçesiyle dışla (kırmızı).": "Right-click: exclude a cell with a reason (red).",
    "Hücre {0}": "Cell {0}",
    "Dışlamayı kaldır ({0})": "Remove exclusion ({0})",
    "Dışla: {0}": "Exclude: {0}",
    "QC: {0}": "QC: {0}",
    "<span style='color:{warn}'>QC: {0} hücre</span> · <span style='color:{bad}'>elle dışlanan: {1}</span>":
        "<span style='color:{warn}'>QC: {0} cells</span> · <span style='color:{bad}'>manually excluded: {1}</span>",
    "Kalite kontrolünden kalanları dışla (doymuş, çekirdeksiz, çok/kısmi çekirdekli, piknotik)":
        "Exclude cells failing quality control (saturated, no/several/partial nucleus, pyknotic)",
    "Dışlanan her hücre gerekçesiyle Excel'in Excluded_cells sayfasına yazılır.": "Every excluded cell is written with its reason to the Excluded_cells sheet in Excel.",
    "doymuş piksel": "saturated pixels", "çekirdek yok": "no nucleus", "birden çok çekirdek": "several nuclei",
    "çekirdek kısmi (hücre parçası?)": "partial nucleus (cell fragment?)", "piknotik çekirdek": "pyknotic nucleus",
    "görüntü kenarı": "image border",
    "apoptotik / piknotik": "apoptotic / pyknotic", "mitotik": "mitotic", "çakışık / ayrılamıyor": "overlapping / not separable",
    "odak dışı": "out of focus", "debris / hücre değil": "debris / not a cell", "diğer": "other",
    # ---- dil
    "Dil / Language": "Language / Dil",
    "Dil değişikliği program yeniden başlatılınca geçerli olur. Şimdi yeniden başlatılsın mı?":
        "The language change takes effect after restarting the program. Restart now?",
}

if __name__ == "__main__":
    out = Path(__file__).with_name("en.json")
    out.write_text(json.dumps(EN, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{out}: {len(EN)} metin")
