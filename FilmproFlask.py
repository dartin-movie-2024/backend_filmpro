from flask import Flask, render_template, request, redirect, session, jsonify
from common import constant
import pyodbc
import os
import jwt
from models import db_model
from flask_cors import CORS
import pandas as pd
from common import utils
from flask_ngrok import run_with_ngrok
app = Flask(__name__)
app.secret_key = constant.secret_key_hex
cors = CORS(app)
# status
# Submitted/open/Assigned/Approved

@app.route('/login', methods=['POST'])
def loginAPI():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({"status": 400, "message": "Both username and password are required"})
    conn = db_model.dbConnect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Tbl_User WHERE username = ? and password = ?;", (username,password))
        user = cursor.fetchone()
        print("#", user)

        if user:
            token = jwt.encode({"id": user.id}, constant.SECRET_KEY, algorithm='HS256')
            session['token'] = token
            return jsonify({"status": 200, "message": "Login successful", "token": token})
        else:
            return jsonify({"status": 400, "message": "Invalid Login Details"})
    except pyodbc.Error as e:
        print(f'Error checking credentials: {e}')
    finally:
        conn.close()
    return jsonify({"status": 400, "message": "Invalid Login Details"})

@app.route('/production_list', methods = ['GET'])
def productionDetails():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        conn = db_model.dbConnect()
        query = f"""SELECT * FROM Tbl_Productions AS C 
                   INNER JOIN Master_ProductionTypes MP ON MP.Production_Type_id = C.Production_Type_id
                   WHERE C.Production_id IN (SELECT UP.Production_id FROM Tbl_User_Productions AS UP 
                   WHERE UP.User_id = {username});
                """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            return jsonify({"status": 200, "message": "successfully", 'result': df.to_dict("records")})
        else:
            return jsonify({"status": 204, "message": "No Data Found"})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401

@app.route('/crew_lists', methods=['GET'])
def getCrewAPI():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        conn = db_model.dbConnect()
        # query = f"""SELECT * FROM Tbl_Crew_info AS C
        #         WHERE C.Production_id IN (SELECT UP.Production_id
        #         FROM Tbl_User_Productions AS UP
        #         WHERE UP.User_id = {username}
        #     );
        # """
        # query = f"""SELECT C.*, MP.Designation_Name, MD.Department_Name FROM Tbl_Crew_info AS C
        #             INNER JOIN Master_Designations MP ON MP.Designation_Id = C.Designation_Id
        #             INNER JOIN Master_Departments MD ON MD.Department_Id = C.Department_Id
        #         WHERE C.Production_id IN (SELECT UP.Production_id
        #         FROM Tbl_User_Productions AS UP
        #         WHERE UP.User_id = {username}
        #     );
        query = f"""SELECT CI.Crew_Name, MDP.Department_Name, MSD.SubDepartment_Name, MD.Designation_Name
                    FROM Tbl_Crew_info AS CI
                    INNER JOIN Master_Departments AS MDP ON CI.Department_Id = MDP.Department_Id
                    INNER JOIN Master_Sub_Departmets AS MSD ON CI.SubDepartment_Id = MSD.SubDepartment_Id
                    INNER JOIN Master_Designations AS MD ON CI.Designation_Id = MD.Designation_Id
                    INNER JOIN Tbl_User_Productions AS UP ON CI.Production_id = UP.Production_id
                    WHERE UP.User_Id = {username};
        """
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            return jsonify({"status": 200,"message": "successfully", 'result': df.to_dict("records")})
        else:
            return jsonify({"status": 204, "message": "No Data Found"})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401

@app.route('/get_scene_setup', methods=['GET']) #Done
def getSceneSetupAPI():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        conn = db_model.dbConnect()
        try:
            query = f"""
            SELECT SD.* FROM Tbl_Scene_details AS SD
            JOIN Tbl_User_Productions AS UP ON SD.Production_id = UP.Production_id
            WHERE UP.User_id = {username};
            """
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify({"status": 200, "message": "Records fetched successfully", "result": df.to_dict("records")})
            else:
                return jsonify({"status": 204, "message": "No Data Found"})
        except pyodbc.Error as e:
            print(f'Error fetching tables: {e}')
        finally:
            conn.close()
        return jsonify({"status": 200, "message": "Token verified successfully", "username": username})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401

