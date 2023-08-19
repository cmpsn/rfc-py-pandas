import pandas as pd


def get_single_value(df: pd.DataFrame,
                     account_col_name: str,
                     accounting_code: str,
                     value_col_name: str,
                     fields_sep: str):
    """
    Select a Single value from DF using:
    - 1 column to find a single value that identifies the target row
    - 1 target column where to search for the value coresp. to target row.

    Parameters:
    ----------
    df (pd.DataFrame): 
        DataFrame to use.
    account_col_name (str): Name of the column containing the accounting codes.
    accounting_code (str): 
        Value of the accounting code coresp. to the row where 
        the value to return exists.
    value_col_name (str): 
        Name of the column containing the value to return.

    Returns: 
    ----------
    A tuple with 2 items:
        - result of calculation
        - error (str)
    """
    result = None
    error = None

    params = (account_col_name, accounting_code, value_col_name)

    #  ===== JSON Input

    # Check if func params coming from JSON are strings.
    if not all(isinstance(item, str) for item in params) or not all(len(item) > 0 for item in params):
        error = (f'Unele din valorile `{account_col_name}`, `{accounting_code}`, `{value_col_name}`'
                 f' definite pentru acest câmp nu sunt înregistrate în baza de date în format string sau sunt înregistrate ca nule.')
        return (result, error)

    # Strip the potential whitespace from the string values in JSON fields
    account_col_name, accounting_code, value_col_name = (
        item.strip() for item in params)

    # ===== DATAFRAME input

    # Check if the json fields values exist in data frame
    # if account_col_name in df.columns.values.tolist():

    if not account_col_name in df.columns.values.tolist():
        error = (f'Coloana `{account_col_name}`,'
                 f' necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire.')
        return (result, error)

    if not accounting_code in df[account_col_name].tolist():
        result = 0.0
        return (result, error)

    if not value_col_name in df.columns.values.tolist():
        error = (f'Coloana `{value_col_name}`,'
                 f' necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire.')
        return (result, error)

    try:
        result = df.loc[df[account_col_name] ==
                        accounting_code, value_col_name].item()

        # Check if the value in the cell is missing (is NaN in pandas) - using pandas method pd.isna()
        if pd.isna(result):
            result = None
            error = (f'Valoarea corespunzătoare rândului cu codul contabil `{accounting_code}`'
                     f' și coloanei `{value_col_name}` lipsește din fișierul încărcat')

        # Check if value in the cell is a number (BUT if it's needed to be a string, then condition pd.isna(result) is enough).
        if not isinstance(result, (float, int)):
            result = None
            error = (f'Valoarea corespunzătoare rândului cu codul contabil `{accounting_code}`'
                     f' și coloanei `{value_col_name}` lipsește din fișierul încărcat sau nu este în format numeric.')

    except Exception:
        error = (f'Valoarea corespunzătoare rândului cu codul contabil `{accounting_code}`'
                 f' și coloanei `{value_col_name}` din fișierul încărcat are un format care nu poate fi procesat.')

    return (result, error)


