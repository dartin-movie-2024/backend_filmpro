from models import db_model
import pandas as pd

def getLocationsDetails(Production_id, query=None):
    conn = db_model.dbConnect()
    get_loc_query = f""" SELECT ML.Location_Id, ML.Location_Name, SL.No_Of_Scenes, ML.Location_Type, 
                        SL.Shoot_Time_Minutes, SL.Screen_Time_Minutes, SL.Status, SL.Assigned_date, 
                        SL.Assigned_To FROM Master_Locations AS ML
                        INNER JOIN Tbl_Scene_Locations AS SL
                        ON ML.Location_Id= SL.Location_Id AND SL.Production_id = {Production_id}
                       """
    # INNER JOIN Tbl_User_Productions UP ON SL.Location_Id = UP.Production_id
    if query != None:
        get_loc_query += f" WHERE ML.Assigned_To = {query['id']};"
    get_df = pd.read_sql(get_loc_query, conn)
    return get_df