# @app.route('/update_sence_setup', methods=["POST"])
# def updateSenceSetupAPI():
#     scene_id = request.form.get('scene_id')
#     assigned_to = request.form.get('assigned_to', None)
#     assigned_date = request.form.get('assigned_date', None)
#     record_status = request.form.get('record_status', None)
#     scene_location = request.form.get('scene_location', None)
#     scene_type = request.form.get('scene_type', None)
#     scene_day_condition = request.form.get('scene_day_condition', None)
#     scene_time = request.form.get('scene_time', None)
#     script_pages = request.form.get('script_pages', None)
#     shoot_location = request.form.get('shoot_location', None)
#     shoot_time = request.form.get('shoot_time', None)
#     short_description = request.form.get('short_description', None)
#     status = request.form.get('status', None)
#     update_query_set = ""
#     if not scene_id:
#         return jsonify({"status": 400, "message": "scene_id field are required"})
#     if assigned_to != None:
#         update_query_set += f"Assigned_To={assigned_to},"
#     if assigned_date != None:
#         update_query_set += f"Assigned_date='{pd.to_datetime(assigned_date, format='YYYY-MM-DD HH:MM:SS')},"
#     if record_status != None:
#         update_query_set += f"Record_Status='{record_status}',"
#     if scene_location != None:
#         update_query_set += f"Scene_Location='{scene_location}',"
#     if scene_type != None:
#         update_query_set += f"Scene_Type = '{scene_type}',"
#     if scene_day_condition != None:
#         update_query_set += f"Scene_day_condition = '{scene_day_condition}',"
#     if scene_time != None:
#         update_query_set += f"Scene_time = '{scene_time}',"
#     if script_pages != None:
#         update_query_set += f"Script_Pages = '{script_pages}',"
#     if shoot_location != None:
#         update_query_set += f"Shoot_Location = '{shoot_location}',"
#     if shoot_time != None:
#         update_query_set += f"Shoot_Time = '{shoot_time}',"
#     if short_description != None:
#         update_query_set += f"Short_description = '{short_description}',"
#     if status != None:
#         update_query_set += f"Status = '{status}',"
#     if update_query_set != "":
#         update_query_set = update_query_set[:-1] + update_query_set[-1].replace(",", "")
#         update_query = f'''UPDATE Tbl_Scene_details SET {update_query_set} WHERE Scene_Id={scene_id} '''
#         conn = db_model.dbConnect()
#         cursor = conn.cursor()
#         try:
#             cursor.execute(update_query)
#             conn.commit()
#             return jsonify({'message': 'updated successfully'}), 200
#         except Exception as e:
#             conn.rollback()
#             return jsonify({'error': f'An error occurred while updating the sence: {str(e)}'}), 500
#         finally:
#             conn.close()

@app.route('/update_scene_setup', methods = ['POST'])
def scenesetupAPI():
    Scene_id = request.form.get('Scene_id')
    Scene_type = request.form.get('Scene_type', None)
    Scene_time = request.form.get('Scene_time', None)
    Shoot_time = request.form.get('Shoot_time', None)
    Costume = request.form.get('Costume',None)
    Stunt = request.form.get('Stunt', None)
    Makeup = request.form.get('Makeup', None)
    Art = request.form.get('Art', None)

    update_query_set = ""

    if not Scene_id:
        return jsonify({"status": 400, "message": "Scene_id field are required"})
    if Scene_type != None:
        update_query_set += f"Scene_type={Scene_type},"
    if Scene_time != None:
        update_query_set += f"Scene_type={Scene_time},"
    if Shoot_time != None:
        update_query_set += f"Shoot_time='{Shoot_time}',"
    if Costume != None:
        update_query_set += f"Costume='{Costume}',"
    if Stunt != None:
        update_query_set += f"Status = '{Stunt}',"
    if Makeup != None:
        update_query_set += f"Makeup = {Makeup},"
    if Art != None:
        update_query_set += f"Art = '{Art}',"

    if update_query_set != "":

        update_scene_details = "UPDATE Tbl_Scene_details SET Scene_Type = ?, Scene_time = ?, Shoot_Time = ? " \
                               "WHERE Scene_Id = ?"
        update_scene_costume = "UPDATE Tbl_Scene_Costumes SET Costume = ? WHERE Scene_Id = ?"
        update_scene_makeup = "UPDATE Tbl_Scene_Makeup SET Makeup_Required = ? WHERE Scene_Id = ?"
        update_scene_art = "UPDATE Tbl_Scene_Art SET Art_Required = ? WHERE Scene_Id = ?"
        update_scene_stunt = "UPDATE Tbl_Scene_Stunts SET Stunt_Details = ? WHERE Scene_Id = ?"



        conn = db_model.dbConnect()
        cursor = conn.cursor()

        try:

            cursor.execute(update_scene_details,(Scene_type, Scene_time, Shoot_time, Scene_id ))
            # cursor.execute(update_scene_costume,(Costume, Scene_id ))
            # cursor.execute(update_scene_makeup,(Makeup, Scene_id ))
            # cursor.execute(update_scene_art,(Art, Scene_id ))
            # cursor.execute(update_scene_stunt,(Stunt, Scene_id ))




            conn.commit()
            cursor.close()

            return jsonify({'message': 'updated successfully'}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'An error occurred while updating the character: {str(e)}'}), 500
        finally:
            conn.close()