def sum_many_rows_same_col(df: pd.DataFrame,
                           account_col_name: str,
                           accounting_codes: str,
                           value_col_name: str,
                           fields_sep: str):
    """
    Compute a value using:
    - 1 column to find multiple values to identify many target rows
    - 1 target column where to search for the values coresp. to the target rows
    - compute the sum of the found values

    Parameters:
    ----------
    df (pd.DataFrame): DataFrame to use.
    account_col_name (str): Name of the column containing the accounting codes.
    accounting_codes (str): An enumeration (separated by comma) of accounting codes (as a long string)
        coresponding to the rows where the values to sum up exists.
    value_col_name (str): Name of the column containing the values to sum up.
    fields_sep (str): A string delimiter that separates between names of input fields.

    Returns: 
    ----------
    A tuple with 2 items:
        - result of calculation
        - error (str)
    """
    result = None
    error = None

    params = (account_col_name, accounting_codes, value_col_name)

    #  ===== JSON Input

    # Check if func params coming from JSON are strings.
    if not all(isinstance(item, str) for item in params) or not all(len(item) > 0 for item in params):
        error = (f'Unele din valorile `{account_col_name}`, `{accounting_codes}`, `{value_col_name}`'
                 f' definite pentru acest câmp nu sunt înregistrate în baza de date în format string sau sunt înregistrate ca nule.')
        return (result, error)

    # Strip the potential whitespace from the string values in JSON fields
    account_col_name, value_col_name = (
        item.strip() for item in (account_col_name, value_col_name))

    accounting_codes_list = [item.strip()
                             for item in accounting_codes.split(fields_sep)]

    if len(accounting_codes_list) < 2:
        error = "Pentru acest câmp a cărui valoare e calculată prin operația aritmetică de adunare" + \
            " trebuie precizate MINIM 2 conturi contabile corespunzând valorilor care trebuie adunate."
        return (result, error)

    # ===== DATAFRAME input

    # Check if the json fields values exist in data frame
    if not account_col_name in df.columns.values.tolist():
        error = (f'Coloana `{account_col_name}`,'
                 f' necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire.')
        return (result, error)

    # filter only the accounting codes that exists in excel (to get sum 0 if fields from database are not found in excel)
    accounting_codes_list = [
        item for item in accounting_codes_list if item in df[account_col_name].tolist()]

    if len(accounting_codes_list) == 0:
        result = 0.0
        return (result, error)

    if not value_col_name in df.columns.values.tolist():
        error = (f'Coloana `{value_col_name}`,'
                 f' necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire.')
        return (result, error)

    # Get the values needed for calculation as pd.Series
    # and check if they are of type float or int to cumpute the SUM
    try:
        partial_values_series = df.loc[df[account_col_name].isin(
            accounting_codes_list), value_col_name]

        # Check if any of the values from the required cells is missing (is NaN in pandas)
        # using pandas methods pd.Series.isnull() and pd.Series.any()
        if partial_values_series.isnull().values.any():
            error = (f'Unele din valorile corespunzătoare rândurilor cu codurile contabile `{accounting_codes_list}`'
                     f' și coloanei `{value_col_name}` lipsesc din fișierul încărcat.')
            return (result, error)

        # Check if all values from the required cells are of type `float`` or `int`, otherwise the sum() cannot be computed.
        # using pure python functions all() and isinstance()
        if not all(isinstance(item, (float, int)) for item in partial_values_series.tolist()):
            error = (f'Unele din valorile corespunzătoare rândurilor cu codurile contabile `{accounting_codes_list}`'
                     f' și coloanei `{value_col_name}` din fișierul încărcat nu sunt în format numeric.')
            return (result, error)

    except Exception:
        error = (f'Unele din valorile corespunzătoare rândurilor cu codurile contabile `{accounting_codes_list}`'
                 f' și coloanei `{value_col_name}` din fișierul încărcat nu pot fi procesate.')
        return (result, error)

    try:
        result = partial_values_series.sum()

        # Check if the result is missing (is NaN in pandas)
        # using pandas method pd.isna()
        if pd.isna(result):
            result = None
            error = (f'Operația de adunare a valorilor corespunzătoare rândurilor cu codurile contabile `{accounting_codes_list}`'
                     f' și coloanei `{value_col_name}` din fișierul încărcat nu a produs un rezultat numeric.')
    except Exception:
        error = (f'Unele din valorile corespunzătoare rândurilor cu codurile contabile `{accounting_codes_list}`'
                 f' și coloanei `{value_col_name}` din fișierul încărcat nu pot fi procesate.')

    return (result, error)


