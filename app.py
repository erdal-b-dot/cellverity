"""ICC CTCF Ölçer – Streamlit arayüzü.  Çalıştır:  ./run.command  (veya streamlit run app.py)"""
import io
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats as sps
from streamlit_image_coordinates import streamlit_image_coordinates

import core

st.set_page_config(page_title="ICC CTCF Ölçer", layout="wide", page_icon="🔬")
ss = st.session_state
ss.setdefault("results", pd.DataFrame())
ss.setdefault("bg_results", pd.DataFrame())
ss.setdefault("selected", set())
ss.setdefault("manual_bg", [])
ss.setdefault("last_click", None)
ss.setdefault("img_key", None)

DISPLAY_W = 1100

# ============================================================== 1. YÜKLEME
st.title("🔬 ICC CTCF Ölçer")
st.caption("CTCF = Integrated Density − (Area × Mean background)  ·  McCloy et al., 2014")

with st.sidebar:
    st.header("1 · Görüntü")
    input_mode = st.radio("Girdi tipi", ["Ayrı kanallar (FITC + DAPI)", "Tek merge görüntü (G=FITC, B=DAPI)"])
    if input_mode.startswith("Ayrı"):
        f_fitc = st.file_uploader("FITC görüntüsü", type=["jpg", "jpeg", "png", "tif", "tiff"])
        f_dapi = st.file_uploader("DAPI görüntüsü (aynı alan)", type=["jpg", "jpeg", "png", "tif", "tiff"],
                                  help="Hücre sayımı ve birbirine değen hücrelerin çekirdeğe göre ayrılması için gereklidir.")
        st.caption("⚠️ **Birbirine değen hücreler varsa DAPI görüntüsünü mutlaka yükleyin.** "
                   "DAPI olmadan sınır yalnızca hücre şekline göre çizilir; test görüntüsünde bu, "
                   "hücre başına ~%5 alan/CTCF farkı yarattı.")
    else:
        f_fitc = st.file_uploader("Merge görüntü", type=["jpg", "jpeg", "png", "tif", "tiff"])
        f_dapi = None
        st.warning("Merge görüntüde kanallar karışabilir; kantitatif analiz için ayrı kanal önerilir.")

    st.header("Ölçüm ayarları")
    ch_label = st.selectbox("Ölçülecek yoğunluk", list(core.CHANNEL_MODES), index=0,
                            help="Renkli kamerada FITC sinyali G (ve kısmen R) kanalındadır. "
                                 "ImageJ'de RGB görüntüyü doğrudan ölçmek (R+G+B)/3 kullanır.")
    group = st.text_input("Grup / koşul etiketi", value="Kontrol",
                          help="Örn. 'CD44 ilaçsız', 'Ax 10 µM 24h'. Grafik ve istatistik bu etikete göre gruplar.")

if f_fitc is None:
    st.info("⬅️ Soldan FITC görüntüsünü yükleyin.")
    if len(ss.results):
        st.subheader("Biriken sonuçlar")
        st.dataframe(ss.results, width="stretch")
    st.stop()

fitc_arr, meta = core.load_image(f_fitc)
dapi_arr = core.load_image(f_dapi)[0] if f_dapi is not None else None
img_key = (f_fitc.name, f_fitc.size, getattr(f_dapi, "name", None))
if ss.img_key != img_key:  # yeni görüntü → seçimleri sıfırla
    ss.img_key, ss.selected, ss.manual_bg, ss.last_click = img_key, set(), [], None

if meta.get("software"):
    st.warning(f"⚠️ Görüntü yazılımla işlenmiş görünüyor: **{meta['software']}**. "
               "Parlaklık/kontrast ayarı yapılmış görüntülerde CTCF güvenilir değildir.")
if fitc_arr.dtype == np.uint8 and f_fitc.name.lower().endswith((".jpg", ".jpeg")):
    st.caption("ℹ️ 8-bit JPEG: kayıplı sıkıştırma piksel değerlerini hafifçe değiştirir; "
               "mümkünse TIFF kaydı tercih edin. Aynı çalışmada tüm görüntüler aynı formatta olmalı.")