@app.route('/get_character_setup', methods = ['GET'])
def getCharacterSetup():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        print(username)
        conn = db_model.dbConnect()
        try:
            query = f"""
                SELECT MC.Character_Name, SC.No_Of_Scenes, SC.Scene_Character_Id,
                MC.Character_Type, SC.Shoot_Time_Minutes, SC.Screen_Time_Minutes, SC.Status, SC.Assigned_To,
                SC.Assigned_date, MC.Description
                FROM Master_Character AS MC
                INNER JOIN Tbl_Scene_characters AS SC
                ON MC.character_id = SC.character_id
                INNER JOIN Tbl_User_Productions UP ON SC.character_id = UP.Production_id
                WHERE UP.User_id = {username};
            """
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify({"status": 200, "message": "Records fetched successfully", "result":
                        df.to_dict("records")})
            else:
                return jsonify({"status": 204, "message": "No Data Found"})
        except pyodbc.Error as e:
            print(f'Error fetching tables: {e}')
        finally:
            conn.close()
        return jsonify({"status": 200, "message": "Token verified successfully", "username": username})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401

@app.route('/update_characters_setup', methods = ['POST'])
def updateCharacterSetupAPI():
    scene_character_id = request.form.get('scene_character_id', None)
    Full_name = request.form.get('full_name')
    Height = request.form.get('height')
    Weight = request.form.get('weight')
    Age = request.form.get('age')
    Gender = request.form.get('gender')
    Description = request.form.get('description')
    Hair_color = request.form.get('hair_color')
    Eye_color = request.form.get('eye_color')
    Key_features = request.form.get('key_features')
    Character = request.form.get('character')
    Character_Type = request.form.get('Character_Type')
    No_Of_Scenes = request.form.get('No_Of_Scenes')
    Shoot_Time_Minutes = request.form.get('Shoot_Time_Minutes')
    Screen_Time_Minutes = request.form.get('Screen_Time_Minutes')
    Status = request.form.get('Status')
    Assigned_To = request.form.get('Assigned_To')
    Assigned_date = request.form.get('Assigned_date')


    update_query_set = ""

    if not scene_character_id:
        return jsonify({"status": 400, "message": "scene_character_id field are required"})
    if Full_name != None:
        update_query_set += f"Assigned_To={Full_name},"
    if Height != None:
        update_query_set += f"Character_Name='{Height}',"
    if Weight != None:
        update_query_set += f"Character_Type='{Weight}',"
    if Age != None:
        update_query_set += f"No_Of_Scenes = '{Age}',"
    if Gender != None:
        update_query_set += f"Screen_Time_Minutes = {Gender},"
    if Description != None:
        update_query_set += f"Shoot_Time_Minutes = '{Description}',"
    if Hair_color != None:
        update_query_set += f"Status = '{Hair_color}',"
    if Eye_color != None:
            update_query_set += f"Status = '{Eye_color}',"
    if Key_features != None:
            update_query_set += f"Status = '{Key_features}',"
    if Character != None:
            update_query_set += f"Status = '{Character}',"
    if Character_Type != None:
            update_query_set += f"Status = '{Character_Type}',"

    if No_Of_Scenes != None:
            update_query_set += f"Status = '{No_Of_Scenes}',"

    if Shoot_Time_Minutes != None:
            update_query_set += f"Status = '{Shoot_Time_Minutes}',"
    if Screen_Time_Minutes != None:
            update_query_set += f"Status = '{Screen_Time_Minutes}',"
    if Status != None:
            update_query_set += f"Status = '{Status}',"
    if Assigned_To != None:
            update_query_set += f"Status = '{Assigned_To}',"
    if Assigned_date != None:
            update_query_set += f"Status = '{Assigned_date}',"

    if update_query_set != "":


        update_master_char_table = "UPDATE Master_Character SET Full_name = ?, Height = ?, Weight = ?, \
                       Actual_Age = ?, Gender = ?, Description = ?, Hair_colour = ?, Eye_Colour = ?, Key_Features = ?, " \
                                   "Character_Name = ?, Character_Type = ? WHERE Character_id = ?"
        update_scene_char_table = "UPDATE Tbl_Scene_Characters SET No_Of_Scenes = ?, Shoot_Time_Minutes = ?, " \
                                  "Screen_Time_Minutes = ?, Status = ?, Assigned_To = ?, Assigned_date = ? " \
                                  "WHERE Scene_Character_id = ? and Character_id = ?"

        conn = db_model.dbConnect()
        cursor = conn.cursor()

        try:

            fetch_character_id = "SELECT Character_id FROM Tbl_Scene_Characters WHERE Scene_Character_id = ?"
            cursor.execute(fetch_character_id, (scene_character_id,))
            character_id = cursor.fetchone()[0]
            print("character_id:",character_id)

            cursor.execute(update_master_char_table, (Full_name, Height, Weight, Age, Gender,
                                                      Description, Hair_color, Eye_color, Key_features, Character,
                                                      Character_Type, character_id))
            cursor.execute(update_scene_char_table,
                           (No_Of_Scenes, Shoot_Time_Minutes, Screen_Time_Minutes, Status, Assigned_To,
                            Assigned_date, scene_character_id, character_id))





            conn.commit()
            cursor.close()

            return jsonify({'message': 'updated successfully'}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'An error occurred while updating the character: {str(e)}'}), 500
        finally:
            conn.close()



