from models import db_model
import pandas as pd
def getCrewDetails(query=None):
    conn = db_model.dbConnect()

    crew_query = f"""
                    SELECT CI.Crew_Id,CI.Crew_Name, MDP.Department_Name, MSD.SubDepartment_Name, MD.Designation_Name
                    FROM Tbl_Crew_info AS CI
                    INNER JOIN Master_Departments AS MDP ON CI.Department_Id = MDP.Department_Id
                    INNER JOIN Master_Sub_Departments AS MSD ON CI.SubDepartment_Id = MSD.SubDepartment_Id
                    INNER JOIN Master_Designations AS MD ON CI.Designation_Id = MD.Designation_Id
                    INNER JOIN Tbl_User_Productions AS UP ON CI.Production_id = UP.Production_id
                    """
    if crew_query != None:
        crew_query += f"WHERE UP.User_Id = {query['id']};"

    crew_df = pd.read_sql(crew_query, conn)
    return crew_df


