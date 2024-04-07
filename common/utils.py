import jwt
from common import constant
from flask import request, jsonify
import pandas as pd
from models import db_model
import pyodbc
def handle_options():
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'Preflight check successful'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

# Decorator for your POST routes that includes the OPTIONS handling function

def getAuthorizationDetails(request):
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return False, 401, "Token is missing in the Authorization header"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return False, 401, "Invalid token format"
        token = parts[1]
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        return True, decoded_token, "success"
    except jwt.ExpiredSignatureError:
        return True, 401, "Token has expired"
    except jwt.InvalidTokenError:
        return True, 401, "Invalid token"


def handle_NATType(df):
    for column in df.columns:
        if df[column].dtypes == 'datetime64[ns]':
            df[column] = df[column].fillna("")
            # print(df[column])
            df[column] = pd.to_datetime(df[column], dayfirst=True).fillna("NA")
            df.loc[df[column] == "NA", column] = ""
    return df

def get_table_data(table_name):
    conn = db_model.dbConnect()
    try:
        query = f"""
            SELECT Status, COUNT(*) as count, (COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()) AS Percentage
            FROM {table_name} GROUP BY Status;
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            return {"status": 200, "message": f"count from {table_name} fetched successfully","result": df.to_dict("records")}
        else:
            return {"status": 204, "message": "No Data Found"}
    except pyodbc.Error as e:
        print(f'Error fetching tables: {e}')
    finally:
        conn.close()