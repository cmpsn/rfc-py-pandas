import os
import sys
import pandas as pd
import json
import constants as const
import formulas


def read_db_fields_json(file_path):
    """
    Read JSON file created as LIST, ex. ['a', 'b'].

    Parameters:
    ----------
    file_path (str): Path to file.

    Returns:
    ----------
    Tuple of:
        - A list of strings (list)
        - error (str)
    """
    field_names = {}
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


def read_data_file(file_path):
    """
    Read .csv, .xls, .xlsx file and transform it to DataFrame.

    Parameters:
    ----------
    file_path (str): 
        Path to file. Ex.: "https://example.com/folder/filename"; 
        when in the same folder as the py script: "filename".

    Returns:
    ----------
    A tuple:
        - df (pd.DataFrame) 
        - error (str)
    """
    _, file_extension = os.path.splitext(file_path)
    df = pd.DataFrame()
    error = ""

    if file_extension == ".csv":
        try:
            df = pd.read_csv(file_path, sep=None, engine='python')
        except Exception:
            # to do: code to handle exception - send error to client as json ...
            error = ("Fișierul încărcat nu poate fi citit."
                     " Exportați încă o dată datele din baza de date originală"
                     " și încercați din nou să îl încărcați în sistem.")

    elif file_extension == ".xlsx":
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception:
            error = ("Fișierul încărcat nu poate fi citit."
                     " Exportați încă o dată datele din baza de date originală"
                     " și încercați din nou să îl încărcați în sistem.")

    elif file_extension == ".xls":
        try:
            df = pd.read_excel(file_path, engine='xlrd')
        except Exception:
            error = ("Fișierul încărcat nu poate fi citit."
                     " Exportați încă o dată datele din baza de date originală"
                     " și încercați din nou să îl încărcați în sistem.")

    else:
        error = ("Fișierul încărcat nu este într-un format compatibil."
                 " Pentru a putea fi procesat, fișierul trebuie să aibă una din extensiile:"
                 " .csv, .xls sau .xlsx.")
    return (df, error)