# ============================================================ KALİBRASYON
sb = core.detect_scale_bar(fitc_arr)
with st.sidebar:
    st.header("Kalibrasyon")
    lbl_um = core.read_scale_label(fitc_arr, sb)
    bar_um = st.number_input("Ölçek çubuğu (µm)", value=lbl_um or 20.0, min_value=0.1,
                             help="Etiketten otomatik okunur (ör. 20 µm = 40×, 50 µm = 20×).")
    if sb.found and lbl_um is None:
        st.error("Ölçek çubuğunun değeri okunamadı — 20 µm varsayıldı. Görüntüdeki değeri kontrol edin.")
    bar_px = st.number_input("Ölçek çubuğu (piksel)", value=int(sb.bar_px or 0), min_value=0,
                             help="Otomatik algılandı; 0 = kalibrasyonsuz (piksel birimi)")
    cam_px = st.number_input("Kamera piksel boyutu (µm)", value=5.86,
                             help="Olympus DP74 = 5.86 µm. Objektif tahmini için kullanılır.")
um_per_px = bar_um / bar_px if bar_px else None

exclude = np.zeros(fitc_arr.shape[:2], bool)
if sb.found:
    y0, y1, x0, x1 = sb.bbox
    exclude[y0:y1, x0:x1] = True

dapi_ch = None
if dapi_arr is not None:
    dapi_ch = core.get_channel(dapi_arr, "B" if dapi_arr.ndim == 3 else "G")
elif input_mode.startswith("Tek"):
    dapi_ch = core.get_channel(fitc_arr, "B")
fitc_ch = core.get_channel(fitc_arr, core.CHANNEL_MODES[ch_label])
sat_value = meta["max_value"]

# ========================================================== SEGMENTASYON
with st.sidebar:
    st.header("2 · Hücre algılama")
    with st.expander("Gelişmiş segmentasyon ayarları"):
        th_method = st.selectbox("Eşik yöntemi (FITC)", list(core.THRESH), index=1)
        th_factor = st.slider("Eşik çarpanı", 0.3, 3.0, 1.0, 0.05,
                              help="<1 → daha geniş hücre sınırı, >1 → daha dar")
        min_cell = st.number_input("Min. hücre alanı (µm²)", value=50.0)
        nuc_split = st.checkbox("Bitişik çekirdekleri ayır", value=True)
        nuc_diam = st.number_input("Tipik çekirdek çapı (µm)", value=10.0)
        min_nuc = st.number_input("Min. çekirdek alanı (µm²)", value=15.0)


@st.cache_data(show_spinner="Hücreler algılanıyor…")
def run_segmentation(fitc_ch, dapi_ch, upp, exclude, th_method, th_factor, min_cell, nuc_split, nuc_diam, min_nuc):
    upp = upp or 1.0
    nuclei = None
    if dapi_ch is not None:
        nuclei = core.segment_nuclei(dapi_ch, upp, exclude, min_nuc, nuc_diam, split=nuc_split)
    labels, th = core.segment_cells(fitc_ch, upp, exclude, nuclei, th_method, th_factor, min_cell)
    return labels, nuclei, th


labels, nuclei, th = run_segmentation(fitc_ch, dapi_ch, um_per_px, exclude, th_method, th_factor,
                                      min_cell, nuc_split, nuc_diam, min_nuc)
cell_ids = [int(i) for i in np.setdiff1d(np.unique(labels), [0])]
ss.selected &= set(cell_ids)

# ---- Bilgi şeridi
c = st.columns(5)
c[0].metric("Hücre sayısı (FITC)", len(cell_ids))
c[1].metric("Çekirdek sayısı (DAPI)", int(nuclei.max()) if nuclei is not None else "—")
if um_per_px:
    obj, raw = core.estimate_objective(um_per_px, cam_px)
    c[2].metric("Kalibrasyon", f"{um_per_px:.4f} µm/px")
    c[3].metric("Tahmini objektif", f"{obj}×", help=f"Hesaplanan {raw:.1f}× (kamera adaptörü 1× varsayımı)")
else:
    c[2].metric("Kalibrasyon", "yok (px)")
c[4].metric("Görüntü", f"{fitc_arr.shape[1]}×{fitc_arr.shape[0]} · {meta['dtype']}")

