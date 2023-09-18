from typing import Callable, Optional
import pandas as pd
import microcalc_parser as mcp


class NeighbourOpsError(Exception):
    pass


class ArgumentOpsError(Exception):
    pass


# ========== Utility funcs


def add(a: float, b: float):
    return a + b


def subtr(a: float, b: float):
    return a - b


def mult(a: float, b: float):
    return a * b


def div(a: float, b: float):
    return a / b


# ======= !!!!! LUCRU ============


def get_lh_item(ls: list[str | list], item_idx: int) -> str | None | list:
    if item_idx == 0:
        return None
    return ls[item_idx - 1]


def get_rh_item(ls: list[str | list], item_idx: int) -> str | None | list:
    if item_idx == len(ls) - 1:
        return None
    return ls[item_idx + 1]


def compute_arithm(
    ls: list[str | list], label_sep: str, operators: dict[str, Callable[..., float]]
):
    total: Optional[float] = None

    if len(ls) == 1:
        if not str(ls[0]).isalnum():
            raise ArgumentOpsError
        return ls[0]

    for idx, item in enumerate(ls):
        if isinstance(item, list):
            compute_arithm(item, label_sep, operators)

        else:
            if item not in operators:
                continue

            # ==== left hand argument handling
            # for accumulation of results check the total

            if total is not None:
                lh = total
            
            else:
                lh = get_lh_item(ls, idx)

                if isinstance(lh, list):
                    lh = compute_arithm(lh, label_sep, operators)
                else:
                    if lh is None:
                        # ========= TO DO - Implementation of unary signs (-, maybe +)
                        # in case the user inserts -+ before numbers or cells indicators
                        # then lh of the current item ca be None (ex. [['-', '12'], ....])
                        raise ArgumentOpsError
                    elif lh in operators:
                        raise NeighbourOpsError
                    elif lh.replace(".", "", 1).isdigit():
                        lh = float(lh)
                    else:
                        # call a function get_val_from_df() to get the value of lh from pandas df, then:
                        # return value_from_df_cell
                        lh = get_val_from_df(lh, label_sep)


            # ==== right hand argument handling

            rh = get_rh_item(ls, idx)

            if isinstance(rh, list):
                rh = compute_arithm(rh, label_sep, operators)
            else:
                if rh is None:
                    raise ArgumentOpsError
                elif rh in operators:
                    raise NeighbourOpsError
                elif rh.replace(".", "", 1).isdigit():
                    rh = float(rh)
                else:
                    # call a function get_val_from_df() to get the value of lh from pandas df, then:
                    # return value_from_df_cell
                    rh = get_val_from_df(rh, label_sep)

            # call the function associated with the current operator/item
            # ========= TO DO -> delete`float()`, now it's just for testing
            arithm_func = operators[item]
            total = arithm_func(lh, rh)

    return total


# ===== TO DO -> NOT implemented yet =========

def get_val_from_df(label: str, label_sep: str):
    # ======= AICI e nevoie de pd.Dataframe =======
    pass


def compute_micro(
    df: pd.DataFrame,
    account_col_name: str,
    micro_formula: str,
    label_fields_sep: str,
    sumplimentary_chars: str,
):
    result = None
    error = None
    
    accepted_suplim_chars = f"{label_fields_sep}{sumplimentary_chars}"

    nested_ops = mcp.parse_field(micro_formula, accepted_suplim_chars)
    # Unzip result - Pyparsing result is wrapped in a list, so result len is 1
    formula = list(*nested_ops)


    # ========== TO DO - IN LUCRU ========
    try:
        result = compute_arithm(formula, label_fields_sep, OPERATORS_MAP)
    except:
        # AICI lista de clase de erori de mai jos
        # RecursionError, ZeroDivisionError .....
        pass

    # linie de cod sunt temporara, ca sa nu dea eroare
    result = 1.0


    return (result, error)


# ======= TO DO - Execution inside compute_micro() ==========

OPERATORS_MAP = {
    "+": add,
    "-": subtr,
    "*": mult,
    "/": div,
}


# res = None
# error = ""

# try:
#     res = compute_arithm(ls, operations)
# except RecursionError:
#     error = (
#         "Nivelul de adâncime al formulei introduse este prea mare,"
#         " a depășit memoria alocată de server. Formula introdusă trebuie să aibă"
#         " un număr rezonabil de paranteze, operatori aritmetici și termeni sau valori."
#     )
# except ZeroDivisionError:
#     error = (
#         "În formula introdusă în câmpul de setări apare explicit o împărțire la zero SAU"
#         " numitorul folosit într-o operație de împărțire din formula introdusă la setări"
#         " are valoarea zero în celula din fișierul cu date ce corespunde numitorului indicat în formulă."
#     )
# except NeighbourOpsError:
#     error = (
#         "Formula introdusă în câmpul de setări conține doi operatori aritmetici"
#         " situați unul lângă altul. Un operator trebuie să aibă atât la stânga cât și la dreapta lui"
#         " fie un indicator către o celulă din fișierul cu date, fie o valoare numerică."
#     )
# except ArgumentOpsError:
#     error = (
#         "Poziția unuia din operatorii aritmetici din formula introdusă la setări este incorectă."
#         " Un operator trebuie să aibă atât la stânga cât și la dreapta lui"
#         " fie un indicator către o celulă din fișierul cu date, fie o valoare numerică."
#     )
# except Exception:
#     error = "A aparut o eroare de funcționare a sistemului."

# if res:
#     print(res)
# if error:
#     print(error)
