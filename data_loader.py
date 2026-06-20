"""
data_loader.py
---------------
Loads the meals dataset from the Excel workbook using pandas and exposes
small helper functions for pulling the dynamic Diet/Lifestyle option lists
that populate the Home page form.
"""

from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "Halal_Meals_Plan.xlsx"

REQUIRED_COLUMNS = [
    "Meal Type",
    "Name",
    "Diet",
    "Lifestyle",
    "Ingredients",
    "Calories",
    "Macros",
]


def load_meals_dataframe() -> pd.DataFrame:
    """
    Read the 'Meals' sheet of the workbook into a pandas DataFrame and do
    light cleanup (strip whitespace on text columns) so downstream string
    matching (Diet/Lifestyle filters) is reliable.
    """
    df = pd.read_excel(DATA_PATH, sheet_name="Meals")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Meals dataset is missing required column(s): {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    text_columns = ["Meal Type", "Name", "Diet", "Lifestyle", "Ingredients", "Calories", "Macros"]
    for col in text_columns:
        df[col] = df[col].astype(str).str.strip()

    return df


def get_unique_diets(df: pd.DataFrame) -> list[str]:
    """Dynamically extract the unique Diet values for the Home page form."""
    return sorted(df["Diet"].dropna().unique().tolist())


def get_unique_lifestyles(df: pd.DataFrame) -> list[str]:
    """Dynamically extract the unique Lifestyle values for the Home page form."""
    return sorted(df["Lifestyle"].dropna().unique().tolist())
