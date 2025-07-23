import pandas as pd
from pathlib import Path

# this point to the Excel file
excel_path = Path(__file__).parent / "../data/online_retail_ii.xlsx"
xl = pd.ExcelFile(excel_path)


for sheet in xl.sheet_names:
    df = xl.parse(sheet)
    # this creates a CSV name like online_retail_2009_2010.csv
    csv_name = sheet.lower().replace(" ", "_").replace("-", "_") + ".csv"
    out_path = Path(__file__).parent / "../data" / csv_name
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")