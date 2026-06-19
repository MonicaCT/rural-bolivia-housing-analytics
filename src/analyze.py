"""Reproducible statistical analysis and publication-quality visualisations."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic"
FIGURES = ROOT / "docs" / "figures"
REPORTS = ROOT / "reports"
PALETTE = {"navy": "#002147", "blue": "#2F6B9A", "gold": "#C9A227",
           "teal": "#2A9D8F", "coral": "#E76F51", "grey": "#62717F"}


def configure_style() -> None:
    np.random.seed(3107)
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update({
        "figure.dpi": 120,
        "savefig.dpi": 180,
        "axes.titleweight": "bold",
        "axes.titlesize": 16,
        "axes.labelsize": 11,
        "font.family": "DejaVu Sans",
        "grid.alpha": 0.20,
        "svg.hashsalt": "vivienda-coroico-portfolio-v1",
    })


def save(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(
        FIGURES / f"{name}.svg",
        bbox_inches="tight",
        facecolor="white",
        metadata={"Date": None},
    )
    plt.close(fig)


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna()
    return float(np.average(values[mask], weights=weights[mask]))


def bootstrap_ci(values: pd.Series, statistic=np.mean, seed: int = 3107) -> tuple[float, float]:
    clean = values.dropna().to_numpy()
    rng = np.random.default_rng(seed)
    estimates = [statistic(rng.choice(clean, len(clean), replace=True)) for _ in range(2_000)]
    return tuple(np.quantile(estimates, [0.025, 0.975]))


def fit_housing_model(households: pd.DataFrame):
    model_data = households.copy()
    for column in ["head_education_years", "monthly_income_bob", "household_size"]:
        model_data[column] = model_data[column].fillna(model_data[column].median())
    model_data["log_income"] = np.log1p(model_data["monthly_income_bob"])
    model_data["woman_head"] = (model_data["head_gender"] == "Woman").astype(int)
    for source, target in [
        ("head_education_years", "education_z"),
        ("log_income", "log_income_z"),
        ("household_size", "hh_size_z"),
    ]:
        model_data[target] = (model_data[source] - model_data[source].mean()) / model_data[source].std()
    predictors = ["education_z", "log_income_z", "hh_size_z", "woman_head"]
    X = sm.add_constant(model_data[predictors])
    model = sm.GLM(model_data["adequate_housing"], X, family=sm.families.Binomial()).fit()
    return model, model_data, predictors


def plot_population_pyramid(members: pd.DataFrame) -> None:
    bins = np.arange(0, 101, 10)
    labels = [f"{start}-{start + 9}" for start in bins[:-1]]
    data = members.assign(age_group=pd.cut(members.age, bins=bins, labels=labels, right=False))
    counts = data.groupby(["age_group", "gender"], observed=False).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(9, 6))
    y = np.arange(len(counts))
    ax.barh(y, -counts.get("Man", 0), color=PALETTE["blue"], label="Men")
    ax.barh(y, counts.get("Woman", 0), color=PALETTE["gold"], label="Women")
    ax.set(yticks=y, yticklabels=counts.index, xlabel="Synthetic population count",
           ylabel="Age group", title="Population structure by age and gender")
    ax.xaxis.set_major_formatter(lambda value, _: f"{abs(int(value))}")
    ax.legend(frameon=False, ncol=2, loc="lower right")
    sns.despine(ax=ax, left=True)
    save(fig, "01_population_pyramid")


def plot_missingness(households: pd.DataFrame, members: pd.DataFrame) -> None:
    missing = pd.concat([
        households.isna().mean().rename("Households"),
        members.isna().mean().rename("Members"),
    ], axis=1).fillna(0)
    missing = (missing.max(axis=1).sort_values().tail(8) * 100)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(missing.index, missing.values, color=PALETTE["coral"])
    for i, value in enumerate(missing.values):
        ax.text(value + 0.3, i, f"{value:.1f}%", va="center", fontsize=10)
    ax.set(xlabel="Missing observations (%)", ylabel="", title="Missingness is measured, not hidden")
    ax.set_xlim(0, max(18, missing.max() + 3))
    sns.despine(ax=ax, left=True)
    save(fig, "02_missingness")


def plot_income(households: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.histplot(households, x="monthly_income_bob", bins=12, color=PALETTE["teal"], ax=axes[0])
    axes[0].set(title="Monthly household income", xlabel="BOB per month", ylabel="Households")
    sns.boxplot(households, x="head_gender", y="monthly_income_bob", hue="head_gender",
                palette=[PALETTE["gold"], PALETTE["blue"]], legend=False, ax=axes[1])
    sns.stripplot(households, x="head_gender", y="monthly_income_bob", color="white",
                  edgecolor=PALETTE["navy"], linewidth=0.7, alpha=0.8, ax=axes[1])
    axes[1].set(title="Income distribution by head gender", xlabel="", ylabel="BOB per month")
    fig.suptitle("Income distributions reveal more than a single average", fontweight="bold", y=1.03)
    sns.despine(fig=fig)
    save(fig, "03_income_distribution")


def plot_housing_by_zone(households: pd.DataFrame) -> None:
    grouped = households.groupby("zone")["adequate_housing"].agg(["mean", "count"]).reset_index()
    grouped["se"] = np.sqrt(grouped["mean"] * (1 - grouped["mean"]) / grouped["count"])
    grouped["lower"] = np.clip(grouped["mean"] - 1.96 * grouped["se"], 0, 1)
    grouped["upper"] = np.clip(grouped["mean"] + 1.96 * grouped["se"], 0, 1)
    fig, ax = plt.subplots(figsize=(9, 5))
    error = np.vstack([grouped["mean"] - grouped["lower"], grouped["upper"] - grouped["mean"]])
    ax.errorbar(grouped.zone, grouped["mean"] * 100, yerr=error * 100, fmt="o",
                markersize=11, capsize=6, color=PALETTE["navy"], ecolor=PALETTE["gold"])
    ax.set(title="Adequate housing by synthetic zone", xlabel="", ylabel="Households (%)", ylim=(0, 105))
    ax.text(0.01, -0.20, "Points show estimates; bars show approximate 95% confidence intervals.",
            transform=ax.transAxes, fontsize=9, color=PALETTE["grey"])
    sns.despine(ax=ax)
    save(fig, "04_housing_by_zone")


def plot_service_access(households: pd.DataFrame) -> None:
    services = ["electricity", "water_improved", "sanitation_improved", "wall_quality", "floor_quality"]
    labels = ["Electricity", "Improved water", "Improved sanitation", "Quality walls", "Quality floor"]
    rates = households[services].mean().mul(100).sort_values()
    label_map = dict(zip(services, labels, strict=True))
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = sns.color_palette("crest", len(rates))
    ax.barh([label_map[index] for index in rates.index], rates.values, color=colors)
    for i, value in enumerate(rates.values):
        ax.text(value + 1, i, f"{value:.0f}%", va="center", fontsize=10)
    ax.set(title="Housing service and material indicators", xlabel="Synthetic households (%)",
           ylabel="", xlim=(0, 105))
    sns.despine(ax=ax, left=True)
    save(fig, "05_service_access")


def plot_gender_outcomes(members: pd.DataFrame) -> None:
    summary = members.groupby("gender").agg(
        literacy=("literate", "mean"), employment=("employed", "mean")
    ).mul(100).T
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(summary))
    ax.hlines(y, summary.min(axis=1), summary.max(axis=1), color="#D8DEE4", linewidth=6)
    ax.scatter(summary["Woman"], y, s=160, color=PALETTE["gold"], label="Women", zorder=3)
    ax.scatter(summary["Man"], y, s=160, color=PALETTE["blue"], label="Men", zorder=3)
    ax.set(yticks=y, yticklabels=["Literacy", "Employment"], xlabel="Synthetic members (%)",
           ylabel="", title="Gender gaps should be shown directly")
    ax.legend(frameon=False, ncol=2)
    sns.despine(ax=ax, left=True)
    save(fig, "06_gender_outcomes")


def plot_vulnerability(households: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(households, x="monthly_income_bob", y="vulnerability_index",
                    hue="adequate_housing", size="household_size", sizes=(45, 220),
                    palette={0: PALETTE["coral"], 1: PALETTE["teal"]}, alpha=0.85, ax=ax)
    ax.set(title="Household vulnerability combines several dimensions",
           xlabel="Monthly household income (BOB)", ylabel="Vulnerability index (0-100)")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[:3], ["Housing adequacy", "Inadequate", "Adequate"], frameon=False)
    sns.despine(ax=ax)
    save(fig, "07_vulnerability_income")


def plot_correlations(households: pd.DataFrame) -> None:
    columns = ["head_education_years", "monthly_income_bob", "household_size", "crop_diversity",
               "housing_score", "vulnerability_index"]
    corr = households[columns].corr(method="spearman")
    labels = ["Education", "Income", "HH size", "Crop diversity", "Housing", "Vulnerability"]
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, square=True,
                xticklabels=labels, yticklabels=labels, cbar_kws={"shrink": 0.75}, ax=ax)
    ax.set_title("Spearman correlations: association is not causation", pad=16)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    save(fig, "08_correlation_heatmap")


def plot_model(model, predictors: list[str]) -> None:
    labels = {
        "education_z": "Education (+1 SD)", "log_income_z": "Income (+1 SD)",
        "hh_size_z": "Household size (+1 SD)", "woman_head": "Woman-headed household",
    }
    estimates = np.exp(model.params[predictors])
    intervals = np.exp(model.conf_int().loc[predictors])
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(predictors))
    ax.errorbar(estimates, y, xerr=np.vstack([estimates - intervals[0], intervals[1] - estimates]),
                fmt="o", color=PALETTE["navy"], ecolor=PALETTE["gold"], capsize=5, markersize=9)
    ax.axvline(1, color=PALETTE["grey"], linestyle="--", linewidth=1)
    ax.set_xscale("log")
    ax.set(yticks=y, yticklabels=[labels[item] for item in predictors], xlabel="Odds ratio (log scale)",
           ylabel="", title="Factors associated with adequate housing")
    ax.text(0.01, -0.20, "Exploratory model on synthetic data; intervals quantify uncertainty.",
            transform=ax.transAxes, fontsize=9, color=PALETTE["grey"])
    sns.despine(ax=ax, left=True)
    save(fig, "09_model_coefficients")


def plot_agriculture(households: pd.DataFrame) -> None:
    grouped = households.groupby("crop_diversity").agg(
        income=("monthly_income_bob", "median"), households=("household_id", "count")
    ).reset_index()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(grouped.crop_diversity, grouped.income, color=PALETTE["teal"], marker="o", linewidth=3)
    for _, row in grouped.iterrows():
        ax.annotate(f"n={int(row.households)}", (row.crop_diversity, row.income),
                    xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8)
    ax.set(title="Agricultural diversity and household income", xlabel="Number of crop categories",
           ylabel="Median monthly income (BOB)")
    sns.despine(ax=ax)
    save(fig, "10_agriculture_diversity")


def export_results(households: pd.DataFrame, members: pd.DataFrame, model, predictors: list[str]) -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    adequacy = weighted_mean(households.adequate_housing, households.survey_weight)
    adequacy_ci = bootstrap_ci(households.adequate_housing)
    metrics = {
        "households": int(len(households)),
        "members": int(len(members)),
        "adequate_housing_weighted_pct": round(adequacy * 100, 1),
        "adequate_housing_ci_pct": [round(value * 100, 1) for value in adequacy_ci],
        "median_income_bob": round(float(households.monthly_income_bob.median()), 0),
        "income_missing_pct": round(float(households.monthly_income_bob.isna().mean() * 100), 1),
        "mean_vulnerability": round(float(households.vulnerability_index.mean()), 1),
        "privacy_status": "Synthetic public data only",
    }
    (REPORTS / "key_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    conf = model.conf_int()
    results = pd.DataFrame({
        "term": predictors,
        "odds_ratio": np.exp(model.params[predictors]),
        "ci_low": np.exp(conf.loc[predictors, 0]),
        "ci_high": np.exp(conf.loc[predictors, 1]),
        "p_value": model.pvalues[predictors],
    })
    results[["odds_ratio", "ci_low", "ci_high", "p_value"]] = results[
        ["odds_ratio", "ci_low", "ci_high", "p_value"]
    ].round(10)
    results.to_csv(REPORTS / "model_results.csv", index=False)
    return metrics


def run(households: pd.DataFrame, members: pd.DataFrame) -> dict:
    configure_style()
    model, _, predictors = fit_housing_model(households)
    plot_population_pyramid(members)
    plot_missingness(households, members)
    plot_income(households)
    plot_housing_by_zone(households)
    plot_service_access(households)
    plot_gender_outcomes(members)
    plot_vulnerability(households)
    plot_correlations(households)
    plot_model(model, predictors)
    plot_agriculture(households)
    return export_results(households, members, model, predictors)


if __name__ == "__main__":
    from src.validate import validate_files

    household_data, member_data = validate_files(DATA)
    print(json.dumps(run(household_data, member_data), indent=2))
