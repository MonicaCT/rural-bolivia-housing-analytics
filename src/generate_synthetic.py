"""Generate a fully synthetic dataset with the structure of a household survey.

The generated records do not correspond to real people or households. The seed is
fixed so every chart and model in the project can be reproduced.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20250618
N_HOUSEHOLDS = 60
N_MEMBERS = 271


def _household_sizes(rng: np.random.Generator) -> np.ndarray:
    sizes = rng.integers(2, 8, size=N_HOUSEHOLDS)
    while sizes.sum() != N_MEMBERS:
        difference = N_MEMBERS - sizes.sum()
        eligible = np.flatnonzero(sizes < 9) if difference > 0 else np.flatnonzero(sizes > 1)
        idx = rng.choice(eligible)
        sizes[idx] += 1 if difference > 0 else -1
    return sizes


def generate(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    output_dir.mkdir(parents=True, exist_ok=True)
    household_id = np.array([f"SYN-H{i:03d}" for i in range(1, N_HOUSEHOLDS + 1)])
    household_size = _household_sizes(rng)
    zone = rng.choice(["Zone A", "Zone B", "Zone C", "Zone D"], N_HOUSEHOLDS,
                      p=[0.28, 0.27, 0.25, 0.20])
    head_gender = rng.choice(["Woman", "Man"], N_HOUSEHOLDS, p=[0.36, 0.64])
    head_age = np.clip(rng.normal(47, 13, N_HOUSEHOLDS).round(), 22, 82).astype(int)
    education = np.clip(rng.normal(7.5, 3.5, N_HOUSEHOLDS).round(), 0, 16)
    rooms = np.maximum(1, np.round(household_size / rng.uniform(1.5, 3.2, N_HOUSEHOLDS))).astype(int)
    electricity = rng.binomial(1, 0.83, N_HOUSEHOLDS)
    water_improved = rng.binomial(1, 0.67, N_HOUSEHOLDS)
    sanitation_improved = rng.binomial(1, 0.55, N_HOUSEHOLDS)
    wall_quality = rng.binomial(1, 0.62, N_HOUSEHOLDS)
    floor_quality = rng.binomial(1, 0.58, N_HOUSEHOLDS)
    crop_diversity = np.clip(rng.poisson(2.2, N_HOUSEHOLDS), 0, 7)
    livestock_count = np.clip(rng.negative_binomial(2, 0.38, N_HOUSEHOLDS), 0, 30)
    log_income = (
        7.15 + 0.055 * education + 0.09 * crop_diversity
        + 0.12 * electricity - 0.10 * (head_gender == "Woman")
        + rng.normal(0, 0.42, N_HOUSEHOLDS)
    )
    monthly_income = np.round(np.exp(log_income) / 10) * 10
    food_expense = np.round(monthly_income * rng.uniform(0.30, 0.58, N_HOUSEHOLDS) / 10) * 10
    health_expense = np.round(rng.gamma(2.0, 55.0, N_HOUSEHOLDS) / 5) * 5
    education_expense = np.round(
        household_size * rng.gamma(1.5, 25.0, N_HOUSEHOLDS) / 5
    ) * 5
    agriculture_share = np.clip(rng.beta(2.3, 2.0, N_HOUSEHOLDS), 0, 1).round(3)
    persons_per_room = household_size / rooms
    housing_score = (
        electricity + water_improved + sanitation_improved + wall_quality + floor_quality
        + (persons_per_room <= 3)
    ) / 6
    adequate_housing = (housing_score >= 0.67).astype(int)
    vulnerability = np.clip(
        100 * (1 - (0.42 * housing_score + 0.28 * (education / 16)
                    + 0.30 * np.clip(monthly_income / 6000, 0, 1)))
        + rng.normal(0, 4, N_HOUSEHOLDS), 0, 100
    ).round(1)
    weights = rng.uniform(0.75, 1.35, N_HOUSEHOLDS).round(3)

    households = pd.DataFrame({
        "household_id": household_id,
        "zone": zone,
        "head_gender": head_gender,
        "head_age": head_age,
        "household_size": household_size,
        "rooms": rooms,
        "persons_per_room": persons_per_room.round(2),
        "electricity": electricity,
        "water_improved": water_improved,
        "sanitation_improved": sanitation_improved,
        "wall_quality": wall_quality,
        "floor_quality": floor_quality,
        "head_education_years": education,
        "monthly_income_bob": monthly_income,
        "food_expense_bob": food_expense,
        "health_expense_bob": health_expense,
        "education_expense_bob": education_expense,
        "agriculture_income_share": agriculture_share,
        "crop_diversity": crop_diversity,
        "livestock_count": livestock_count,
        "housing_score": housing_score.round(3),
        "adequate_housing": adequate_housing,
        "vulnerability_index": vulnerability,
        "survey_weight": weights,
    })
    households.loc[rng.choice(N_HOUSEHOLDS, 9, replace=False), "monthly_income_bob"] = np.nan
    households.loc[rng.choice(N_HOUSEHOLDS, 3, replace=False), "head_education_years"] = np.nan
    households.loc[rng.choice(N_HOUSEHOLDS, 2, replace=False), "health_expense_bob"] = np.nan

    member_rows: list[dict] = []
    member_number = 1
    for hid, size, hh_income in zip(household_id, household_size, monthly_income, strict=True):
        for position in range(size):
            relationship = "Head" if position == 0 else rng.choice(
                ["Partner", "Child", "Other relative"], p=[0.20, 0.68, 0.12]
            )
            age = int(head_age[member_number % N_HOUSEHOLDS]) if position == 0 else int(
                np.clip(rng.gamma(2.1, 14), 0, 90)
            )
            gender = rng.choice(["Woman", "Man"])
            literacy_probability = 0.60 + 0.38 / (1 + np.exp(-(age - 12) / 7))
            literacy_probability -= 0.04 * (gender == "Woman") * (age > 45)
            literate = int(rng.random() < np.clip(literacy_probability, 0.25, 0.99))
            employed_probability = 0.05 if age < 15 or age > 75 else 0.48 + 0.10 * (gender == "Man")
            employed = int(rng.random() < employed_probability)
            personal_income = 0 if not employed else max(0, rng.lognormal(7.0, 0.65))
            member_rows.append({
                "member_id": f"SYN-P{member_number:04d}",
                "household_id": hid,
                "relationship": relationship,
                "gender": gender,
                "age": age,
                "literate": literate,
                "employed": employed,
                "personal_income_bob": round(personal_income / 10) * 10,
                "household_income_reference_bob": hh_income,
            })
            member_number += 1
    members = pd.DataFrame(member_rows)
    members.loc[rng.choice(len(members), 7, replace=False), "literate"] = np.nan

    households.to_csv(output_dir / "households_synthetic.csv", index=False)
    members.to_csv(output_dir / "members_synthetic.csv", index=False)
    return households, members


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1] / "data" / "synthetic")

