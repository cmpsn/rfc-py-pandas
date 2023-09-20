import os
import sys
import json
import computation as cmp


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

    rfc_fields = cmp.compute_fields(field_names_path, data_file_path)

    jsn_out_name, jsn_out_extension = os.path.splitext(field_names_path)
    jsn_out_path = "".join([jsn_out_name, "_output", jsn_out_extension])

    with open(jsn_out_path, "w", encoding="utf-8") as j_file:
        json.dump(obj=rfc_fields, fp=j_file, skipkeys=True, ensure_ascii=False)
