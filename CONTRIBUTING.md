# Contributing to CellVerity

Thank you for your interest in CellVerity. Bug reports, questions, test images from other microscopes and code
contributions are all welcome.

## Reporting a problem or asking a question
Open an [issue](https://github.com/erdal-b-dot/cellverity/issues) and include:

1. **Version and system** — in the program: **Help ▸ About / version info ▸ Copy info**, then paste it.
2. **What you did and what you expected** — the steps, and what happened instead (a screenshot helps).
3. **The image, if you can share it** — the raw FITC (and DAPI) file *as saved by the microscope software*
   (not a screenshot or a re-saved copy; calibration and exposure are read from the original file).
   If the image is unpublished, say so and we can arrange a private transfer.

Images from microscopes or cameras other than the tested one (Olympus BX43 + DP74, cellSens) are especially useful:
they let us check calibration and segmentation on new image types.

## Contributing code
Changes go through a **fork + pull request** so that each contribution is reviewed, tested and credited to its
author.

1. Fork the repository on GitHub and clone your fork.
2. Create a branch: `git checkout -b short-description`.
3. Set up the environment (Python 3.12 via [uv](https://docs.astral.sh/uv/)):
   ```bash
   uv venv --python 3.12 .venv
   uv pip install --python .venv -r requirements-desktop.txt
   .venv/bin/python desktop.py            # Windows: .venv\Scripts\python desktop.py
   ```
4. Make your change, then run the tests (below).
5. Commit with a clear message (Turkish or English) and open a pull request against `main`. Describe *what* changed
   and *why*; include a screenshot for interface changes.

The **Tests** workflow runs automatically on every pull request (Linux, Windows, macOS). A pull request is merged
when the tests pass and the change has been reviewed.

## Tests
```bash
.venv/bin/python tests/test_core.py
```
Tests that need the unpublished validation images (`ornek/`, not in the repository) are **skipped** automatically;
the others use the public example data in `examples/` (CC BY 4.0) and run everywhere. Add a test for any new
calculation, file format or bug fix — ideally one that uses `examples/` or a small synthetic image.

## Ground rules for changes
- **Measurements must stay identical to ImageJ/Fiji.** Any change to `core.py`, `report.py` or `fiji.py` that alters
  a measured value needs a reason in the pull request and a test; the Fiji-verified tests must keep passing.
- **Provenance:** a new setting that can change results must be written to the Excel output (a column or the
  *Methods* sheet), so that measurements remain reproducible.
- **Interface text** is written in Turkish inside `T("…")` and translated in `locales/en_source.py`; then run
  `.venv/bin/python locales/en_source.py` to rebuild `locales/en.json`. The tests check that every text has a
  translation with the same placeholders (`{0}`, `{1:.2f}` …).
- **Colours and icons** come from `theme.py` (`theme.COLORS`, `theme.icon("name")`, SVGs in `assets/icons/` using
  `currentColor`). Do not hard-code colours in the interface. Colours drawn *on the image* (cell boundaries, nuclei,
  background boxes) are data, not theme.
- **User guide:** describe user-visible changes in `docs/KULLANIM_KILAVUZU.md` (Turkish) and `docs/USER_GUIDE.md`
  (English); rebuild with `cd docs && ../.venv/bin/python build_html.py`.
- **Packaging:** new data files must be added to `cellverity.spec`, otherwise the installed program will not find
  them.

## Use of AI tools
If you use AI assistants for code or text, say so in the pull request (tool and what it was used for). You remain
responsible for reviewing, testing and understanding everything you submit. The project itself was developed with
substantial AI assistance (Claude Code); the authors directed the design, reviewed the changes and performed the
validation.

## Credit
Contributors are listed in the README and in the Zenodo record of the release that includes their work. If you
co-author a commit, add a trailer with the e-mail address linked to your GitHub account:
`Co-authored-by: Name Surname <email>`.

## Code of conduct
Be respectful and constructive. Scientific disagreement is welcome; personal attacks are not. Problems can be
reported privately to the maintainer (erdal.balcan@cbu.edu.tr).

---

## Türkçe özet
- **Hata bildirimi / soru:** GitHub'da *Issue* açın. **Yardım ▸ Hakkında / sürüm bilgisi ▸ Bilgileri kopyala**
  çıktısını, yaptığınız adımları ve mümkünse mikroskobun kaydettiği **ham** görüntüyü ekleyin.
- **Kod katkısı:** *fork* → yeni dal → değişiklik → `tests/test_core.py` → *pull request*. Testler her pull
  request'te Linux, Windows ve macOS'ta kendiliğinden çalışır.
- **Kurallar:** ölçümler ImageJ/Fiji ile birebir aynı kalmalı; sonucu değiştirebilecek her ayar Excel'e yazılmalı;
  arayüz metinleri `T("…")` + `locales/en_source.py`; renkler/simgeler `theme.py`'den; kullanıcıya görünen
  değişiklik kılavuzlara yazılmalı.
- **Yapay zekâ kullanımı** pull request'te belirtilmeli. **Katkıda bulunanlar** README'de ve Zenodo kaydında yer alır.
