from typing import Callable
import formulas

SPECIAL_RFC = "special_rfc"
SPECIAL_RFC_SPLIT_SEP = ":"
ID = "id"
KEY = "key"
ACC_COL_NAME = "account_col_name"
ACC_CODE = "account_code"
VAL_COL_NAME = "value_col_name"
FIELDS_SPLIT_SEP = ","
SINGLE_CELL = "single_cell"
AMRSC = "sum_many_rows_same_col"
SSRTC = "subtract_same_row_two_cols"

OPERATIONS: dict[str, dict[str, Callable]] = {
    SINGLE_CELL: {"func": formulas.get_single_value},
    AMRSC: {"func": formulas.sum_many_rows_same_col},
    SSRTC: {"func": formulas.subtract_two_single_values},
}
