"""Data contracts for synthetic public data and future private pipelines."""

from pathlib import Path

import pandas as pd

FORBIDDEN_COLUMNS = {
    "name", "nombre", "surname", "apellido", "address", "direccion",
    "phone", "telefono", "email", "latitude", "longitude", "cedula", "ci",
}


def validate(households: pd.DataFrame, members: pd.DataFrame) -> None:
    all_columns = {column.lower() for column in [*households.columns, *members.columns]}
    exposed = FORBIDDEN_COLUMNS.intersection(all_columns)
    if exposed:
        raise ValueError(f"Direct identifiers are forbidden in public data: {sorted(exposed)}")
    if len(households) != 60 or len(members) != 271:
        raise ValueError("Expected exactly 60 synthetic households and 271 synthetic members")
    if not households["household_id"].is_unique or not members["member_id"].is_unique:
        raise ValueError("Synthetic IDs must be unique")
    if not members["household_id"].isin(households["household_id"]).all():
        raise ValueError("Every member must reference an existing household")
    if not households["adequate_housing"].dropna().isin([0, 1]).all():
        raise ValueError("adequate_housing must be binary")
    if not households["vulnerability_index"].between(0, 100).all():
        raise ValueError("vulnerability_index must remain between 0 and 100")
    if not members["age"].between(0, 100).all():
        raise ValueError("Member ages are outside the accepted range")


def validate_files(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    households = pd.read_csv(data_dir / "households_synthetic.csv")
    members = pd.read_csv(data_dir / "members_synthetic.csv")
    validate(households, members)
    return households, members


if __name__ == "__main__":
    validate_files(Path(__file__).resolve().parents[1] / "data" / "synthetic")
    print("All public-data validation checks passed.")