# ---- Hücre ayırma modu göstergesi
touching = core.touching_pairs(labels)
seg_mode = "DAPI çekirdekleri" if nuclei is not None and nuclei.max() > 0 else "Yalnızca şekil"
touch_txt = ", ".join(f"{a}–{b}" for a, b in touching)
if seg_mode == "DAPI çekirdekleri":
    st.success(f"🧬 **Hücre ayırma: DAPI çekirdekleri** — sınırlar çekirdeklere göre çizildi."
               + (f" Birbirine değen hücreler: {touch_txt}." if touching else ""))
elif touching:
    st.error(f"⚠️ **Hücre ayırma: Yalnızca şekil** — birbirine değen hücreler var ({touch_txt}). "
             "Aralarındaki sınır çekirdeğe göre değil, şekle göre çizildi; alan ve CTCF hatalı bölünebilir. "
             "**Aynı alanın DAPI görüntüsünü yükleyin.**")
else:
    st.warning("ℹ️ **Hücre ayırma: Yalnızca şekil** (DAPI yok). Hücreler birbirine değmediği için sınırlar "
               "etkilenmez, ancak çekirdek sayımı yapılamaz.")

# ============================================================ BACKGROUND
with st.sidebar:
    st.header("3 · Background")
    bg_size = st.number_input("Kutu boyutu (piksel × piksel)", value=50, min_value=5, step=5)
    bg_n = st.number_input("Otomatik kutu sayısı", value=3, min_value=1, max_value=10)
    bg_mode = st.radio("Background kaynağı", ["Otomatik", "Elle (görüntüye tıklayarak)"])
    if bg_mode.startswith("Elle") and st.button("Elle eklenen kutuları temizle"):
        ss.manual_bg = []

if bg_mode == "Otomatik":
    bg_boxes = core.auto_background_boxes(fitc_ch, labels > 0, exclude, int(bg_size), int(bg_n),
                                          signal_thresh=th * 0.3)
else:
    bg_boxes = list(ss.manual_bg)

# ===================================================== GÖRÜNTÜ + İMLEÇ
st.subheader("Hücre seçimi")
b = st.columns([1, 1, 1, 2])
if b[0].button("✅ Tüm hücreleri seç", width="stretch"):
    ss.selected = set(cell_ids)
if b[1].button("✖️ Seçimi temizle", width="stretch"):
    ss.selected = set()
click_mode = b[2].radio("Tıklama", ["Hücre seç/bırak", "Background kutusu ekle"],
                        label_visibility="collapsed",
                        index=1 if bg_mode.startswith("Elle") else 0)
gain = b[3].slider("Görüntü parlaklığı (yalnızca görünüm, ölçümü etkilemez)", 1.0, 10.0, 1.0, 0.5)

disp = core.overlay(core.to_display(fitc_arr, gain), labels, ss.selected, bg_boxes, nuclei)
click = streamlit_image_coordinates(disp, width=DISPLAY_W, key="img")
if click and click != ss.last_click:
    ss.last_click = click
    scale = fitc_arr.shape[1] / click["width"]
    cx, cy = int(click["x"] * scale), int(click["y"] * scale)
    if click_mode.startswith("Hücre"):
        cid = int(labels[cy, cx])
        if cid:
            ss.selected ^= {cid}
    else:
        ss.manual_bg.append(core.box_at(cy, cx, int(bg_size), fitc_ch.shape))
    st.rerun()

ms = st.multiselect("Seçili hücreler (görüntüye tıklayarak da seçebilirsiniz)", cell_ids,
                    default=sorted(ss.selected))
if set(ms) != ss.selected:
    ss.selected = set(ms)
    st.rerun()

# ================================================================ ÖLÇÜM
st.subheader("CTCF ölçümü")
if not bg_boxes:
    st.error("Background kutusu yok. Otomatik modda kutu boyutunu küçültün veya elle ekleyin.")
    st.stop()
bg_df = core.measure_backgrounds(fitc_ch, bg_boxes, (um_per_px or 1) ** 2, sat_value)
bg_mean = float(bg_df["Mean"].mean())

