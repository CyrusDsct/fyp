import pandas as pd


def coerce_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = series.astype(str).str.strip()
    cleaned = cleaned.replace({"": None, "nan": None, "none": None, "null": None, "n/a": None}, regex=False)

    # Handle common numeric-like formatting found in CSV exports.
    cleaned = cleaned.str.replace(",", "", regex=False)
    cleaned = cleaned.str.replace("%", "", regex=False)
    cleaned = cleaned.str.replace("$", "", regex=False)
    cleaned = cleaned.str.replace("HK$", "", regex=False)

    return pd.to_numeric(cleaned, errors="coerce")
