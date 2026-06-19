"""Build synthetic data, validate it, run analysis, and publish static documentation."""

from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

from src.analyze import run
from src.generate_synthetic import generate
from src.validate import validate

ROOT = Path(__file__).resolve().parents[1]


def write_dictionary(households: pd.DataFrame, members: pd.DataFrame) -> None:
    descriptions = {
        "household_id": "Random synthetic household identifier",
        "member_id": "Random synthetic person identifier",
        "zone": "Synthetic aggregate area; not a real location",
        "adequate_housing": "Composite binary outcome based on services, materials and crowding",
        "housing_score": "Share of six adequate housing components",
        "vulnerability_index": "Demonstration index from housing, education and income (0-100)",
        "survey_weight": "Synthetic demonstration survey weight",
    }
    rows = []
    for table_name, frame in [("households", households), ("members", members)]:
        for column in frame.columns:
            rows.append({
                "table": table_name,
                "variable": column,
                "dtype": str(frame[column].dtype),
                "description": descriptions.get(column, column.replace("_", " ").capitalize()),
                "missing_n": int(frame[column].isna().sum()),
            })
    pd.DataFrame(rows).to_csv(ROOT / "data" / "data_dictionary.csv", index=False)


def write_executive_summary(metrics: dict) -> None:
    text = f"""# Executive summary

> **Demonstration only:** every observation in this public repository is synthetic.

This reproducible case study contains **{metrics['households']} synthetic households** and
**{metrics['members']} synthetic household members**. The weighted adequate-housing estimate is
**{metrics['adequate_housing_weighted_pct']}%** (bootstrap 95% interval:
{metrics['adequate_housing_ci_pct'][0]}%-{metrics['adequate_housing_ci_pct'][1]}%). Median synthetic
monthly household income is **BOB {metrics['median_income_bob']:.0f}**.

## Decisions supported

- Prioritise service access and overcrowding rather than relying on income alone.
- Report uncertainty and missingness beside every headline result.
- Treat observed associations as exploratory, not causal.
- Use disaggregated gender indicators while protecting small groups from disclosure.

## Limitations

The dataset is synthetic and cannot support claims about Coroico or Bolivia. The sample is deliberately
small, the survey weights are illustrative, and the housing index is a documented demonstration rather
than a validated policy instrument.
"""
    (ROOT / "reports" / "executive-summary.md").write_text(text, encoding="utf-8")


def write_research_paper(households: pd.DataFrame, members: pd.DataFrame, metrics: dict) -> None:
    model = pd.read_csv(ROOT / "reports" / "model_results.csv")
    term_labels = {
        "education_z": "Education (+1 SD)",
        "log_income_z": "Log income (+1 SD)",
        "hh_size_z": "Household size (+1 SD)",
        "woman_head": "Woman-headed household",
    }
    model_rows = "".join(
        "<tr>"
        f"<td>{term_labels[row.term]}</td><td>{row.odds_ratio:.2f}</td>"
        f"<td>{row.ci_low:.2f}-{row.ci_high:.2f}</td><td>{row.p_value:.3f}</td>"
        "</tr>"
        for row in model.itertuples()
    )
    income = households["monthly_income_bob"].dropna()
    education = households["head_education_years"].dropna()
    summary_rows = [
        ("Households, n", f"{len(households)}"),
        ("Household members, n", f"{len(members)}"),
        ("Household size, median (IQR)",
         f"{households.household_size.median():.1f} ({households.household_size.quantile(.25):.1f}-{households.household_size.quantile(.75):.1f})"),
        ("Age of household head, mean (SD)",
         f"{households.head_age.mean():.1f} ({households.head_age.std():.1f})"),
        ("Woman-headed households, %", f"{(households.head_gender == 'Woman').mean() * 100:.1f}"),
        ("Education of head, median years (IQR)",
         f"{education.median():.1f} ({education.quantile(.25):.1f}-{education.quantile(.75):.1f})"),
        ("Monthly income, median BOB (IQR)",
         f"{income.median():.0f} ({income.quantile(.25):.0f}-{income.quantile(.75):.0f})"),
        ("Income missing, %", f"{metrics['income_missing_pct']:.1f}"),
        ("Adequate housing, weighted % (95% CI)",
         f"{metrics['adequate_housing_weighted_pct']:.1f} ({metrics['adequate_housing_ci_pct'][0]:.1f}-{metrics['adequate_housing_ci_pct'][1]:.1f})"),
        ("Vulnerability index, mean (SD)",
         f"{households.vulnerability_index.mean():.1f} ({households.vulnerability_index.std():.1f})"),
    ]
    summary_html = "".join(f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in summary_rows)
    paper = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Research paper | Privacy-first household survey analysis</title>