@app.route('/update_crew', methods=['POST'])
def updateCrewAPI():
    crew_id = request.form.get('crew_id')
    name = request.form.get('crew_name')
    dept_id = request.form.get('dept_id')
    sub_dept_id = request.form.get('sub_dept_id')
    designation_id = request.form.get('designation_id')

    if not crew_id:
        return jsonify({"status": 400, "message": "crew_id field are required"})
    if not name:
        return jsonify({"status": 400, "message": "name field are required"})
    if not dept_id:
        return jsonify({"status": 400, "message": "dept_id field are required"})
    if not sub_dept_id or not designation_id:
        return jsonify({"status": 400, "message": "sub_dept_id field are required"})
    if not designation_id:
        return jsonify({"status": 400, "message": "designation_id field are required"})

    conn = db_model.dbConnect()
    cursor = conn.cursor()
    try:
        query = f"select * from Tbl_Crew_info where Crew_id = {crew_id}"
        df = pd.read_sql(query, conn)
        if len(df) > 0:
            update_query = f'''UPDATE Tbl_Crew_info
                    SET Crew_Name = '{name}', Department_Id = {dept_id}, SubDepartment_Id = {sub_dept_id},
                     Designation_Id = {designation_id} WHERE Crew_id = {crew_id}
                '''
            # print(update_query)
            cursor.execute(update_query)
            conn.commit()
            return jsonify({'message': 'Crew member updated successfully'}), 200
        else:
            return jsonify({'message': 'Crew member Not Found'}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'An error occurred while updating the crew member: {str(e)}'}), 500
    finally:
        conn.close()

##Location setup get
@app.route('/Location_setup', methods = ['GET'])
def get_location_setup():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        print(username)
        conn = db_model.dbConnect()
        try:
            query = f"""
                        SELECT * FROM Master_Locations AS ML
                        INNER JOIN Tbl_Scene_Locations AS SL
                        ON ML.Location_Id= SL.Location_Id
                        INNER JOIN Tbl_User_Productions UP ON SL.Location_Id = UP.Production_id
                        WHERE UP.User_id ={username} ;
                    """
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify({"status": 200, "message": "Records fetched successfully", "result":
                        df.to_dict("records")})
            else:
                return jsonify({"status": 204, "message": "No Data Found"})
        except pyodbc.Error as e:
            print(f'Error fetching tables: {e}')
        finally:
            conn.close()
        return jsonify({"status": 200, "message": "Token verified successfully", "username": username})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401


