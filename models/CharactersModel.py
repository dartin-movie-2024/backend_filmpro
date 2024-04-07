from models import db_model
import pandas as pd

def getCharacterDetails(Production_id, query=None):
    conn = db_model.dbConnect()
    get_character_query = f"""SELECT MC.Character_id ,Character_Name, MC.Description, SC.No_Of_Scenes, MC.Character_Type, 
                              SC.Shoot_Time_Minutes, SC.Screen_Time_Minutes, SC.Status, SC.Assigned_date,SC.Assigned_To 
                              FROM Master_Character AS MC INNER JOIN Tbl_Scene_characters AS SC
                              ON MC.character_id = SC.character_id AND SC.Production_id = {Production_id}"""
    # INNER JOIN Tbl_User_Productions UP ON SC.Production_id = UP.Production_id
    if query != None:
        get_character_query += f" AND MC.Assigned_To = {query['id']};"
    get_df = pd.read_sql(get_character_query, conn)
    return get_df