import os
import sys
import pandas as pd
import json
import constants as cnst


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
        - A list of strings (list)
        - error (str)
    """
    field_names = {}
    error = ""

    try:
        with open(file_path, "r") as file:
            try:
                field_names: dict[str, list[dict] | bool] = json.load(file)
            except Exception:
                error = "A apărut o eroare la citirea câmpurilor din baza de date."
    except FileNotFoundError:
        error = "Denumirile câmpurilor nu au putut fi extrase din baza de date."
    except Exception:
        error = "A apărut o eroare în funcționarea serverului."
    finally:
        return (field_names, error)


def read_data_file(file_path: str) -> tuple:
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

    if file_extension == ".xls":
        try:
            df = pd.read_excel(file_path, engine="xlrd")
        except Exception:
            error = (
                "Fișierul încărcat nu poate fi citit."
                " Exportați încă o dată datele din baza de date originală"
                " și încercați din nou să îl încărcați în sistem."
            )

    elif file_extension == ".xlsx":
        try:
            df = pd.read_excel(file_path, engine="openpyxl")
        except Exception:
            error = (
                "Fișierul încărcat nu poate fi citit."
                " Exportați încă o dată datele din baza de date originală"
                " și încercați din nou să îl încărcați în sistem."
            )

    elif file_extension == ".csv":
        try:
            df = pd.read_csv(file_path, sep=None, engine="python")
        except Exception:
            error = (
                "Fișierul încărcat nu poate fi citit."
                " Exportați încă o dată datele din baza de date originală"
                " și încercați din nou să îl încărcați în sistem."
            )

    else:
        error = (
            "Fișierul încărcat nu este într-un format compatibil."
            " Pentru a putea fi procesat, fișierul trebuie să aibă una din extensiile:"
            " .csv, .xls sau .xlsx."
        )
    return (df, error)


def filter_special_jsn_vals(dictio: dict[str, str], separator: str, after_sep: bool):
    """
    Take a dictionary, iterate over its keys, check if the coresp.
    value is a string, then check if the input separator is in the string,
    in which case the string is splitted by the separator and
    the second item (index 1) is filtered and returned as the new value
    of the respective key.

    Parameters:
    ----------
    dictio (dict):
        A dictionary to iterate through.

    separator (str):
        A string separator used to split the string values of the dictionary.

    after_sep (bool):
        A boolean to specify if the filtered and returned slice of the string
        is that AFTER the first encounter of the separator
        (if False, the string slice before the separator is filtered and returned.)

    Returns:
    ----------
    A dictionary with changed string values, in case the separator
    is found in the string value.
    """
    for key in dictio.keys():
        if isinstance(dictio[key], str) and (separator in dictio[key]):
            if after_sep:
                dictio[key] = dictio[key].split(separator)[1]
                # dictio.update({key: val.split(sep)[1]})
            else:
                dictio[key] = dictio[key].split(separator)[0]

    return dictio


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

    jsn_inp_obj, jsn_inp_reading_error = read_db_fields_json(field_names_path)

    # Check for errors of reading the input json
    if len(jsn_inp_reading_error) > 0:
        errors.append({"global_error": jsn_inp_reading_error})
        return errors

    # Check if the input json object is not a dictionary and if it's empty
    if (not isinstance(jsn_inp_obj, dict)) or (len(jsn_inp_obj) == 0):
        errors.append(
            {
                "global_error": "Pentru această firmă nu au fost create anterior câmpurile necesare pentru a introduce valori în RFC."
            }
        )
        return errors

    # ===== Read the input data file as pd.df =====

    df, df_inp_reading_error = read_data_file(data_file_path)

    # Check for errors of reading the data file (.csv, .xls, .xlsx)
    if len(df_inp_reading_error) > 0:
        errors.append({"global_error": df_inp_reading_error})
        return errors

    # Check if Data Frame is a table with min. 1 row an 1 col (size > 2 is a must)
    if df.size < 2:
        errors.append(
            {
                "global_error": "Datele din fișierul încărcat nu au minim un rând și minim o coloană."
            }
        )
        return errors

    # Tuple of input JSON objects keys that must be present at runtime - from cnstants
    fields_required_keys = (
        cnst.ID,
        cnst.ACC_COL_NAME,
        cnst.ACC_CODE,
        cnst.VAL_COL_NAME,
    )

    # =========== LUCRU ===============

    final_results = []
    jsn_inp_obj_keys = jsn_inp_obj.keys()

    for item in jsn_inp_obj_keys:
        if item not in cnst.OPERATIONS.keys():
            continue

        objs_list = jsn_inp_obj[item]

        # Check if is non empty list
        if (not isinstance(objs_list, list)) or (len(objs_list) == 0):
            errors.append(
                {
                    "global_error": "Unele informații despre câmpurile care implică identificarea "
                    "celulelor necesare pentru calcule lipsesc din baza de date."
                }
            )
            return errors

        # If it's a SPECIAL RFC case, for each object in the list filter the values after a split separator for special cases:
        # if special case, keep the string slice AFTER the separator, otherwise keep the slice before the separator.
        if cnst.SPECIAL_RFC in jsn_inp_obj_keys:
            objs_list = [
                filter_special_jsn_vals(
                    dictio=obj,
                    separator=cnst.SPECIAL_RFC_SPLIT_SEP,
                    after_sep=True if jsn_inp_obj[cnst.SPECIAL_RFC] else False,
                )
                for obj in objs_list
                if isinstance(obj, dict)
            ]

        # For each Field Object from the input json file call the appropriate computing func
        # collect results in a Generator
        call_specific_func = cnst.OPERATIONS[item]

        # ============== AICI de inserat procesarea pentru micro calculator ===============
        # if item === cnst.MICRO_CALC: ... else: procesarea tip Multiple Fields (curentă)

        processing_collection = (
            {
                "id": obj[cnst.ID],
                "results": call_specific_func(
                    df,
                    obj[cnst.ACC_COL_NAME],
                    obj[cnst.ACC_CODE],
                    obj[cnst.VAL_COL_NAME],
                    cnst.MULTIPLE_FIELDS_SPLIT_SEP,
                ),
            }
            for obj in objs_list
            if isinstance(obj, dict)
            and all(item in obj.keys() for item in fields_required_keys)
        )

        # Create a list with unzipped results
        results = [
            {"id": item["id"], "value": item["results"][0], "error": item["results"][1]}
            for item in processing_collection
        ]

        final_results.extend(results)

    return final_results


if __name__ == "__main__":
    try:
        field_names_path = sys.argv[1]
        data_file_path = sys.argv[2]
    except Exception:
        print(
            (
                "Ai uitat sa adaugi in linia de comanda"
                " fisierul JSON ce contine numele campurilor/indicatorilor ca argv[1]"
                " si fisierul csv/xls/xlsx cu datele de analizat ca argv[2]."
            )
        )

        sys.exit(1)

    rfc_fields = compute_fields(field_names_path, data_file_path)

    jsn_out_name, jsn_out_extension = os.path.splitext(field_names_path)
    jsn_out_path = "".join([jsn_out_name, "_output", jsn_out_extension])

    with open(jsn_out_path, "w", encoding="utf-8") as j_file:
        json.dump(obj=rfc_fields, fp=j_file, skipkeys=True, ensure_ascii=False)