<style>
:root{{--navy:#002147;--blue:#2f6b9a;--gold:#c9a227;--ink:#20262e;--muted:#5f6c78;--line:#d9dee3}}
*{{box-sizing:border-box}} html{{scroll-behavior:smooth}} body{{margin:0;background:#eef1f4;color:var(--ink);font:17px/1.72 Georgia,'Times New Roman',serif}}
.paper{{max-width:980px;margin:2rem auto;background:white;padding:5rem 6.5rem;box-shadow:0 8px 36px #00214718}}
.eyebrow{{font:700 .78rem/1.3 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--blue)}}
h1{{font-size:2.65rem;line-height:1.13;color:var(--navy);margin:.7rem 0 1rem}} h2{{font-size:1.55rem;color:var(--navy);border-bottom:1px solid var(--line);padding-bottom:.3rem;margin-top:2.7rem}}
h3{{font-size:1.15rem;color:var(--navy);margin-top:1.8rem}} p{{text-align:justify}} a{{color:var(--blue)}}
.authors,.meta{{font-family:system-ui,sans-serif}} .authors{{font-size:1.05rem;font-weight:700}} .meta{{font-size:.88rem;color:var(--muted)}}
.notice{{margin:2rem 0;padding:1rem 1.2rem;border-left:5px solid var(--gold);background:#fff9e8;font-family:system-ui,sans-serif;font-size:.9rem}}
.abstract{{border-top:3px solid var(--navy);border-bottom:1px solid var(--line);padding:1rem 0;margin:2.2rem 0}} .abstract h2{{border:0;margin:.2rem 0}}
.keywords{{font-size:.92rem}} .toc{{background:#f6f8fa;padding:1rem 1.5rem;font-family:system-ui,sans-serif;font-size:.9rem;columns:2}} .toc a{{display:block;text-decoration:none;margin:.25rem}}
table{{width:100%;border-collapse:collapse;margin:1.2rem 0 2rem;font-size:.91rem}} caption{{text-align:left;font-weight:700;margin-bottom:.5rem;color:var(--navy)}} th{{background:var(--navy);color:white;text-align:left}} th,td{{padding:.6rem .7rem;border-bottom:1px solid var(--line)}} tr:nth-child(even){{background:#f7f8fa}}
figure{{margin:2rem 0}} figure img{{width:100%;height:auto}} figcaption{{font-size:.88rem;color:var(--muted);line-height:1.5}}
.equation{{text-align:center;margin:1.5rem 0;font-size:1.08rem;overflow-x:auto}} .number{{float:right;color:var(--muted)}}
.callout{{padding:1rem 1.2rem;background:#eef6f5;border:1px solid #c9e4df;font-family:system-ui,sans-serif;font-size:.9rem}}
.statements{{font-size:.93rem;background:#f6f8fa;padding:1rem 1.4rem}} .references li{{margin-bottom:.65rem}}
.paper-nav{{position:sticky;top:0;background:var(--navy);color:white;padding:.7rem 1rem;font:600 .88rem system-ui,sans-serif;z-index:2}} .paper-nav a{{color:white;margin-right:1rem;text-decoration:none}}
@media(max-width:760px){{.paper{{margin:0;padding:2.5rem 1.3rem}}h1{{font-size:2rem}}.toc{{columns:1}}}}
@media print{{body{{background:white;font-size:11pt}}.paper-nav{{display:none}}.paper{{max-width:none;margin:0;padding:1.6cm;box-shadow:none}}a{{color:inherit;text-decoration:none}}h2{{break-after:avoid}}figure,table{{break-inside:avoid}}@page{{size:A4;margin:1.6cm}}}}
</style></head><body>
<nav class="paper-nav"><a href="index.html">← Dashboard</a><a href="#abstract">Abstract</a><a href="#methods">Methods</a><a href="#results">Results</a><a href="#references">References</a></nav>
<article class="paper">
<div class="eyebrow">Research article · Cross-sectional methods demonstration · STROBE-aligned</div>
<h1>Socioeconomic and Housing Conditions in Rural Bolivia: A Privacy-First Reproducible Survey Analysis</h1>
<div class="authors">Monica Cueto Tapia</div>
<div class="meta">Reproducible household survey analysis · Version 1.0 · 18 June 2026</div>
<aside class="notice"><strong>Research integrity statement.</strong> Every public observation is synthetic. This article demonstrates a defensible research workflow and must not be cited as empirical evidence about Coroico or Bolivia.</aside>

<section class="abstract" id="abstract"><h2>Abstract</h2>
<p><strong>Background:</strong> Household surveys can inform housing and social policy, but public reproducibility may conflict with respondent confidentiality. <strong>Objective:</strong> To demonstrate a privacy-first, reproducible workflow for analysing housing adequacy and socioeconomic vulnerability. <strong>Methods:</strong> We generated 60 synthetic households and 271 synthetic members, validated referential integrity and disclosure constraints, quantified missingness, calculated weighted descriptive estimates with 2,000-resample bootstrap intervals, and fitted a parsimonious logistic regression. <strong>Results:</strong> Weighted adequate housing was {metrics['adequate_housing_weighted_pct']:.1f}% (95% bootstrap interval {metrics['adequate_housing_ci_pct'][0]:.1f}%-{metrics['adequate_housing_ci_pct'][1]:.1f}%). Synthetic median monthly income was BOB {metrics['median_income_bob']:.0f}, with {metrics['income_missing_pct']:.1f}% missing. All exploratory regression intervals crossed the null value, appropriately signalling limited precision. <strong>Conclusions:</strong> Reproducibility does not require publication of identifiable microdata. A strong analytical product combines privacy controls, explicit estimands, uncertainty, reproducible code and restrained interpretation.</p>
<p class="keywords"><strong>Keywords:</strong> household survey; housing adequacy; reproducible research; synthetic data; missing data; logistic regression; research ethics</p></section>

<nav class="toc"><strong>Contents</strong><a href="#introduction">1. Introduction</a><a href="#methods">2. Methods</a><a href="#results">3. Results</a><a href="#discussion">4. Discussion</a><a href="#limitations">5. Limitations</a><a href="#conclusion">6. Conclusion</a><a href="#statements">Declarations</a><a href="#references">References</a></nav>

<section id="introduction"><h2>1. Introduction</h2>
<p>Housing is multidimensional: construction materials, basic services, crowding and household resources jointly shape wellbeing. Survey analysis often compresses these dimensions into percentages without reporting denominators, uncertainty, missingness or the assumptions behind composite measures. These omissions weaken both scientific interpretation and operational decision-making.</p>
<p>A second challenge is disclosure. Household microdata may combine names, ages, occupations, income, health information and property characteristics. Removing a name column is insufficient when rare combinations can re-identify respondents. This project therefore treats privacy architecture as part of statistical quality rather than as an administrative appendix.</p>
<h3>1.1 Research questions</h3><ol><li>How can adequate housing be defined transparently from multiple components?</li><li>Which socioeconomic characteristics are associated with adequate housing in a small cross-sectional demonstration?</li><li>How should missingness and sampling uncertainty be communicated?</li><li>How can survey analysis remain reproducible without exposing confidential source records?</li></ol></section>

<section id="methods"><h2>2. Methods</h2>
<h3>2.1 Study design and reporting framework</h3><p>The paper follows the Introduction-Methods-Results-Discussion structure and is mapped to the STROBE checklist for cross-sectional studies [1,2]. It is a methodological demonstration, not a registered observational study.</p>
<h3>2.2 Data generation and units of analysis</h3><p>A fixed pseudorandom seed generated 60 households and 271 nested members. Aggregate zones are fictional. No value was copied, perturbed or sampled from a real respondent. Household and person denominators are kept separate throughout.</p>
<h3>2.3 Privacy and quality controls</h3><p>Automated tests reject direct-identifier columns, duplicate identifiers, orphaned member records, invalid binary outcomes and impossible ages. Public file rules exclude SPSS, legacy Word and private raw-data directories from version control.</p>
<h3>2.4 Estimands and uncertainty</h3><p>For survey weights <em>w</em><sub>i</sub> and outcome <em>y</em><sub>i</sub>, the weighted mean is:</p>
<div class="equation">ȳ<sub>w</sub> = Σ<sub>i</sub> w<sub>i</sub>y<sub>i</sub> / Σ<sub>i</sub>w<sub>i</sub> <span class="number">(1)</span></div>
<p>The 95% interval uses the 2.5th and 97.5th percentiles of 2,000 household bootstrap estimates:</p>
<div class="equation">CI<sub>.95</sub>(θ̂) = [ Q<sub>.025</sub>(θ̂*), Q<sub>.975</sub>(θ̂*) ] <span class="number">(2)</span></div>
<h3>2.5 Housing and vulnerability measures</h3><p>The housing score is the unweighted share of six documented components: electricity, improved water, improved sanitation, quality walls, quality floor and absence of severe crowding. Adequate housing requires a score of at least two thirds. The vulnerability index combines housing, head education and capped income:</p>
<div class="equation">V<sub>i</sub> = 100[1 − (0.42H<sub>i</sub> + 0.28E<sub>i</sub>/16 + 0.30 min(Y<sub>i</sub>/6000,1))] + ε<sub>i</sub> <span class="number">(3)</span></div>
<h3>2.6 Exploratory model</h3><p>A logistic generalised linear model estimates conditional associations with adequate housing:</p>
<div class="equation">log[p<sub>i</sub>/(1−p<sub>i</sub>)] = β<sub>0</sub> + β<sub>1</sub>E<sub>i</sub> + β<sub>2</sub>log(Y<sub>i</sub>+1) + β<sub>3</sub>S<sub>i</sub> + β<sub>4</sub>G<sub>i</sub> <span class="number">(4)</span></div>
<p>Education, log income and household size are standardised. Missing education and income are median-filled for this demonstration; a substantive study should use design-aware multiple imputation and sensitivity analysis [5]. No coefficient is interpreted causally.</p></section>

<section id="results"><h2>3. Results</h2>
<table><caption>Table 1. Synthetic sample characteristics</caption><thead><tr><th>Characteristic</th><th>Estimate</th></tr></thead><tbody>{summary_html}</tbody></table>
<figure><img src="figures/02_missingness.svg" alt="Missing data audit"><figcaption><strong>Figure 1.</strong> Missingness by variable. Income has the largest deliberately introduced missing proportion. Missingness is displayed before outcome modelling.</figcaption></figure>
<h3>3.1 Housing adequacy and services</h3><p>The weighted adequate-housing estimate was {metrics['adequate_housing_weighted_pct']:.1f}% (95% bootstrap interval {metrics['adequate_housing_ci_pct'][0]:.1f}%-{metrics['adequate_housing_ci_pct'][1]:.1f}%). Wide zone-specific intervals reflect the small number of households and discourage unstable rankings.</p>
<figure><img src="figures/04_housing_by_zone.svg" alt="Housing adequacy by synthetic zone"><figcaption><strong>Figure 2.</strong> Adequate housing by fictional aggregate zone. Points are estimates and bars are approximate 95% intervals.</figcaption></figure>
<h3>3.2 Socioeconomic patterning</h3><p>Median synthetic monthly household income was BOB {metrics['median_income_bob']:.0f}. The mean vulnerability index was {metrics['mean_vulnerability']:.1f} on a 0-100 scale. Correlations describe co-movement only and do not establish pathways of causation.</p>
<figure><img src="figures/07_vulnerability_income.svg" alt="Income and vulnerability"><figcaption><strong>Figure 3.</strong> Income and multidimensional vulnerability. Point size indicates household size and colour indicates housing classification.</figcaption></figure>
<h3>3.3 Exploratory regression</h3>
<table><caption>Table 2. Exploratory logistic model for adequate housing</caption><thead><tr><th>Predictor</th><th>Odds ratio</th><th>95% CI</th><th>p-value</th></tr></thead><tbody>{model_rows}</tbody></table>
<div class="callout"><strong>Interpretation:</strong> every confidence interval includes 1. The defensible conclusion is insufficient precision to distinguish these adjusted associations from the null, not evidence that the predictors have no relationship with housing.</div>
<figure><img src="figures/09_model_coefficients.svg" alt="Regression odds ratios"><figcaption><strong>Figure 4.</strong> Adjusted odds ratios on a logarithmic scale. The dashed vertical line marks the null value.</figcaption></figure></section>

<section id="discussion"><h2>4. Discussion</h2><p>This analysis integrates disclosure controls, explicit denominators, uncertainty, documented measurement and automated reproduction. The wide intervals are analytically important: they show why complex machine learning and detailed subgroup ranking would be inappropriate for a 60-household study.</p><p>For a real survey, scientific interpretation would depend on information that cannot be reconstructed from the data alone: target population, sampling frame, selection probabilities, field dates, non-response process, questionnaire, interviewer procedures and ethics approval. These elements should be documented before substantive re-analysis.</p></section>
<section id="limitations"><h2>5. Limitations</h2><ul><li>Synthetic observations cannot validate or reproduce the original empirical findings.</li><li>The demonstration weights do not represent a real sampling design.</li><li>The housing threshold and vulnerability coefficients require substantive validation.</li><li>Median filling understates missing-data uncertainty and is used only to keep the example transparent.</li><li>Binary gender measurement is an artificial simplification.</li><li>Cross-sectional associations cannot identify causal effects.</li></ul></section>
<section id="conclusion"><h2>6. Conclusion</h2><p>Strong research communication is not the accumulation of charts or equations. It is the alignment of a meaningful question, appropriate estimand, transparent method, uncertainty, ethical data handling and restrained conclusion. This workflow provides a publishable foundation once authorised, anonymised source data and a complete survey design are available.</p></section>
<section class="statements" id="statements"><h2>Declarations</h2><p><strong>Ethics and privacy:</strong> No real participant record is processed by the public pipeline. <strong>Data availability:</strong> Synthetic CSV files and their generator are included. <strong>Code availability:</strong> The complete pipeline, tests and dependency lockfile accompany this paper. <strong>Funding:</strong> No external funding is declared for this demonstration. <strong>Competing interests:</strong> None declared. <strong>Author contribution:</strong> Monica Cueto Tapia: conceptualisation, methodology, analysis design, interpretation and presentation.</p></section>
<section class="references" id="references"><h2>References</h2><ol>
<li>von Elm E, et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement. <em>Lancet</em>. 2007;370:1453-1457. <a href="https://doi.org/10.1016/S0140-6736(07)61602-X">doi:10.1016/S0140-6736(07)61602-X</a>.</li>
<li>STROBE Initiative. Checklist for cross-sectional studies. <a href="https://www.strobe-statement.org/checklists/">Official checklist</a>.</li>
<li>Lohr SL. <em>Sampling: Design and Analysis</em>. 3rd ed. Chapman and Hall/CRC; 2021.</li>
<li>Peng RD. Reproducible research in computational science. <em>Science</em>. 2011;334:1226-1227. <a href="https://doi.org/10.1126/science.1213847">doi:10.1126/science.1213847</a>.</li>
<li>Little RJA, Rubin DB. <em>Statistical Analysis with Missing Data</em>. 3rd ed. Wiley; 2019.</li>
<li>Wickham H. Tidy data. <em>Journal of Statistical Software</em>. 2014;59:1-23. <a href="https://doi.org/10.18637/jss.v059.i10">doi:10.18637/jss.v059.i10</a>.</li>
</ol></section>
</article></body></html>"""
    (ROOT / "docs" / "research-paper.html").write_text(paper, encoding="utf-8")

    markdown = f"""# Socioeconomic and Housing Conditions in Rural Bolivia

## A Privacy-First Reproducible Survey Analysis

**Author:** Monica Cueto Tapia  
**Reporting framework:** IMRaD; STROBE-aligned cross-sectional methods demonstration  
**Data status:** 100% synthetic public records

## Structured abstract

**Background:** Public reproducibility may conflict with household-survey confidentiality.  
**Methods:** Synthetic data for {len(households)} households and {len(members)} members; data contracts,
weighted estimates, 2,000-resample bootstrap intervals and exploratory logistic regression.  
**Results:** Weighted adequate housing was {metrics['adequate_housing_weighted_pct']:.1f}%
(95% interval {metrics['adequate_housing_ci_pct'][0]:.1f}%-{metrics['adequate_housing_ci_pct'][1]:.1f}).
All model intervals crossed the null.  
**Conclusion:** Strong analysis combines privacy, explicit estimands, uncertainty, reproducible code and
restrained interpretation.

The complete print-ready article, tables, figures, methods, declarations and references are published
as `docs/research-paper.html`.
"""
    (ROOT / "reports" / "research-paper.md").write_text(markdown, encoding="utf-8")


def write_dashboard(metrics: dict) -> None:
    cards = [
        ("Synthetic households", metrics["households"]),
        ("Synthetic members", metrics["members"]),
        ("Adequate housing", f"{metrics['adequate_housing_weighted_pct']}%"),
        ("Median income", f"BOB {metrics['median_income_bob']:.0f}"),
    ]
    card_html = "".join(
        f'<article class="card"><span>{html.escape(str(label))}</span><strong>{value}</strong></article>'
        for label, value in cards
    )
    figures = [
        ("01_population_pyramid", "Population structure"),
        ("02_missingness", "Missing data audit"),
        ("03_income_distribution", "Income distribution"),
        ("04_housing_by_zone", "Housing and uncertainty"),
        ("05_service_access", "Service access"),
        ("06_gender_outcomes", "Gender outcomes"),
        ("07_vulnerability_income", "Multidimensional vulnerability"),
        ("08_correlation_heatmap", "Associations"),
        ("09_model_coefficients", "Exploratory model"),
        ("10_agriculture_diversity", "Agricultural diversity"),
    ]
    figure_html = "".join(
        f'<figure><img src="figures/{name}.svg" alt="{title}"><figcaption>{title}</figcaption></figure>'
        for name, title in figures
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rural Bolivia Household Survey Analysis</title>
<style>
:root{{--navy:#002147;--blue:#2f6b9a;--gold:#c9a227;--ink:#1d2733;--paper:#f5f7f9}}
*{{box-sizing:border-box}} body{{margin:0;font:16px/1.6 system-ui,sans-serif;color:var(--ink);background:var(--paper)}}
header{{background:linear-gradient(135deg,var(--navy),var(--blue));color:white;padding:5rem max(6vw,2rem) 4rem}}
header p{{max-width:760px;font-size:1.15rem}} .badge{{display:inline-block;background:var(--gold);color:#17202a;padding:.35rem .7rem;border-radius:999px;font-weight:700}}
.paper-link{{display:inline-block;margin-top:.8rem;padding:.75rem 1rem;border:2px solid white;border-radius:8px;color:white;text-decoration:none;font-weight:700}}
main{{max-width:1200px;margin:auto;padding:2rem}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem;margin-top:-4rem}}
.card{{background:white;padding:1.2rem;border-radius:12px;box-shadow:0 8px 24px #00214718;border-top:4px solid var(--gold)}}
.card span{{display:block;color:#62717f}} .card strong{{font-size:1.7rem;color:var(--navy)}}
.notice{{margin:2rem 0;padding:1rem 1.2rem;background:#fff8df;border-left:5px solid var(--gold)}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:1.25rem}}
figure{{margin:0;background:white;padding:1rem;border-radius:12px;box-shadow:0 4px 18px #00214710}} img{{width:100%;height:auto}} figcaption{{font-weight:700;color:var(--navy)}}
footer{{padding:2rem;text-align:center;color:#62717f}} @media(max-width:600px){{.gallery{{grid-template-columns:1fr}} header{{padding-top:3rem}}}}
</style></head><body>
<header><span class="badge">Privacy-first reproducible analysis</span><h1>Socioeconomic and Housing Conditions</h1>
<p>A transparent demonstration of survey analysis, uncertainty, statistical modelling and responsible data communication.</p>
<a class="paper-link" href="research-paper.html">Read the STROBE-aligned research paper →</a></header>
<main><section class="cards">{card_html}</section>
<aside class="notice"><strong>Important:</strong> all public observations are synthetic. Results demonstrate methods and must not be interpreted as estimates for Coroico or Bolivia.</aside>
<h2>Analytical narrative</h2><section class="gallery">{figure_html}</section>
<h2>Methodological position</h2><p>Estimates include uncertainty, missing data are disclosed, and the regression is explicitly exploratory. Association is not causation.</p></main>
<footer>Built from code with a fixed random seed and automated validation.</footer></body></html>"""
    (ROOT / "docs" / "index.html").write_text(page, encoding="utf-8")


def build() -> dict:
    households, members = generate(ROOT / "data" / "synthetic")
    validate(households, members)
    write_dictionary(households, members)
    metrics = run(households, members)
    write_executive_summary(metrics)
    write_research_paper(households, members, metrics)
    write_dashboard(metrics)
    return metrics


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