colA, colB = st.columns([1, 2])
with colA:
    st.markdown(f"**Background ortalaması:** {bg_mean:.3f}  (n={len(bg_df)} kutu, {int(bg_size)}×{int(bg_size)} px)")
    st.dataframe(bg_df[["BG", "Mean", "StdDev", "Min", "Max"]].round(3), hide_index=True, width="stretch")
    if bg_mean == 0:
        st.info("Background = 0: kamera siyah seviyesi kırpılmış. CTCF ≈ IntDen olur. "
                "Bu, karşılaştırılan tüm görüntüler aynı ayarla çekildiyse sorun değildir.")
    if (bg_df["Max"] > th * 0.5).any():
        st.warning("Bazı background kutularında sinyal/debris olabilir (Max yüksek). Kutuları kontrol edin.")

sel = sorted(ss.selected)
with colB:
    if not sel:
        st.info("Ölçüm için hücre seçin (görüntüye tıklayın ya da 'Tüm hücreleri seç').")
        cell_df = pd.DataFrame()
    else:
        cell_df = core.measure_cells(fitc_ch, labels, sel, bg_mean, um_per_px, sat_value, nuclei)
        show = ["Cell", "Area", "Mean", "StdDev", "Min", "Max", "IntDen", "RawIntDen", "CTCF", "Saturated_px"]
        st.dataframe(cell_df[show].round(2), hide_index=True, width="stretch")
        if cell_df["Saturated_px"].sum() > 0:
            st.warning("⚠️ Doymuş (maksimum değerli) piksel içeren hücreler var — CTCF olduğundan düşük hesaplanır.")

