import os
import pandas as pd


def read_data_file(file_path: str) -> tuple[pd.DataFrame, str]:
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
