from typing import Callable, Optional
import pyparsing as pp
import pandas as pd


class NeighbourOpsError(Exception):
    pass


class ArgumentOpsError(Exception):
    pass


class NotUnaryOpError(Exception):
    pass


# ========= Expression parser


def parse_field(src: str, suplimentary_chars: str):
    """
    Parse the string with input formula and returns
    a nested list of lists with terms and operations.
    """
    pp.ParserElement.enable_packrat()

    base_expr = pp.Word(pp.alphanums, pp.alphanums + suplimentary_chars)

    sign = pp.oneOf("+ -")
    muldiv = pp.oneOf("* /")
    plusminus = pp.oneOf("+ -")

    expr = pp.infix_notation(
        base_expr,
        [
            (sign, 1, pp.opAssoc.RIGHT),
            (muldiv, 2, pp.opAssoc.LEFT),
            (plusminus, 2, pp.opAssoc.LEFT),
        ],
    )

    # Force the entire input string to match the grammar
    # making `parse_all` (second param of func) True

    result = expr.parse_string(src, True).as_list()

    # Pyparsing returns a list wrapped in a list (len=1)
    # when the string has more than 1 terms,
    # otherwise returns a non-wrapped list, also len=1,

    return result


# ========= Values retriever from dataframe

def get_val_from_df(
    term: str,
    term_sep: str,
    df: pd.DataFrame,
    account_col_name: str,
) -> tuple[float | None, str | None]:
    """
    Parse a string label, split in 2 segments:
    - first segment is the column name in df where the value resides,
    - second segment is the string value found in `account_col_name` column
    and get the value from dataframe found where column name meets the row
    where the second segment is found.
    """
    val = None
    error = None

    try:
        term_segments = term.split(term_sep, 1)
        value_col_name = term_segments[0]
        accounting_code = term_segments[1]
    except Exception:
        error = (
            f"Operatorul de legătură `{term_sep}` nu apare în interiorul"
            f" termenului `{term}` introdus la setări."
            f" Operatorul este necesar pentru a identifica în fișierul cu date"
            f" corespondența dintre coloana cu valori numerice și denumirea contului contabil."
        )
        return (val, error)

    # ===== DATAFRAME input

    if not accounting_code in df[account_col_name].tolist():
        error = (
            f"Codul contabil `{accounting_code}`,"
            f" din expresia introdusă la setări, nu există în fișierul încărcat sau are altă denumire."
        )
        return (val, error)

    if not value_col_name in df.columns.values.tolist():
        error = (
            f"Coloana `{value_col_name}`,"
            f" din expresia introdusă la setări, nu există în fișierul încărcat sau are altă denumire."
        )
        return (val, error)

    try:
        val = df.loc[df[account_col_name] == accounting_code, value_col_name].item()

    except Exception:
        error = (
            f"A apărut o eroare la citirea din fișierul cu date a valorii corespunzătoare termenului `{term}`,"
            f" mai exact coloanei `{value_col_name}` și contului contabil `{accounting_code}`."
        )
    else:
        try:
            # Check if the value is missing (i.e, is NaN in pandas, or nan in numpy - which is float)
            if pd.isna(val):
                val = None
                error = (
                    f"Valoarea `{val}` corespunzătoare termenului `{term}`, mai exact coloanei `{value_col_name}`"
                    f" și contului contabil `{accounting_code}` lipsește din fișierul încărcat sau"
                    f" nu poate fi transformată în valoare numerică."
                )
            else:
                val = float(val)
        except Exception:
            error = (
                f"Valoarea `{val}` corespunzătoare termenului `{term}`, mai exact coloanei `{value_col_name}`"
                f" și contului contabil `{accounting_code}` nu poate fi transformată în valoare numerică."
            )

    return (val, error)


# ========== Arithm utility funcs


def add(a: float, b: float):
    return round(a + b, 2)


def subtr(a: float, b: float):
    return round(a - b, 2)


