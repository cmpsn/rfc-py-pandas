import json
import pyparsing as pp
from constants import MICRO_CALC_PARSER_JOINERS


def parse_microformula_field(src: str):
    """
    Parse the string with input formula and returns
    a nested list of lists with terms and operations.
    """
    pp.ParserElement.enable_packrat()

    base_expr = pp.Word(pp.alphanums, pp.alphanums + MICRO_CALC_PARSER_JOINERS)

    muldiv = pp.oneOf("* /")
    plusminus = pp.oneOf("+ -")

    expr = pp.infix_notation(
        base_expr,
        [
            (muldiv, 2, pp.opAssoc.LEFT),
            (plusminus, 2, pp.opAssoc.LEFT),
        ],
    )

    src = src.replace(" ", "")

    result = expr.parse_string(src).as_list()
    # Pyparsing returns a list wraped in a list -> get the first element 
    return result[0]


def read_db_fields_json(file_path: str):
    """
    Read JSON file created as LIST, ex. ['a', 'b'].

    Parameters:
    ----------
    file_path (str):
        Path to file.

    Returns:
    ----------
    Tuple of:
        - A dictionary with values as lists of dictionaries or as booleans.
        - error (str)
    """
    field_names: dict[str, list[dict[str, str]] | bool] = {}
    error = ""

    try:
        with open(file_path, "r") as file:
            try:
                field_names = json.load(file)
            except Exception:
                error = "A apărut o eroare la citirea câmpurilor din baza de date."
    except FileNotFoundError:
        error = "Denumirile câmpurilor nu au putut fi extrase din baza de date."
    except Exception:
        error = "A apărut o eroare în funcționarea serverului."
    finally:
        return (field_names, error)
