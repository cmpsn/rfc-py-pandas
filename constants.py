from typing import Callable
import microcalc
import multiformulas

SPECIAL_RFC_SPLIT_SEP = ":"
MICRO_CALC_FIELDS_SPLIT_SEP = "@"
MICRO_CALC_SUPLIM_CHARS = "._"
MULTI_FORMULAS_FIELDS_SPLIT_SEP = ","

# first level API keys
SPECIAL_RFC = "special_rfc"
MICRO_CALC = "micro_calculator"
SINGLE_CELL = "single_cell"
AMRSC = "sum_many_rows_same_col"
SSRTC = "subtract_same_row_two_cols"

# API objects keys
ID = "id"
KEY = "key"
MICRO_FORMULA = "micro_formula"
ACC_COL_NAME = "account_col_name"
ACC_CODE = "account_code"
VAL_COL_NAME = "value_col_name"

# API keys mapping to computing functions
PROCEDURES_MAP: dict[str, Callable[..., tuple[float | None, str | None]]] = {
    MICRO_CALC: microcalc.compute_micro,
    SINGLE_CELL: multiformulas.get_single_value,
    AMRSC: multiformulas.sum_many_rows_same_col,
    SSRTC: multiformulas.subtract_two_single_values, # type: ignore
}