def subtract_two_single_values(df: pd.DataFrame,
                               account_col_name: str,
                               accounting_codes: str,
                               value_col_names: str,
                               fields_sep: str):
    """
    Compute a value using:
    - 1 column to find multiple values to identify many target rows
    - 1 target column where to search for the values coresp. to the target rows
    - subtract the two identified values

    Parameters:
    ----------
    df (pd.DataFrame): DataFrame to use.
    account_col_name (str): Name of the column containing the accounting codes. 
    accounting_codes (str): An enumeration (separated by comma) of accounting codes (as a long string)
        coresponding to the rows where the values to sum up exists.
    value_col_names (str): An enumeration (separated by comma) of the names of columns (as a long string)
        containing the values to subtract (first value_col_name - second value_col_name).
    fields_sep (str): A string delimiter that separates between names of input fields.

    Returns:
    ----------
    A tuple with 2 items:
        - result of calculation (float or int)
        - error (str)
    """
    result = None
    error = None

    params = (account_col_name, accounting_codes, value_col_names)

    #  ===== JSON Input =====

    # Check if func params coming from JSON are strings.
    if not all(isinstance(item, str) for item in params) or not all(len(item) > 0 for item in params):
        error = (f'Unele din valorile `{account_col_name}`, `{accounting_codes}`, `{value_col_names}`'
                 f' precizate pentru acest câmp nu sunt înregistrate în baza de date în format string sau sunt înregistrate ca nule.')
        return (result, error)

    # Split and Strip the potential whitespace from the string values in JSON fields
    account_col_name = account_col_name.strip()
    accounting_codes_list = [item.strip()
                             for item in accounting_codes.split(fields_sep)]
    value_col_names_list = [item.strip()
                            for item in value_col_names.split(fields_sep)]

    if len(accounting_codes_list) > 2:
        error = "Pentru acest câmp a cărui valoare e calculată prin operația aritmetică de scădere" + \
            " trebuie precizate MAXIM 2 conturi contabile corespunzând valorilor cu care se face operația de scădere."
        return (result, error)

    if len(value_col_names_list) > 2:
        error = "Pentru acest câmp a cărui valoare e calculată prin operația aritmetică de scădere" + \
            " trebuie precizate MAXIM 2 nume de coloane în care se găsesc cei 2 termeni ai scăderii."
        return (result, error)

    if (len(accounting_codes_list) + len(value_col_names_list)) < 3:
        error = "Pentru acest câmp a cărui valoare e calculată prin operația aritmetică de scădere a 2 termeni" + \
            " trebuie precizate fie 2 conturi contabile și 1 nume de coloană, fie 1 cont contabil și 2 nume de coloane"
        return (result, error)

    # Get the subtraction elements
    accounting_code_first = accounting_codes_list[0]
    accounting_code_second = accounting_codes_list[1] if len(
        accounting_codes_list) > 1 else accounting_codes_list[0]
    value_col_name_first = value_col_names_list[0]
    value_col_name_second = value_col_names_list[1] if len(
        value_col_names_list) > 1 else value_col_names_list[0]

    # ===== DATAFRAME input =====

    columns_values_list = df.columns.values.tolist()

    # Check if the json fields values exist in data frame
    if not account_col_name in columns_values_list:
        error = (f'Coloana `{account_col_name}`,'
                 f' necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire.')
        return (result, error)

    term_first = 0.0
    term_second = 0.0
    account_col_name_series = df[account_col_name]

    try:
        if accounting_code_first in account_col_name_series.tolist():
            # Check if the json fields values exist in framedata
            if value_col_name_first in columns_values_list:

                term_first = df.loc[account_col_name_series.isin(
                    [accounting_code_first]), value_col_name_first].item()

                # Check if the value in cell is missing (is NaN in pandas) - using pandas method pd.isna()
                if pd.isna(pd.Series([term_first])).any():
                    error = (f'Valoarea corespunzătoare rândului cu codul contabil `{accounting_code_first}` și coloanei `{value_col_name_first}`,'
                             f' lipsește din fișierul încărcat.')
                    return (result, error)

                # Check if value in cell is a number in order to do math operations on it.
                if not isinstance(term_first, (float, int)):
                    error = (f'Valoarea corespunzătoare rândului cu codul contabil `{accounting_code_first}` și coloanei `{value_col_name_first}`,'
                             f' din fișierul încărcat nu este în format numeric.')
                    return (result, error)

            else:
                error = (f'Coloana `{value_col_name_first}` corespunzătoare rândului cu contul contabil `{accounting_code_first}`,'
                         f' necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire.')
                return (result, error)

        if accounting_code_second in account_col_name_series.tolist():
            # Check if the json fields values exist in framedata
            if value_col_name_second in columns_values_list:

                term_second = df.loc[account_col_name_series.isin(
                    [accounting_code_second]), value_col_name_second].item()

                # Check if the value in cell is missing (is NaN in pandas) - using pandas method pd.isna()
                if pd.isna(pd.Series([term_second])).any():
                    error = (f'Valoarea corespunzătoare rândului cu codul contabil `{accounting_code_second}` și coloanei `{value_col_name_second}`,'
                             f' lipsește din fișierul încărcat.')
                    return (result, error)

                # Check if value in cell is a number in order to do math operations on it.
                if not isinstance(term_second, (float, int)):
                    error = (f'Valoarea corespunzătoare rândului cu codul contabil `{accounting_code_second}` și coloanei `{value_col_name_second}`,'
                             f' din fișierul încărcat nu este în format numeric.')
                    return (result, error)

            else:
                error = (f'Coloana `{value_col_name_second}` corespunzătoare rândului cu contul contabil `{accounting_code_second}`,'
                         f' necesară pentru calcule, nu există în fișierul încărcat sau are altă denumire.')
                return (result, error)

    except Exception:
        error = (f'Unele din valorile corespunzătoare rândurilor cu codurile contabile `{accounting_code_first}`, `{accounting_code_second}`'
                 f' și coloanelor `{value_col_name_first}`, `{value_col_name_second}` din fișierul încărcat nu pot fi procesate.')
        return (result, error)

    try:
        result = round(term_first - term_second, ndigits=2)
        if pd.isna(result):
            result = None
            error = (f'Unele din valorile corespunzătoare rândului cu codul contabil `{accounting_code_first}`'
                     f' și coloanei `{value_col_name_first}` sau rândului cu codul contabil `{accounting_code_second}`'
                     f' și coloanei `{value_col_name_second}` lipsesc din fișierul încărcat sau nu sunt în format numeric.')
    except Exception:
        error = (f'Unele din valorile corespunzătoare rândului cu codul contabil `{accounting_code_first}`'
                 f' și coloanei `{value_col_name_first}` sau rândului cu codul contabil `{accounting_code_second}`'
                 f' și coloanei `{value_col_name_second}` din fișierul încărcat nu sunt în format numeric.')

    return (result, error)