def mult(a: float, b: float):
    return round(a * b, 2)


def div(a: float, b: float):
    return round(a / b, 2)


def unary_minus(x: float):
    if x == 0.0:
        return x
    return -x


def unary_plus(x: float):
    return x


def get_lh_item(ls: list[str | list], item_idx: int) -> str | None | list:
    """
    Returns the left-hand neighbor of an item in a list
    or None, if is the first element.
    """
    if item_idx == 0:
        return None
    return ls[item_idx - 1]


def get_rh_item(ls: list[str | list], item_idx: int) -> str | None | list:
    """
    Returns the right-hand neighbor of an item in a list
    or None, if item is the last element.
    """
    if item_idx == len(ls) - 1:
        return None
    return ls[item_idx + 1]


# ========= Arithm computation of the parser result


def compute_arithm(
    ls: list[str | list],
    label_sep: str,
    operators: dict[str, Callable[..., float]],
    df: pd.DataFrame,
    account_col_name: str,
):
    """
    Traverse the parser result and compute the arithmetic expressions.
    """
    result: Optional[float] = None
    errors: list[str] = []

    ls_len = len(ls)

    if ls_len == 0:
        return (result, errors)

    if ls_len == 1:
        elem = ls[0]

        if isinstance(elem, list):
            result, next_errors = compute_arithm(
                elem, label_sep, operators, df, account_col_name
            )

            if len(next_errors) > 0:
                errors.extend(next_errors)

            return (result, errors)

        else:
            if elem.replace(".", "", 1).isdigit():
                result = float(elem)
            else:
                result, data_error = get_val_from_df(
                    elem, label_sep, df, account_col_name
                )

                if data_error is not None:
                    errors.append(data_error)

            return (result, errors)

    if ls_len == 2:
        # first element in list of len=2 must be a unary operator
        first_elem = ls[0]
        second_elem = ls[1]

        if isinstance(first_elem, list) or first_elem not in UNARY_MAP:
            raise NotUnaryOpError

        else:
            unary_func = UNARY_MAP[first_elem]

            if isinstance(second_elem, list):
                result, next_errors = compute_arithm(
                    second_elem, label_sep, operators, df, account_col_name
                )

                if result is not None:
                    result = unary_func(result)

                if len(next_errors) > 0:
                    errors.extend(next_errors)

            else:
                if second_elem in operators:
                    raise NeighbourOpsError
                elif second_elem.replace(".", "", 1).isdigit():
                    result = unary_func(float(second_elem))
                else:
                    result, data_error = get_val_from_df(
                        second_elem, label_sep, df, account_col_name
                    )

                    if result is not None:
                        result = unary_func(result)

                    if data_error is not None:
                        errors.append(data_error)

            return (result, errors)

    for idx, item in enumerate(ls):
        if isinstance(item, list):
            compute_arithm(item, label_sep, operators, df, account_col_name)

        else:
            if item not in operators:
                continue

            # ==== left hand argument handling
            # accumulation of previous computations as lh

            if result is not None:
                lh = result

            else:
                lh = get_lh_item(ls, idx)

                if isinstance(lh, list):
                    lh, next_errors = compute_arithm(
                        lh, label_sep, operators, df, account_col_name
                    )

                    if len(next_errors) > 0:
                        errors.extend(next_errors)

                else:
                    if lh is None:
                        raise ArgumentOpsError
                    elif lh in operators:
                        raise NeighbourOpsError
                    elif lh.replace(".", "", 1).isdigit():
                        lh = float(lh)
                    else:
                        lh, data_error = get_val_from_df(
                            lh, label_sep, df, account_col_name
                        )

                        if data_error is not None:
                            errors.append(data_error)

            # ==== right hand argument handling

            rh = get_rh_item(ls, idx)

            if isinstance(rh, list):
                rh, next_errors = compute_arithm(
                    rh, label_sep, operators, df, account_col_name
                )

                if len(next_errors) > 0:
                    errors.extend(next_errors)

            else:
                if rh is None:
                    raise ArgumentOpsError
                elif rh in operators:
                    raise NeighbourOpsError
                elif rh.replace(".", "", 1).isdigit():
                    rh = float(rh)
                else:
                    rh, data_error = get_val_from_df(
                        rh, label_sep, df, account_col_name
                    )

                    if data_error is not None:
                        errors.append(data_error)

            # call the function associated with the current arithmetic operator/item

            if lh is not None and rh is not None:
                arithm_operation = operators[item]
                result = arithm_operation(lh, rh)

    return (result, errors)


