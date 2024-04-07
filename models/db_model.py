import pandas as pd
import pyodbc
from common import constant


def dbConnect():
    return pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={constant.server};UID={constant.username};PWD={constant.password};DATABASE={constant.database_name}'
    )

