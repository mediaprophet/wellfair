from __future__ import annotations

from typing import Dict

import pandas as pd

from src.utils import data_type_from_filename


def find_df_by_keyword(normalized: dict, keyword: str) -> pd.DataFrame | None:
    for fname, df in normalized.get("dataframes", {}).items():
        if keyword in fname.lower():
            return df
    return None


def find_df_by_datatype(normalized: dict, datatype: str) -> pd.DataFrame | None:
    for fname, df in normalized.get("dataframes", {}).items():
        if data_type_from_filename(fname) == datatype:
            return df
    return None
