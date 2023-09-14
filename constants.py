from typing import Callable
import microformula
import formulas

SPECIAL_RFC_SPLIT_SEP = ":"
MICRO_CALC_FIELDS_SPLIT_SEP = "@"
MULTIPLE_FIELDS_SPLIT_SEP = ","

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
OPERATIONS: dict[str, Callable] = {
    MICRO_CALC: microformula.compute_micro,
    SINGLE_CELL: formulas.get_single_value,
    AMRSC: formulas.sum_many_rows_same_col,
    SSRTC: formulas.subtract_two_single_values,
}
