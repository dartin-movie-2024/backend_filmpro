from models import db_model
import pandas as pd

def getSceneSetupDetails(query=None):
    conn = db_model.dbConnect()
    if query != None:
        get_query = f"""SELECT SD.Scene_Id, SD.Scene_Location, SD.Shoot_Location, SD.Shoot_Time, SD.Scene_time, 
                        SD.Status, SD.Assigned_To, SD.Assigned_date FROM Tbl_Scene_details AS SD
                        JOIN Tbl_User_Productions AS UP ON SD.Production_id = UP.Production_id
                        WHERE UP.User_id = {query['id']};"""
    else:
        # get_query = 'SELECT * FROM Tbl_Scene_details'
        get_query = f"""SELECT SD.Scene_Id, SD.Scene_Location, SD.Shoot_Location, SD.Shoot_Time, SD.Scene_time, 
                        SD.Status, SD.Assigned_To, SD.Assigned_date FROM Tbl_Scene_details AS SD
                        JOIN Tbl_User_Productions AS UP ON SD.Production_id = UP.Production_id;"""
    get_df = pd.read_sql(get_query, conn)
    return get_df