# ========= Micro-calc integrator

def compute_micro(
    df: pd.DataFrame,
    account_col_name: str,
    micro_formula: str,
    label_fields_sep: str,
    sumplimentary_chars: str,
):
    """
    Returns a tuple with the result of computation as float or None,
    and an error as None or string.
    """
    result = None
    error = None

    accepted_suplim_chars = f"{label_fields_sep}{sumplimentary_chars}"

    try:
        operations_nested = parse_field(micro_formula, accepted_suplim_chars)
    except pp.ParseException as pe:
        error = (
            f"Expresia introdusă în câmpul micro-calculator de la setări nu este conformă cu regulile"
            f" de construire a formulelor de calcul."
            f" Verificați dacă formula introdusă respectă regulile precizate."
            f" Detalii returnate de sistem: `{pe}`"
        )
        return (result, error)
    except Exception:
        error = (
            "Expresia introdusă în câmpul micro-calculator de la setări nu este conformă cu regulile"
            " de construire a formulelor de calcul."
            " Verificați dacă formula introdusă respectă regulile precizate."
        )
        return (result, error)

    # Check if the json field for col name where to find accounting_codes exists in data frame
    if account_col_name not in df.columns.values.tolist():
        error = (
            f"Coloana `{account_col_name}`,"
            f" necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire."
        )
        return (result, error)

    # Do the computations
    try:
        result, computation_errors = compute_arithm(
            operations_nested, label_fields_sep, OPERATORS_MAP, df, account_col_name
        )

        if len(computation_errors) > 0:
            error = "\n".join(computation_errors)

    except RecursionError:
        error = (
            "Nivelul de adâncime al formulei introduse este prea mare,"
            " a depășit memoria alocată de server. Formula introdusă trebuie să aibă"
            " un număr rezonabil de paranteze, operatori aritmetici și termeni sau valori."
        )
    except ZeroDivisionError:
        error = (
            "În formula introdusă în câmpul de setări apare explicit o împărțire la zero SAU"
            " numitorul folosit într-o operație de împărțire din formula introdusă la setări"
            " are valoarea zero în celula din fișierul cu date ce corespunde numitorului indicat în formulă."
        )
    except NeighbourOpsError:
        error = (
            "Formula introdusă în câmpul de setări conține doi operatori aritmetici"
            " situați unul lângă altul. Un operator trebuie să aibă atât la stânga cât și la dreapta lui"
            " fie un indicator către o celulă din fișierul cu date, fie o valoare numerică."
        )
    except ArgumentOpsError:
        error = (
            "Poziția unuia din operatorii aritmetici din formula introdusă la setări este incorectă."
            " Un operator trebuie să aibă atât la stânga cât și la dreapta lui"
            " fie un indicator către o celulă din fișierul cu date, fie o valoare numerică."
        )
    except NotUnaryOpError:
        error = (
            "Operatorii unari pot fi doar semnele `+` și `-`, sistemul a detectat alt tip de expresie"
            " în poziție de operator unar."
        )
    except Exception:
        error = (
            "A aparut o eroare în procesarea calculelor conform expresiei introduse."
            " în câmpul micro-calculator de la setări."
        )

    return (result, error)


# ======= Operations maps

OPERATORS_MAP = {
    "+": add,
    "-": subtr,
    "*": mult,
    "/": div,
}

UNARY_MAP = {"+": unary_plus, "-": unary_minus}
