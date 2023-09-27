import constants as cnst
import inputs as inp


def filter_special_jsn_vals(dictio: dict[str, str], separator: str, after_sep: bool):
    """
    Take a dictionary, iterate over its keys, check if the coresp.
    value is a string, then check if the input separator is in that string,
    in which case split the string using the separator. If after_sep is True,
    return the second element, else return the first element.

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
    Takes paths to:
    1) a json file with objects and their field names
    2) a xls/csv file with data
    and returns a list of objects with computation results and error
    for each input object.

    Parameters:
    ----------
    field_names_path (str):
        Path to JSON file containing the names
        of the indicators to compute | Can be sys.argv[1]

    data_file_path (str):
        Path to data file (extensions: .csv, .xls, xlsx)

    Returns:
    ----------
    A list of dictionaries with each field id, value and computation error.
    """
    # Initialize an object to accumulate errors
    errors = []

    # ===== Read the input json coresp. to id_firm =====

    jsn_inp_obj, jsn_inp_reading_error = inp.read_db_fields_json(field_names_path)

    # Check for errors of reading the input json
    if len(jsn_inp_reading_error) > 0:
        errors.append({"global_error": jsn_inp_reading_error})
        return errors

    # Check if the input json object is a dictionary and if it's empty
    if (not isinstance(jsn_inp_obj, dict)) or (len(jsn_inp_obj) < 1):
        errors.append(
            {
                "global_error": (
                    "Pentru această firmă nu au fost create anterior câmpurile necesare pentru a introduce valori în RFC."
                    " Dacă nu acesta este cazul, atunci a apărut o eroare privind formatul datelor pe server"
                    " (json format not a dictionary)"
                )
            }
        )
        return errors

    # ===== Read the input data file as pandas dataFrame =====

    df, df_inp_reading_error = inp.read_data_file(data_file_path)

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

    # =========== ACTUAL WORK ===============

    final_results = []
    jsn_inp_obj_keys = jsn_inp_obj.keys()

    for item in jsn_inp_obj_keys:
        if item not in cnst.PROCEDURES_MAP.keys():
            continue

        objs_list = jsn_inp_obj[item]

        # Check if is non empty list
        if (not isinstance(objs_list, list)) or (len(objs_list) == 0):
            errors.append(
                {
                    "global_error": (
                        "Setările câmpurilor necesare pentru calcule lipsesc din baza de date"
                        " sau sunt returnate în format incorect de către server."
                    )
                }
            )
            return errors

        # If it's a SPECIAL RFC case, for each object in the list filter the values after a split separator for special cases:
        # if special case, keep the string slice AFTER the separator, otherwise keep the slice before the separator.
        if cnst.SPECIAL_RFC in jsn_inp_obj_keys:
            try:
                objs_list = [
                    filter_special_jsn_vals(
                        dictio=obj,
                        separator=cnst.SPECIAL_RFC_SPLIT_SEP,
                        after_sep=True if jsn_inp_obj[cnst.SPECIAL_RFC] else False,
                    )
                    for obj in objs_list
                ]
            except Exception:
                errors.append(
                    {
                        "global_error": (
                            "Serverul returnează anumite obiecte cu setările de câmpuri"
                            " care nu sunt în formatul necesar pentru calcule (dict format error in json)."
                        )
                    }
                )
                return errors

        # For each Field Object from the input json file call the appropriate computing func
        # collect results in a Generator

        specific_func = cnst.PROCEDURES_MAP[item]

        try:
            if item in [cnst.MICRO_CALC, cnst.MICRO_CALC_FLEXI]:
                processing_collection = (
                    {
                        "id": obj[cnst.ID],
                        "results": specific_func(
                            df,
                            obj[cnst.ACC_COL_NAME].replace(" ", ""),
                            obj[cnst.MICRO_FORMULA],  # do not replace whitespace
                            cnst.MICRO_CALC_FIELDS_SPLIT_SEP,
                            cnst.MICRO_CALC_SUPLIM_CHARS,
                            strict_data_query=False if item == cnst.MICRO_CALC_FLEXI else True,
                        ),
                    }
                    for obj in objs_list
                )
            else:
                processing_collection = (
                    {
                        "id": obj[cnst.ID],
                        "results": specific_func(
                            df,
                            obj[cnst.ACC_COL_NAME].replace(" ", ""),
                            obj[cnst.ACC_CODE].replace(" ", ""),
                            obj[cnst.VAL_COL_NAME].replace(" ", ""),
                            cnst.MULTI_FORMULAS_FIELDS_SPLIT_SEP,
                        ),
                    }
                    for obj in objs_list
                )

            results = [
                {
                    "id": item["id"],
                    "value": item["results"][0],
                    "error": item["results"][1],
                }
                for item in processing_collection
            ]

            final_results.extend(results)

        except KeyError:
            errors.append(
                {
                    "global_error": (
                        "Serverul returnează anumite obiecte cu setările de câmpuri din care"
                        " lipsesc chei obligatorii pentru efectuare de calcule (dict key errors in json)."
                    )
                }
            )
            return errors
        except (AttributeError, TypeError):
            errors.append(
                {
                    "global_error": (
                        "Serverul returnează anumite obiecte în care setările unor câmpuri"
                        " nu sunt în formatul necesar pentru calcule (type error in json, string expected)."
                    )
                }
            )
            return errors
        except Exception:
            errors.append(
                {
                    "global_error": (
                        "Serverul returnează anumite obiecte cu setările de câmpuri"
                        " care nu sunt sub în formatul necesar pentru calcule (dict format error in json)."
                    )
                }
            )
            return errors

    return final_results