meta_cols = {"Image": f_fitc.name, "DAPI_image": getattr(f_dapi, "name", ""), "Group": group,
             "Channel": ch_label.split(" –")[0], "um_per_px": um_per_px or np.nan,
             "BG_box_px": int(bg_size), "BG_n": len(bg_df),
             "Segmentation": seg_mode, "Touching_pairs": touch_txt,
             "Cells_in_field": len(cell_ids), "Nuclei_in_field": int(nuclei.max()) if nuclei is not None else np.nan,
             "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}

if st.button("➕ Bu görüntünün ölçümlerini sonuç tablosuna ekle", type="primary", disabled=cell_df.empty):
    add = cell_df.assign(**meta_cols)
    keep = ss.results[ss.results.get("Image", pd.Series(dtype=str)) != f_fitc.name] if len(ss.results) else ss.results
    ss.results = pd.concat([keep, add], ignore_index=True)
    bga = bg_df.assign(Image=f_fitc.name, Group=group)
    keepb = ss.bg_results[ss.bg_results["Image"] != f_fitc.name] if len(ss.bg_results) else ss.bg_results
    ss.bg_results = pd.concat([keepb, bga], ignore_index=True)
    st.success(f"{len(add)} hücre eklendi (aynı görüntü önceden eklendiyse üzerine yazıldı).")

# ===================================================== IMAGEJ KARŞILAŞTIRMA
st.subheader("🔁 ImageJ / Fiji karşılaştırması")
if not sel:
    st.info("Paketi indirmek için önce yukarıdan hücre seçin (ör. '✅ Tüm hücreleri seç').")
else:
    base = f_fitc.name.rsplit(".", 1)[0]
    st.download_button(f"⬇️ ImageJ/Fiji karşılaştırma paketi — {len(sel)} hücre + {len(bg_boxes)} BG (ZIP)",
                       core.imagej_export_zip(fitc_ch, labels, sel, bg_boxes, base, (int(bar_px), bar_um)),
                       f"ImageJ_{base}.zip", "application/zip", type="primary")
    st.caption("ZIP içinde: ölçülen kanal (TIFF) + aynı ROI'ler (RoiSet.zip) + NASIL_KULLANILIR.txt. "
               f"Fiji'de Set Scale: {bar_px} piksel = {bar_um:g} µm.  ·  Hücre ayırma: {seg_mode}.")

# =================================================== ELLE ÇİZİM KARŞILAŞTIRMASI
st.subheader("✍️ Elle çizim ile karşılaştırma")
st.caption("Fiji'de hücreleri Freehand ile çizip ROI Manager → More → Save… ile kaydettiğiniz RoiSet.zip'i yükleyin. "
           "Her elle çizilmiş ROI en çok örtüşen otomatik hücreyle eşleştirilir. Aynı background kullanılır.")
f_man = st.file_uploader("Elle çizilmiş ROI'ler (RoiSet.zip veya .roi)", type=["zip", "roi"], key="manual_rois")
if f_man is not None:
    man = core.read_imagej_rois(f_man.getvalue(), fitc_ch.shape)
    man = [(n, m) for n, m in man if not n.upper().startswith("BG")]
    cmp_df = core.compare_manual(fitc_ch, labels, man, bg_mean, um_per_px)
    if cmp_df.empty:
        st.warning("ROI bulunamadı.")
    else:
        st.dataframe(cmp_df.round(3), hide_index=True, width="stretch")
        if "Dice" in cmp_df:
            k = st.columns(3)
            k[0].metric("Ortalama Dice", f"{cmp_df['Dice'].mean():.3f}", help="1 = birebir aynı sınır")
            k[1].metric("Ortalama |Alan farkı|", f"{cmp_df['Area_diff_%'].abs().mean():.1f} %")
            k[2].metric("Ortalama |CTCF farkı|", f"{cmp_df['CTCF_diff_%'].abs().mean():.1f} %")
        st.download_button("⬇️ Karşılaştırma tablosu (CSV)", cmp_df.to_csv(index=False).encode("utf-8-sig"),
                           f"Manual_vs_Auto_{f_fitc.name.rsplit('.', 1)[0]}.csv", "text/csv")
        st.caption(f"Hücre ayırma modu: {seg_mode}. Elle ROI'ler aynı kanal üzerinde ölçüldü.")

# ============================================================ SONUÇLAR
st.divider()
st.subheader(f"Sonuç tablosu — {len(ss.results)} hücre, "
             f"{ss.results['Image'].nunique() if len(ss.results) else 0} görüntü")
if len(ss.results):
    res = ss.results
    front = ["Group", "Image", "Cell", "Area_unit", "Area", "Mean", "StdDev", "Min", "Max",
             "IntDen", "RawIntDen", "BG_Mean", "CTCF"]
    res = res[front + [c for c in res.columns if c not in front]]
    edited = st.data_editor(res, width="stretch", num_rows="dynamic", key="res_editor")
    ss.results = edited

    summary = (edited.groupby("Group")["CTCF"]
               .agg(n="count", Mean="mean", SD="std", Median="median", Min="min", Max="max")
               .assign(SEM=lambda d: d["SD"] / np.sqrt(d["n"])).reset_index())
    st.markdown("**Grup özeti (CTCF)**")
    st.dataframe(summary.round(2), hide_index=True, width="stretch")

    # ---- dışa aktarım
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    d1, d2, d3, d4 = st.columns(4)
    d1.download_button("⬇️ CSV", edited.to_csv(index=False).encode("utf-8-sig"),
                       f"CTCF_{stamp}.csv", "text/csv", width="stretch")
    xbuf = io.BytesIO()
    with pd.ExcelWriter(xbuf, engine="openpyxl") as xw:
        edited.to_excel(xw, sheet_name="Cells", index=False)
        summary.to_excel(xw, sheet_name="Group_summary", index=False)
        ss.bg_results.to_excel(xw, sheet_name="Background", index=False)
        pd.DataFrame({"Formula": ["CTCF = IntDen − (Area × Mean_background)",
                                  "IntDen = Area × Mean (kalibre birim); RawIntDen = Σ piksel",
                                  "StdDev = örneklem SD (ImageJ ile aynı)"]}).to_excel(xw, sheet_name="Methods", index=False)
    d2.download_button("⬇️ Excel", xbuf.getvalue(), f"CTCF_{stamp}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    pbuf = io.BytesIO()
    disp.save(pbuf, "PNG")
    d3.download_button("⬇️ ROI görüntüsü (PNG)", pbuf.getvalue(),
                       f"ROI_{f_fitc.name.rsplit('.', 1)[0]}.png", "image/png", width="stretch")
    if d4.button("🗑️ Tabloyu sıfırla", width="stretch"):
        ss.results, ss.bg_results = pd.DataFrame(), pd.DataFrame()
        st.rerun()

    # ============================================================ GRAFİK
    st.subheader("Grafik")
    g1, g2, g3 = st.columns(3)
    metric = g1.selectbox("Değişken", ["CTCF", "CTCF_per_Area", "Mean", "IntDen", "Area"])
    kind = g2.selectbox("Grafik tipi", ["Bar (ortalama ± SEM) + noktalar", "Box + noktalar", "Violin + noktalar"])
    norm = g3.checkbox("İlk gruba göre normalize et (kontrol = 1)")

    import matplotlib.pyplot as plt
    groups = list(dict.fromkeys(edited["Group"]))
    data = [edited.loc[edited["Group"] == g, metric].dropna().to_numpy(float) for g in groups]
    if norm and len(data[0]) and data[0].mean() != 0:
        ref = data[0].mean()
        data = [d / ref for d in data]
    fig, ax = plt.subplots(figsize=(max(3.5, 1.3 * len(groups) + 1.5), 4), dpi=150)
    x = np.arange(len(groups))
    if kind.startswith("Bar"):
        ax.bar(x, [d.mean() for d in data], yerr=[d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else 0 for d in data],
               capsize=4, color="#7fbf7f", edgecolor="black", width=0.6)
    elif kind.startswith("Box"):
        ax.boxplot(data, positions=x, widths=0.5, showfliers=False)
    else:
        ok = [i for i, d in enumerate(data) if len(d) > 1]
        if ok:
            ax.violinplot([data[i] for i in ok], positions=x[ok], showmedians=True)
    rng = np.random.default_rng(0)
    for i, d in enumerate(data):
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(d)), d, s=12, color="black", alpha=0.7, zorder=3)
    ax.set_xticks(x, groups, rotation=30 if len(groups) > 3 else 0, ha="right" if len(groups) > 3 else "center")
    unit = edited["Area_unit"].iloc[0] if "Area_unit" in edited else ""
    ylab = {"CTCF": "CTCF (a.u.)", "CTCF_per_Area": f"CTCF / Area (a.u./{unit})", "Mean": "Mean intensity",
            "IntDen": "Integrated density", "Area": f"Area ({unit})"}[metric]
    ax.set_ylabel(("Relative " if norm else "") + ylab)
    ax.spines[["top", "right"]].set_visible(False)

    # ---- istatistik
    stat_txt = ""
    valid = [d for d in data if len(d) >= 3]
    if len(groups) == 2 and len(valid) == 2:
        t = sps.ttest_ind(*data, equal_var=False)
        u = sps.mannwhitneyu(*data)
        stat_txt = f"Welch t-test p = {t.pvalue:.4g} · Mann–Whitney U p = {u.pvalue:.4g}"
    elif len(groups) > 2 and len(valid) == len(groups):
        a = sps.f_oneway(*data)
        k = sps.kruskal(*data)
        stat_txt = f"One-way ANOVA p = {a.pvalue:.4g} · Kruskal–Wallis p = {k.pvalue:.4g}"
        if len(groups) > 2:
            tk = sps.tukey_hsd(*data)
            rows = [(groups[i], groups[j], tk.pvalue[i, j]) for i in range(len(groups)) for j in range(i + 1, len(groups))]
            stat_txt += "\n\nTukey HSD:\n" + "\n".join(f"- {a_} vs {b_}: p = {p:.4g}" for a_, b_, p in rows)
    fig.tight_layout()
    gc1, gc2 = st.columns([2, 1])
    gc1.pyplot(fig)
    with gc2:
        st.markdown("**İstatistik**")
        st.markdown(stat_txt or "İstatistik için her grupta ≥3 hücre gerekir.")
        st.caption("Not: Hücreler teknik tekrar sayılır; yayın için biyolojik tekrar (deney) "
                   "ortalamalarıyla test önerilir.")
        for fmt in ("png", "pdf", "svg"):
            fb = io.BytesIO()
            fig.savefig(fb, format=fmt, dpi=600 if fmt == "png" else None, bbox_inches="tight")
            st.download_button(f"⬇️ Grafik ({fmt.upper()})", fb.getvalue(), f"CTCF_plot_{stamp}.{fmt}",
                               width="stretch", key=f"dl_{fmt}")
