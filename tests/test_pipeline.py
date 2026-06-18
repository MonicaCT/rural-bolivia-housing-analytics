from pathlib import Path

import pandas as pd

from src.analyze import fit_housing_model
from src.generate_synthetic import generate
from src.validate import FORBIDDEN_COLUMNS, validate


def test_generator_is_reproducible(tmp_path: Path):
    first_hh, first_members = generate(tmp_path / "first")
    second_hh, second_members = generate(tmp_path / "second")
    pd.testing.assert_frame_equal(first_hh, second_hh)
    pd.testing.assert_frame_equal(first_members, second_members)


def test_public_data_contract(tmp_path: Path):
    households, members = generate(tmp_path)
    validate(households, members)
    columns = {column.lower() for column in [*households.columns, *members.columns]}
    assert not FORBIDDEN_COLUMNS.intersection(columns)
    assert households.household_id.str.startswith("SYN-").all()
    assert members.member_id.str.startswith("SYN-").all()


def test_model_outputs_finite_estimates(tmp_path: Path):
    households, _ = generate(tmp_path)
    model, _, predictors = fit_housing_model(households)
    assert model.converged
    assert model.params[predictors].notna().all()

