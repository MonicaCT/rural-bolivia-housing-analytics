# Validation Report - Rural Bolivia Housing Analytics Website

Date: 2026-07-13

## Scope

Reusable portfolio website applied to the existing rural Bolivia housing analytics repository.

## Files reviewed or reused

- `README.md`
- `docs/index.html`
- `docs/research-paper.html`
- `docs/figures/*.svg`
- `reports/executive-summary.md`
- `reports/key_metrics.json`
- `reports/model_results.csv`
- `reports/STROBE-checklist.md`
- `reports/technical-report.qmd`
- `sql/analytical_model.sql`
- `tests/test_pipeline.py`
- `CITATION.cff`
- `LICENSE`

## Validation checklist

| Check | Status | Notes |
|---|---|---|
| HTML page created from reusable template | PASS | `docs/index.html` uses the approved template CSS and JS. |
| Relative routes | PASS | Local routes inside Pages point to files under `docs/`; files outside `docs/` use GitHub links. |
| Figures | PASS | Eight existing SVG figures are reused from `docs/figures`. |
| Tables | PASS | Existing embedded paper tables and `reports/model_results.csv` are linked without regeneration. |
| Report product | PASS | `docs/research-paper.html` is reused as the main report product. |
| Privacy statement | PASS | Page states that public data are synthetic and original identifiable records are not distributed. |
| Sensitive strings | PASS | No Windows local paths or credential-like strings were introduced. |
| Responsive layout | PASS | Uses the approved responsive template CSS. |
| Keyboard navigation | PASS | Includes skip link, semantic navigation and template menu behavior. |
| README navigation | PASS | Top buttons now expose Website, Report, Main Figures, Executive Tables, Methodology, Repository and Back to Portfolio. |
| Data and models intact | PASS | No data, scripts, models, reports, figures or tests were modified. |
| GitHub Pages | WARNING | Repository is prepared for `main` / `docs`; public publication depends on GitHub Pages configuration. |

## GitHub Pages

Expected configuration:

```text
Source: Deploy from a branch
Branch: main
Folder: /docs
```

If the public URL returns 404, the expected status is:

```text
Pending human configuration
```

## No pipeline execution

No Python, R, SQL, model, data-generation, figure-generation or dashboard-generation commands were run during this phase.
