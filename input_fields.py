import json


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
