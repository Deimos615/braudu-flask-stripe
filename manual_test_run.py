from braudu_flagged import *
import pandas as pd
import os
import time

if __name__ == '__main__':
    # You must initialize logging, otherwise you'll not see debug output.
    # Read data from Excel file
    # import data locally
    data = pd.read_excel(os.path.join("files", "input_data.xlsx"))

    start = time.time()
    # process input data
    output_data = process_data(data, "Head of Development",2)

    print(f"Time taken: {time.time() - start}")
    # Create output Excel file
    output_df = pd.DataFrame(output_data)
    # output_df = output_df.sort_values(by=output_df.columns[0], key=lambda x: x.str.lower())
    output_df.to_excel(os.path.join("files", "output_data.xlsx"), index=False)