# @app.route('/update_location_setup', methods = ['POST'])
# def updatelocAPI():
#     location_id = request.form.get('location_id')
#     loc_desc = request.form.get('loc_desc')
#     inst_AD = request.form.get('inst_AD')
#     update_query_set = ""
#
#
#     if not location_id:
#         return jsonify({"status": 400, "message": "location_id field are required"})
#     if not loc_desc:
#         return jsonify({"status": 400, "message": "loc_desc field are required"})
#     if not inst_AD:
#         return jsonify({"status": 400, "message": "inst_AD field are required"})
#
#     if loc_desc != None:
#         update_query_set += f"Assigned_To={loc_desc},"
#     if inst_AD != None:
#         update_query_set += f"Character_Name='{inst_AD}',"
#
#
#     if update_query_set != "":
#         print("location_id:", location_id, "loc_desc:", loc_desc, "inst_AD:", inst_AD)
#         update_scene_locations_table = "UPDATE Tbl_scene_locations SET AD_Instructions = ? WHERE Location_Id = ?"
#         update_Master_Locations_table = "UPDATE Master_Locations SET Location_Description = ? WHERE Location_Id = ?"
#
#         conn = db_model.dbConnect()
#         cursor = conn.cursor()
#
#         try:
#
#
#             cursor.execute(update_scene_locations_table, (inst_AD, location_id))
#             cursor.execute(update_Master_Locations_table, (loc_desc, location_id))
#             conn.commit()
#             cursor.close()
#
#             return jsonify({'message': 'updated successfully'}), 200
#         except Exception as e:
#             conn.rollback()
#             return jsonify({'error': f'An error occurred while updating the location details: {str(e)}'}), 500
#         finally:
#             conn.close()
#
# def get_special_requirements():
#     conn = db_model.dbConnect()
#     cursor = conn.cursor()
#
#     try:
#         cursor.execute("SELECT Special_Requirements FROM Tbl_scene_locations")
#         special_requirements = [row[0] for row in cursor.fetchall()]
#         return special_requirements
#     except Exception as e:
#         # Handle the exception (e.g., log the error)
#         return []
#     finally:
#         conn.close()
# @app.route('/api/special_requirements', methods=['GET'])
# def get_special_requirements_api():
#     special_requirements = get_special_requirements()
#     return jsonify(special_requirements)


# Function to get special requirements from Tbl_scene_locations

@app.route('/update_location_setup', methods=['POST'])
def updatelocAPI():
    location_id = request.form.get('location_id')
    loc_desc = request.form.get('loc_desc')
    inst_AD = request.form.get('inst_AD')
    special_req = request.form.get('special_req')
    update_query_set = ""

    if not location_id:
        return jsonify({"status": 400, "message": "location_id field are required"})
    if not loc_desc:
        return jsonify({"status": 400, "message": "loc_desc field are required"})
    if not inst_AD:
        return jsonify({"status": 400, "message": "inst_AD field are required"})

    if loc_desc is not None:
        update_query_set += f"Assigned_To={loc_desc},"
    if inst_AD is not None:
        update_query_set += f"Character_Name='{inst_AD}',"

    if update_query_set:
        print("location_id:", location_id, "loc_desc:", loc_desc, "inst_AD:", inst_AD)
        update_scene_locations_table = "UPDATE Tbl_scene_locations SET AD_Instructions = ?, Special_requirements = ? WHERE Location_Id = ?"
        update_Master_Locations_table = "UPDATE Master_Locations SET Location_Description = ? WHERE Location_Id = ?"

        conn = db_model.dbConnect()
        cursor = conn.cursor()

        try:
            cursor.execute(update_scene_locations_table, (inst_AD, special_req, location_id))
            cursor.execute(update_Master_Locations_table, (loc_desc, location_id))
            conn.commit()
            cursor.close()

            return jsonify({'message': 'updated successfully'}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'An error occurred while updating the location details: {str(e)}'}), 500
        finally:
            conn.close()



