import os
import re
import sys

abs_path = os.path.dirname(__file__)
# /Python-Project'
main_cwd = re.sub('crawl_data.*','crawl_data',abs_path)
os.chdir(main_cwd)
sys.path.append(main_cwd)

import json
import pandas as pd
import requests
from w88_bti_market.selenium_w88 import get_ct_tokens
from functions.sql_lite import SQLiteDB

df = SQLiteDB("./w88_bti_market/w88.db").read_df("SELECT * FROM matches")
df1 = SQLiteDB("./w88_bti_market/w88.db").read_df("SELECT * FROM markets")
df2 = SQLiteDB("./w88_bti_market/w88.db").read_df("SELECT * FROM outcomes")

df.to_csv("./csv_data/matches.csv", index=False)
df1.to_csv("./csv_data/markets.csv", index=False)
df2.to_csv("./csv_data/outcomes.csv", index=False)