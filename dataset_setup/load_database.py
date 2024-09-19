from glob import glob
import pandas as pd

def load_datasets_from_filesystem():
    file_list = glob("resources/datasets/*/*_all.csv")
    for file in file_list:
        df_ = pd.read_csv(file)
        df_,