def compute_fields(field_names_path: str, data_file_path: str):
    """
    Main execution of the script.

    Parameters:
    ----------
    field_names_path (str):
        Path to JSON file containing the names 
        of the indicators to compute | Can be sys.argv[1]

    data_file_path (str):
        Path to data file (extensions: .csv, .xls, xlsx)

    Returns:
    ----------
    A JSON format from a python dictionary that includes all indicators and all errors.
    """
    # Initialize an object to accumulate errors
    errors = []

    # ===== Read the input json coresp. to id_firm =====

    jsn_inp_obj, jsn_inp_reading_error = read_db_fields_json(
        field_names_path)

    # Check for errors of reading the input json
    if len(jsn_inp_reading_error) > 0:
        errors.append({"global_error": jsn_inp_reading_error})
        return errors

    # Check if the input json object is not a dictionary and if it's empty
    if (not isinstance(jsn_inp_obj, dict)) or (len(jsn_inp_obj) == 0):
        errors.append(
            {"global_error": "Pentru această firmă nu au fost create anterior câmpurile necesare pentru a introduce valori în RFC."})
        return errors

    jsn_inp_obj_keys = jsn_inp_obj.keys()

    # ===== Read the input data file as pd.df =====

    df, df_inp_reading_error = read_data_file(data_file_path)

    # Check for errors of reading the data file (.csv, .xls, .xlsx)
    if len(df_inp_reading_error) > 0:
        errors.append({"global_error": df_inp_reading_error})
        return errors

    # Check if Data Frame is a table with min. 1 row an 1 col (size > 2 is a must)
    if df.size < 2:
        errors.append(
            {"global_error": "Datele din fișierul încărcat nu au minim un rând și minim o coloană."})
        return errors

    # Tuple of input JSON objects keys that must be present at runtime - from constants
    fields_required_keys = (const.ID, const.ACC_COL_NAME,
                            const.ACC_CODE, const.VAL_COL_NAME)

    # 1. ======= START copying SINGLE CELL values operations ===========

    single_cell_results = []

    if const.SINGLE_CELL in jsn_inp_obj_keys:
        single_cell_objs_list = jsn_inp_obj[const.SINGLE_CELL]

        # Check if is non empty list
        if (not isinstance(single_cell_objs_list, list)) or (len(single_cell_objs_list) == 0):
            errors.append(
                {"global_error": "Unele informații despre câmpurile care implică identificarea celulelor unice lipsesc din baza de date."})
            return errors

        # For each Field Object from the input json file call the appropriate computing func
        # single values is of type <generator> because of "()" instead of "[]"
        single_cell_collection = ({"id": obj[const.ID], "results": formulas.get_single_value(
            df=df, 
            account_col_name=obj[const.ACC_COL_NAME],
            accounting_code=obj[const.ACC_CODE],
            value_col_name=obj[const.VAL_COL_NAME])} for obj in single_cell_objs_list if isinstance(obj, dict) and
            all(item in obj.keys() for item in fields_required_keys))

        # Create a list with unzipped results for single_cell_collection
        single_cell_results = [{"id": item["id"], "value": item["results"][0],
                                "error": item["results"][1]} for item in single_cell_collection]

    # 2. ======= START sum_many_rows_same_col operations ===========

    add_many_rows_same_col_results = []

    if const.AMRSC in jsn_inp_obj_keys:
        add_many_rows_same_col_objs_list = jsn_inp_obj[const.AMRSC]

        # Check if is non empty list
        if (not isinstance(add_many_rows_same_col_objs_list, list)) or (len(add_many_rows_same_col_objs_list) == 0):
            errors.append(
                {"global_error": "Unele informații despre câmpurile care implică operația aritmetică de adunare lipsesc din baza de date."})
            return errors

        # For each Field Object from the input json file call the appropriate computing func
        add_many_rows_same_col_collection = ({"id": obj[const.ID], "results": formulas.sum_many_rows_same_col(
            df=df,
            account_col_name=obj[const.ACC_COL_NAME],
            accounting_codes=obj[const.ACC_CODE],
            value_col_name=obj[const.VAL_COL_NAME])} for obj in add_many_rows_same_col_objs_list if isinstance(obj, dict) and
            all(item in obj.keys() for item in fields_required_keys))

        # Create a list with unzipped results for sum_many_rows_same_col
        add_many_rows_same_col_results = [{"id": item["id"], "value": item["results"][0],
                                           "error": item["results"][1]} for item in add_many_rows_same_col_collection]

    # 3. ======= START subtract_same_row_two_cols operations ===========

    subtract_same_row_two_cols_results = []

    if const.SSRTC in jsn_inp_obj_keys:
        subtract_same_row_two_cols_objs_list = jsn_inp_obj[const.SSRTC]

        # Check if is non empty list
        if (not isinstance(subtract_same_row_two_cols_objs_list, list)) or (len(subtract_same_row_two_cols_objs_list) == 0):
            errors.append(
                {"global_error": "Unele informații despre câmpurile care implică operația aritmetică de scădere" +
                 " lipsesc din baza de date."})
            return errors

        # For each Field Object from the input json file call the appropriate computing func
        subtract_same_row_two_cols_collection = ({"id": obj[const.ID], "results": formulas.subtract_two_single_values(
            df=df,
            account_col_name=obj[const.ACC_COL_NAME],
            accounting_codes=obj[const.ACC_CODE],
            value_col_names=obj[const.VAL_COL_NAME])} for obj in subtract_same_row_two_cols_objs_list if isinstance(obj, dict) and
            all(item in obj.keys() for item in fields_required_keys))

        # Create a list with unzipped results for subtract_same_row_two_cols
        subtract_same_row_two_cols_results = [{"id": item["id"], "value": item["results"][0],
                                               "error": item["results"][1]} for item in subtract_same_row_two_cols_collection]

    # ===== Merge results =====
    final_results = single_cell_results + \
        add_many_rows_same_col_results + subtract_same_row_two_cols_results + errors

    return final_results


if __name__ == "__main__":
    try:
        field_names_path = sys.argv[1]
        data_file_path = sys.argv[2]
    except Exception:
        print(("Ai uitat sa adaugi in linia de comanda"
               " fisierul JSON ce contine numele campurilor/indicatorilor ca argv[1]"
               " si fisierul csv/xls/xlsx cu datele de analizat ca argv[2]."))

        sys.exit(1)

    rfc_fields = compute_fields(field_names_path, data_file_path)

    jsn_out_name, jsn_out_extension = os.path.splitext(field_names_path)
    jsn_out_path = ''.join([jsn_out_name, '_output', jsn_out_extension])

    with open(jsn_out_path, "w", encoding='utf-8') as j_file:
        json.dump(obj=rfc_fields, fp=j_file, skipkeys=True, ensure_ascii=False)