@app.route('/add_production', methods = ['POST'])
def addProduction():
    Production_name = request.form.get('Production_name', None)
    Type_of_production = request.form.get('Type_of_production', None)
    image_upload = request.files.get('image_upload',None)
    print("Production_name:",Production_name,"Type_of_production:",Type_of_production,"image_upload:",image_upload)

    if not Production_name:
        return jsonify({"status": 400, "message": "Production_name field is required"})
    if not Type_of_production:
        return jsonify({"status": 400, "message": "Type_of_production field is required"})
    if not image_upload:
        return jsonify({"status": 400, "message": "image_upload is required"})
    conn = db_model.dbConnect()
    cursor = conn.cursor()
    try:
        query = f"SELECT * from Tbl_Productions"
        df = pd.read_sql(query,conn)
        print(len(df))
        if len(df)>0:

            update_production_name_query = "UPDATE Tbl_Productions SET Production_Name = ?"
            update_production_type_query = "UPDATE Master_ProductionTypes SET Production_Type = ?"

            # Execute the queries with parameters
            cursor.execute(update_production_name_query, (Production_name,))
            cursor.execute(update_production_type_query, (Type_of_production,))
            conn.commit()
            cursor.close()




            return jsonify({'message': 'Production is updated successfully'}), 200
        else:
            return jsonify({"message": 'Production is not updated successfully'}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'An error occurred while updating the production: {str(e)}'}), 500
    finally:
        conn.close()


### Percentage routes
@app.route('/count_scene_setup', methods = ['GET'])
def scene_percent():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        conn = db_model.dbConnect()
        try:
            query = f"""
                SELECT Status, COUNT(*) as count,(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()) AS Percentage
                FROM Tbl_Scene_details GROUP BY Status ;
                """
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify(
                    {"status": 200, "message": "Records fetched successfully", "result": df.to_dict("records")})
            else:
                return jsonify({"status": 204, "message": "No Data Found"})
        except pyodbc.Error as e:
            print(f'Error fetching tables: {e}')
        finally:
            conn.close()
        return jsonify({"status": 200, "message": "Token verified successfully", "username": username})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401

@app.route('/count_character_setup', methods = ['GET'])
def character_percent():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        conn = db_model.dbConnect()
        try:
            query = f"""
                SELECT Status, COUNT(*) as count,(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()) AS Percentage
                FROM Tbl_Scene_characters GROUP BY Status; 

                """
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify(
                    {"status": 200, "message": "Records fetched successfully", "result": df.to_dict("records")})
            else:
                return jsonify({"status": 204, "message": "No Data Found"})
        except pyodbc.Error as e:
            print(f'Error fetching tables: {e}')
        finally:
            conn.close()
        return jsonify({"status": 200, "message": "Token verified successfully", "username": username})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401
#https://dbdocs.io/rkkumar0433/Filmygo
@app.route('/count_location_setup', methods = ['GET'])
def location_percent():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"status": 401, "message": "Token is missing in the Authorization header"}), 401

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=['HS256'])
        username = decoded_token['id']
        conn = db_model.dbConnect()
        try:
            query = f"""
                SELECT Status, COUNT(*) as count,(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()) AS Percentage
                FROM Tbl_Scene_Locations GROUP BY Status; 

                """
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify(
                    {"status": 200, "message": "Records fetched successfully", "result": df.to_dict("records")})
            else:
                return jsonify({"status": 204, "message": "No Data Found"})
        except pyodbc.Error as e:
            print(f'Error fetching tables: {e}')
        finally:
            conn.close()
        return jsonify({"status": 200, "message": "Token verified successfully", "username": username})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401


@app.route('/get_actors', methods = ['GET'])
def GetActors():
    try:
        conn = db_model.dbConnect()
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            user_id = response['id']
            query = f"SELECT * FROM Tbl_Actor_Details"
            df = pd.read_sql(query, conn)
            if len(df)> 0:
                return jsonify({"status": 200, "message": "records fetched successfully!",
                                "result": df.to_dict("records")})
            else:
                return jsonify({"status": 204, "message": "No data Found"})
    except Exception as ex:
        conn.rollback()
        return jsonify({'error': f'An error occurred while fetching the details: {str(ex)}'}), 400

    finally:
        conn.close()



if __name__ == '__main__':
    app.run(port=9000)
    # app.run()
