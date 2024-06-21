from flask import Flask, render_template, request, redirect, session, jsonify
from common import constant
import pyodbc
import os
import jwt
from models import db_model
import pandas as pd
from common import utils
from models import CrewModel as CM
from models import SceneModels as SM
from models import CharactersModel as CRM
from models import LocationModel as LM
from datetime import datetime
from flask_cors import CORS
import base64
import config
from werkzeug.utils import secure_filename
from extraction import main_func

app = Flask(__name__)
# test=CORS(app)
# CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Authorization"]}})
# app = Flask(__name__)
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:3001", "allow_headers": "Authorization"}})
# cors = CORS(app, resources={
#     r"/api/*": {
#         "origins": "http://localhost:3001",
#         "allow_headers": ["Authorization", "Content-Type"],
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
#     }
# })

# test.init_app(app,origins= "http://127.0.0.1:3001",allow_headers=["Content-Type", "Authorization"])
app.secret_key = constant.secret_key_hex


def post_with_options(route):
    def decorator(func):
        @app.route(route, methods=["POST", "OPTIONS"])
        def wrapper(*args, **kwargs):
            response = utils.handle_options()
            if response:
                return response
            return func(*args, **kwargs)

        return wrapper

    return decorator


@app.route("/api/login", methods=["POST", "OPTIONS"])
def loginAPI():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight check successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    Email_Id = request.form.get("username")
    password = request.form.get("password")
    if not Email_Id or not password:
        return jsonify(
            {"status": 400, "message": "Both username and password are required"}
        )
    conn = db_model.dbConnect()
    try:

        get_query = f"SELECT * FROM Tbl_App_Users WHERE Email_Id = '{Email_Id}' and Password = '{password}';"
        user_df = pd.read_sql(get_query, conn)
        if len(user_df) > 0:
            user_id = user_df["User_id"].iloc[0]
            login_type = user_df["Designation"].iloc[0]
            data = {"id": str(user_id), "Production_id": None, "login_type": login_type}
            user_production_query = (
                f"select * from Tbl_User_Productions where User_id = {user_id}"
            )
            user_production_df = pd.read_sql(user_production_query, conn)
            if len(user_production_df) > 0:
                data["Production_id"] = str(user_production_df["Production_id"].iloc[0])
            token = jwt.encode(data, constant.SECRET_KEY, algorithm="HS256")
            return jsonify(
                {
                    "status": 200,
                    "message": "Login successful",
                    "token": token,
                    "login_type": login_type,
                }
            )
        else:
            return jsonify({"status": 400, "message": "Invalid Login Details"})
    except pyodbc.Error as e:
        print(f"Error checking credentials: {e}")
    finally:
        conn.close()
    return jsonify({"status": 400, "message": "Invalid Login Details"})


@app.route("/api/production_list", methods=["GET"])
def productionDetails():
    try:
        conn = db_model.dbConnect()
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            user_id = response["id"]
            query = f"""SELECT * FROM Tbl_Productions AS C
                    INNER JOIN Master_ProductionTypes AS MP ON MP.Production_Type_id = C.Production_Type_id
                    INNER JOIN Tbl_User_Productions AS UP ON UP.Production_id = C.Production_id
                    WHERE UP.User_id = {user_id};
                    """
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": df.to_dict(orient="records"),
                    }
                )
            else:
                return jsonify({"status": 400, "message": "No Data Found"}), 400
    except Exception as ex:
        conn.rollback()
        return (
            jsonify(
                {"error": f"An error occurred while updating the sence: {str(ex)}"}
            ),
            400,
        )
    finally:
        conn.close()


@app.route("/api/get_crew", methods=["GET"])
def getCrewDetails():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            crew_df = CM.getCrewDetails(response)
            if len(crew_df) > 0:
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": crew_df.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )
    except Exception as ex:
        return (
            jsonify(
                {"error": f"An error occurred while updating the sence: {str(ex)}"}
            ),
            400,
        )


@app.route("/api/upload_crew", methods=["POST", "OPTIONS"])
def uploadCrewDetails():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            update_query_set = ""
            Crew_id = request.form.get("Crew_id", None)
            Crew_Name = request.form.get("Crew_Name", None)
            Department_Id = request.form.get("Department_Id", None)
            SubDepartment_Id = request.form.get("SubDepartment_Id", None)
            Designation_Id = request.form.get("Designation_Id", None)
            if not Crew_id:
                return jsonify(
                    {"status": 400, "message": "Scene_id field are required"}
                )
            if Crew_Name != None:
                update_query_set += f"Crew_Name='{Crew_Name}',"
            if Department_Id != None:
                update_query_set += f" Department_Id={Department_Id},"
            if SubDepartment_Id != None:
                update_query_set += f"SubDepartment_Id={SubDepartment_Id},"
            if Designation_Id != None:
                update_query_set += f"Designation_Id={Designation_Id},"
            datetime_now = pd.to_datetime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            if update_query_set != "":
                update_query_set += f"Last_Updated_on = '{datetime_now}', Last_Updated_By = {response['id']}"
                update_query_set = update_query_set[:-1] + update_query_set[-1].replace(
                    ",", ""
                )
                update_query = f"UPDATE Tbl_Crew_info SET {update_query_set} WHERE Crew_id = {Crew_id}"
                conn = db_model.dbConnect()
                cursor = conn.cursor()
                try:
                    cursor.execute(update_query)
                    conn.commit()
                    return (
                        jsonify({"status": 200, "message": "updated successfully"}),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 500,
                                "message": f"An error occurred while updating the sence: {str(e)}",
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()
            else:
                return jsonify({"status": 400, "message": f"invalid input fileds"}), 400
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/get_scene_setup", methods=["GET"])  # Done
def getSceneDetails():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            sd_df = SM.getSceneSetupDetails()

            if len(sd_df) > 0:
                sd_df = utils.handle_NATType(sd_df)
                grouped_count = sd_df.groupby("Status").size().reset_index(name="count")
                total_count = grouped_count["count"].sum()
                grouped_count["percentage"] = (
                    grouped_count["count"] / total_count
                ) * 100
                group_list = grouped_count.to_dict(orient="records")
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": sd_df.to_dict("records"),
                        "count_list": group_list,
                    }
                )
            else:
                return jsonify(
                    {
                        "status": 400,
                        "message": "No Data Found",
                        "result": [],
                        "count_list": [],
                    }
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


# Count stuff
@app.route("/api/count", methods=["GET"])
def scene_percent():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return (
            jsonify(
                {
                    "status": 401,
                    "message": "Token is missing in the Authorization header",
                }
            ),
            401,
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return jsonify({"status": 401, "message": "Invalid token format"}), 401
    token = parts[1]
    try:
        decoded_token = jwt.decode(token, constant.SECRET_KEY, algorithms=["HS256"])
        username = decoded_token["id"]
        conn = db_model.dbConnect()
        try:
            scene_data = utils.get_table_data("Tbl_Scene_details")
            character_data = utils.get_table_data("Tbl_Scene_characters")
            location_data = utils.get_table_data("Tbl_Scene_Locations")

            response = {
                "scene_setup": scene_data,
                "character_setup": character_data,
                "location_setup": location_data,
            }

            return jsonify(response)
        except pyodbc.Error as e:
            print(f"Error fetching tables: {e}")
        finally:
            conn.close()
        return jsonify(
            {
                "status": 200,
                "message": "Token verified successfully",
                "username": username,
            }
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"status": 401, "message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"status": 401, "message": "Invalid token"}), 401


@app.route("/api/get_character_setup", methods=["POST", "OPTIONS"])
def getCharacterDetails():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Production_id = request.form.get("Production_id", None)
            if Production_id == None:
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": "pelase enter the Production_id filed",
                        }
                    ),
                    400,
                )
            print(response)
            # crm_df = CRM.getCharacterDetails(Production_id, response)
            crm_df = CRM.getCharacterDetails(Production_id)
            if len(crm_df) > 0:
                try:
                    grouped_count = (
                        crm_df.groupby("Status").size().reset_index(name="count")
                    )
                    total_count = grouped_count["count"].sum()
                    grouped_count["percentage"] = (
                        grouped_count["count"] / total_count
                    ) * 100
                    group_list = grouped_count.to_dict(orient="records")
                except:
                    group_list = []
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": crm_df.to_dict("records"),
                        "count_list": group_list,
                    }
                )
            else:
                return jsonify(
                    {
                        "status": 400,
                        "message": "No Data Found",
                        "result": [],
                        "count_list": [],
                    }
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/get_location_setup", methods=["POST", "OPTIONS"])
def getLocationDetails():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Production_id = request.form.get("Production_id", None)

            if Production_id == None:
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": "pelase enter the Production_id filed",
                        }
                    ),
                    400,
                )
            # loc_df = LM.getLocationsDetails(Production_id, response)
            loc_df = LM.getLocationsDetails(Production_id)
            if len(loc_df) > 0:
                try:
                    grouped_count = (
                        loc_df.groupby("Status").size().reset_index(name="count")
                    )
                    total_count = grouped_count["count"].sum()
                    grouped_count["percentage"] = (
                        grouped_count["count"] / total_count
                    ) * 100
                    group_list = grouped_count.to_dict(orient="records")
                except:
                    group_list = []
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": loc_df.to_dict("records"),
                        "count_list": group_list,
                    }
                )
            else:
                return jsonify(
                    {
                        "status": 400,
                        "message": "No Data Found",
                        "result": [],
                        "count_list": [],
                    }
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


# @app.route('/api/add_production', methods=['GET'])
# def createProduction():
#     try:
#         conn = db_model.dbConnect()
#         status, response, msg = utils.getAuthorizationDetails(request)
#         if msg != "success":
#             return jsonify({"status": 401, "message": msg}), response
#         else:
#             Production_name = request.form.get('Production_name', None)
#             Production_Type_id = request.form.get('Production_Type_id', None)
#             image_upload = request.files.get('Image_Path', None)
#             insert_query = f"""Insert INTO Tbl_Productions  (Production_Name, Production_Type_Id, Image_Path,Record_Status)
#                 VALUES('{Production_name}', '{Production_Type_id}', '{image_upload}', 1)"""
#             conn = db_model.dbConnect()
#             cursor = conn.cursor()
#             try:
#                 cursor.execute(insert_query)
#                 conn.commit()
#                 return jsonify({"status": 200, 'message': 'Insert successfully'}), 200
#             except Exception as e:
#                 conn.rollback()
#                 return jsonify(
#                     {"status": 500, 'message': f'An error occurred while updating the sence: {str(e)}'}), 500
#             finally:
#                 conn.close()
#     except Exception as ex:
#         conn.rollback()
#         return jsonify({'error': f'An error occurred while updating the sence: {str(ex)}'}), 400
#     finally:
#         conn.close()


@app.route("/api/update_scene_setup", methods=["POST", "OPTIONS"])
def sceneSetupAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        conn = db_model.dbConnect()
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Scene_Id = request.form.get("Scene_Id")
            Script_Id = request.form.get("Script_Id", None)
            Scene_Type = request.form.get("Scene_Type", None)
            Scene_day_condition = request.form.get("Scene_day_condition", None)
            Script_Pages = request.form.get("Script_Pages", None)
            Scene_Location = request.form.get("Scene_Location", None)
            Shoot_Location = request.form.get("Shoot_Location", None)
            Scene_time = request.form.get("Scene_time", None)
            Shoot_Time = request.form.get("Shoot_Time", None)
            Short_description = request.form.get("Short_description", None)
            Status = request.form.get("Status", None)
            Assigned_To = request.form.get("Assigned_To", None)
            update_query_set = ""
            if not Scene_Id:
                return jsonify(
                    {"status": 400, "message": "Scene_Id field are required"}
                )
            # if Script_Id != None:
            #     update_query_set += f"Script_Id={Script_Id},"
            if Scene_Type != None:
                update_query_set += f"Scene_Type='{Scene_Type}',"
            if Scene_day_condition != None:
                update_query_set += f"Scene_day_condition='{Scene_day_condition}',"
            if Script_Pages != None:
                update_query_set += f"Script_Pages='{Script_Pages}',"
            if Scene_Location != None:
                update_query_set += f"Scene_Location = '{Scene_Location}',"
            if Shoot_Location != None:
                update_query_set += f"Shoot_Location = '{Shoot_Location}',"
            if Scene_time != None:
                update_query_set += f"Scene_time = '{Scene_time}',"
            if Shoot_Time != None:
                update_query_set += f"Shoot_Time = '{Shoot_Time}',"
            if Short_description != None:
                update_query_set += f"Short_description = '{Short_description}',"
            if Status != None:
                update_query_set += f"Status = '{Status}',"
            if Assigned_To != None:
                datetime_now = pd.to_datetime(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                update_query_set += (
                    f"Assigned_To = '{Assigned_To}',Assigned_date = '{datetime_now}',"
                )

            if update_query_set != "":
                update_query_set += f"Record_Status = 1, Created_By={response['id']}"
                update_query = f"UPDATE Tbl_Scene_details SET {update_query_set} WHERE Script_Id = {Script_Id}"
                conn = db_model.dbConnect()
                cursor = conn.cursor()
                try:
                    cursor.execute(update_query)
                    conn.commit()
                    return (
                        jsonify({"status": 200, "message": "updated successfully"}),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 500,
                                "message": f"An error occurred while updating the sence: {str(e)}",
                            }
                        ),
                        500,
                    )
                # finally:
                #     conn.close()
            else:
                return jsonify({"status": 400, "message": f"invalid input fileds"}), 400
    except Exception as ex:
        conn.rollback()
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )
    finally:
        conn.close()


# Modified version
# @app.route('/api/update_scene_setup', methods=['POST'])
# def scenesetupAPI():
#     try:
#         conn = db_model.dbConnect()
#         status, response, msg = utils.getAuthorizationDetails(request)
#         if msg != "success":
#             return jsonify({"status": 401, "message": msg}), response
#         else:
#             Scene_id = request.form.get('Scene_id')
#             Scene_type = request.form.get('Scene_type', None)
#             Scene_time = request.form.get('Scene_time', None)
#             Shoot_time = request.form.get('Shoot_time', None)
#             Costume = request.form.get('Costume',None)
#             Stunt = request.form.get('Stunt', None)
#             Makeup = request.form.get('Makeup', None)
#             Art = request.form.get('Art', None)
#
#             update_query_set = ""
#
#             if not Scene_id:
#                 return jsonify({"status": 400, "message": "Scene_id field are required"})
#             if Scene_type != None:
#                 update_query_set += f"Scene_type={Scene_type},"
#             if Scene_time != None:
#                 update_query_set += f"Scene_type={Scene_time},"
#             if Shoot_time != None:
#                 update_query_set += f"Shoot_time='{Shoot_time}',"
#             if Costume != None:
#                 update_query_set += f"Costume='{Costume}',"
#             if Stunt != None:
#                 update_query_set += f"Status = '{Stunt}',"
#             if Makeup != None:
#                 update_query_set += f"Makeup = {Makeup},"
#             if Art != None:
#                 update_query_set += f"Art = '{Art}',"
#
#             if update_query_set != "":
#
#                 update_scene_details = "UPDATE Tbl_Scene_details SET Scene_Type = ?, Scene_time = ?, Shoot_Time = ? " \
#                                        "WHERE Scene_Id = ?"
#                 update_scene_costume = "UPDATE Tbl_Scene_Costumes SET Costume = ? WHERE Scene_Id = ?"
#                 update_scene_makeup = "UPDATE Tbl_Scene_Makeup SET Makeup_Required = ? WHERE Scene_Id = ?"
#                 update_scene_art = "UPDATE Tbl_Scene_Art SET Art_Required = ? WHERE Scene_Id = ?"
#                 update_scene_stunt = "UPDATE Tbl_Scene_Stunts SET Stunt_Details = ? WHERE Scene_Id = ?"
#
#
#
#                 conn = db_model.dbConnect()
#                 cursor = conn.cursor()
#
#                 cursor.execute(update_scene_details,(Scene_type, Scene_time, Shoot_time, Scene_id ))
#                 cursor.execute(update_scene_costume,(Costume, Scene_id ))
#                 cursor.execute(update_scene_makeup,(Makeup, Scene_id ))
#                 cursor.execute(update_scene_art,(Art, Scene_id ))
#                 cursor.execute(update_scene_stunt,(Stunt, Scene_id ))
#                 conn.commit()
#                 cursor.close()
#
#                 return jsonify({'message': 'updated successfully'}), 200
#     except Exception as e:
#         conn.rollback()
#         return jsonify({'error': f'An error occurred while updating the character: {str(e)}'}), 500
#     finally:
#         conn.close()


@app.route("/api/update_character_setup", methods=["POST", "OPTIONS"])
def updateCharacterSetupAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Scene_Character_Id = request.form.get("Scene_Character_Id", None)
            Scene_Id = request.form.get("Scene_Id", None)
            Character_id = request.form.get("Character_id", None)
            Script_pages = request.form.get("Script_pages", None)
            Features_Required = request.form.get("Features_Required", None)
            No_Of_Scenes = request.form.get("No_Of_Scenes", None)
            Shoot_Time_Minutes = request.form.get("Shoot_Time_Minutes", None)
            Screen_Time_Minutes = request.form.get("Screen_Time_Minutes", None)
            Assigned_To = request.form.get("Assigned_To", None)
            Status = request.form.get("Status", "Submitted")
            update_query_set = ""
            if not Scene_Character_Id:
                return jsonify(
                    {"status": 400, "message": "Scene_Character_Id field are required"}
                )
            if Scene_Id != None:
                update_query_set += f"Scene_Id={Scene_Id},"
            if Character_id != None:
                update_query_set += f"Character_id={Character_id},"
            if Script_pages != None:
                update_query_set += f"Script_pages='{Script_pages}',"
            if Features_Required != None:
                update_query_set += f"Features_Required = '{Features_Required}',"
            if No_Of_Scenes != None:
                update_query_set += f"No_Of_Scenes = {No_Of_Scenes},"
            if Shoot_Time_Minutes != None:
                update_query_set += f"Shoot_Time_Minutes = {Shoot_Time_Minutes},"
            if Screen_Time_Minutes != None:
                update_query_set += f"Screen_Time_Minutes = {Screen_Time_Minutes},"
            if Assigned_To != None:
                datetime_now = pd.to_datetime(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                update_query_set += (
                    f"Assigned_To = {Assigned_To}, Assigned_date='{datetime_now}',"
                )

            if update_query_set != "":
                update_query_set += (
                    f"Record_Status=1, Created_By={response['id']}, Status='{Status}'"
                )
                update_query = f"UPDATE Tbl_Scene_Characters SET {update_query_set} WHERE Scene_Character_Id = {Scene_Character_Id}"
                conn = db_model.dbConnect()
                cursor = conn.cursor()
                try:
                    cursor.execute(update_query)
                    conn.commit()
                    return (
                        jsonify({"status": 200, "message": "updated successfully"}),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 500,
                                "message": f"An error occurred while updating the sence: {str(e)}",
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()
            else:
                return jsonify({"status": 400, "message": f"invalid input fileds"}), 400

    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/update_production", methods=["POST", "OPTIONS"])
def updateProductionDetailsAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Production_id = request.form.get("Production_id", None)
            Production_Name = request.form.get("Production_Name", None)
            Production_Type_Id = request.form.get("Production_Type_Id", None)
            Image_Path = request.form.get("Image_Path", None)
            update_query_set = ""
            if not Production_id:
                return jsonify(
                    {"status": 400, "message": "Production_id field are required"}
                )
            if Production_Name != None:
                update_query_set += f"Production_Name='{Production_Name}',"
            if Production_Type_Id != None:
                update_query_set += f"Production_Type_Id={Production_Type_Id},"
            if Image_Path != None:
                update_query_set += f"Image_Path='{Image_Path}',"
            if update_query_set != "":
                update_query_set += "Record_Status=1"
                update_production_table = f"UPDATE Tbl_Productions SET {update_query_set} WHERE Production_id = {Production_id}"
                conn = db_model.dbConnect()
                cursor = conn.cursor()
                try:
                    cursor.execute(update_production_table)
                    conn.commit()
                    cursor.close()
                    return jsonify({"message": "updated successfully"}), 200
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "error": f"An error occurred while updating the character: {str(e)}"
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()

            else:
                return jsonify({"status": 400, "message": f"invalid input fileds"}), 400

    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


# @app.route('/add_production', methods = ['POST'])
# def addProduction():
#     Production_name = request.form.get('Production_name', None)
#     Type_of_production = request.form.get('Type_of_production', None)
#     image_upload = request.files.get('image_upload',None)
#     print("Production_name:",Production_name,"Type_of_production:",Type_of_production,"image_upload:",image_upload)
#
#     if not Production_name:
#         return jsonify({"status": 400, "message": "Production_name field is required"})
#     if not Type_of_production:
#         return jsonify({"status": 400, "message": "Type_of_production field is required"})
#     if not image_upload:
#         return jsonify({"status": 400, "message": "image_upload is required"})
#     conn = db_model.dbConnect()
#     cursor = conn.cursor()
#     try:
#         query = f"SELECT * from Tbl_Productions"
#         df = pd.read_sql(query,conn)
#         print(len(df))
#         if len(df)>0:
#
#             update_production_name_query = "UPDATE Tbl_Productions SET Production_Name = ?"
#             update_production_type_query = "UPDATE Master_ProductionTypes SET Production_Type = ?"
#
#             # Execute the queries with parameters
#             cursor.execute(update_production_name_query, (Production_name,))
#             cursor.execute(update_production_type_query, (Type_of_production,))
#             conn.commit()
#             cursor.close()
#             return jsonify({'message': 'Production is updated successfully'}), 200
#         else:
#             return jsonify({"message": 'Production is not updated successfully'}), 400
#     except Exception as e:
#         conn.rollback()
#         return jsonify({'error': f'An error occurred while updating the production: {str(e)}'}), 500
#     finally:
#         conn.close()
@app.route("/api/add_production", methods=["POST", "OPTIONS"])
def addProductionDetailsAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type, Authorization"
            )
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response

        Production_Name = request.form.get("Production_Name")
        Production_Type_Id = request.form.get("Production_Type_Id")
        Image_Path = request.form.get("Image_Path")

        if (Production_Name or Production_Type_Id or Image_Path) == None:
            return jsonify({"status": 400, "message": "all the fields are required"})

        insert_query_set = (Production_Name, Production_Type_Id, Image_Path)

        if None not in insert_query_set:  # Check if all required fields are provided
            insert_query = "INSERT INTO Tbl_Productions (Production_Name, Production_Type_Id, Image_Path) VALUES (?, ?, ?)"
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(insert_query, insert_query_set)
                conn.commit()
                cursor.close()
                return jsonify({"message": "Inserted successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "error": f"An error occurred while inserting the values: {str(e)}"
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
        else:
            return jsonify({"status": 400, "message": "Invalid input fields"}), 400

    except Exception as ex:
        return jsonify({"status": 400, "message": f"An error occurred: {str(ex)}"}), 400


@app.route("/api/create_department", methods=["POST", "OPTIONS"])
def createDepartmentAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type, Authorization"
            )
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            # Department_Id = request.form.get('Department_Id', None)
            Production_id = request.form.get("Production_id", None)
            Department_Name = request.form.get("Department_Name", None)
            Department_Type = request.form.get("Department_Type", None)
            Total_Members = request.form.get("Total_Members", None)
            # if Department_Id == None:
            #     return jsonify({"status": 400, "message": "Department_Id field are required"})
            if Production_id == None:
                return jsonify(
                    {"status": 400, "message": "Production_id field are required"}
                )
            if Department_Name == None:
                return jsonify(
                    {"status": 400, "message": "Department_Name field are required"}
                )
            if Department_Type == None:
                return jsonify(
                    {"status": 400, "message": "Department_Type field are required"}
                )
            if Total_Members == None:
                return jsonify(
                    {"status": 400, "message": "Total_Members field are required"}
                )

            insert_department_table = f"""INSERT INTO Master_Departments (Production_id, Department_Name, Department_Type, Total_Members, Record_Status)
                        VALUES ({Production_id}, '{Department_Name}', '{Department_Type}', {Total_Members}, 1);"""
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(insert_department_table)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Insert successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/update_department", methods=["POST", "OPTIONS"])
def updateDepartmentAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Department_Id = request.form.get("Department_Id", None)
            Production_id = request.form.get("Production_id", None)
            Department_Name = request.form.get("Department_Name", None)
            Department_Type = request.form.get("Department_Type", None)
            Total_Members = request.form.get("Total_Members", None)
            if Department_Id == None:
                return jsonify(
                    {"status": 400, "message": "Department_Id field are required"}
                )
            update_query_set = ""
            if Production_id != None:
                update_query_set += f"Production_id={Production_id},"
            if Department_Name != None:
                update_query_set += f"Department_Name='{Department_Name}',"
            if Department_Type != None:
                update_query_set += f"Department_Type='{Department_Type}',"
            if Total_Members != None:
                update_query_set += f"Total_Members={Total_Members},"
            if update_query_set != "":
                update_query_set += "Record_Status=1"
                update_department_table = f"UPDATE Master_Departments SET {update_query_set} WHERE Department_Id={Department_Id}"
                conn = db_model.dbConnect()
                cursor = conn.cursor()
                try:
                    cursor.execute(update_department_table)
                    conn.commit()
                    cursor.close()
                    return (
                        jsonify({"status": 200, "message": "Updated successfully"}),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 400,
                                "message": f"An error occurred while updating the character: {str(e)}",
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()
            else:
                return jsonify({"status": 400, "message": f"give me valid input"}), 400
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/create_subdepartment", methods=["POST", "OPTIONS"])
def createSubDepartmentAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type, Authorization"
            )
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Production_id = request.form.get("Production_id", None)
            Department_Id = request.form.get("Department_Id", None)
            SubDepartment_Name = request.form.get("SubDepartment_Name", None)
            Total_Members = request.form.get("Total_Members", None)

            if Production_id == None:
                return jsonify(
                    {"status": 400, "message": "Production_id field are required"}
                )
            if Department_Id == None:
                return jsonify(
                    {"status": 400, "message": "Department_Id field are required"}
                )
            if SubDepartment_Name == None:
                return jsonify(
                    {"status": 400, "message": "SubDepartment_Name field are required"}
                )
            if Total_Members == None:
                return jsonify(
                    {"status": 400, "message": "Total_Members field are required"}
                )

            insert_department_table = f"""INSERT INTO Master_Sub_Departments (Production_id, Department_Id, SubDepartment_Name, Total_Members, Record_Status)
                        VALUES ({Production_id}, {Department_Id}, '{SubDepartment_Name}', {Total_Members}, 1);"""
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(insert_department_table)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Insert successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/update_subdepartment", methods=["POST", "OPTIONS"])
def updateSubDepartmentAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            SubDepartment_Id = request.form.get("SubDepartment_Id", None)
            Production_id = request.form.get("Production_id", None)
            Department_Id = request.form.get("Department_Id", None)
            SubDepartment_Name = request.form.get("SubDepartment_Name", None)
            Total_Members = request.form.get("Total_Members", None)
            if SubDepartment_Id == None:
                return jsonify(
                    {"status": 400, "message": "SubDepartment_Id field are required"}
                )
            update_query_set = ""
            if Production_id != None:
                update_query_set += f"Production_id={Production_id},"
            if Department_Id != None:
                update_query_set += f"Department_Id='{Department_Id}',"
            if SubDepartment_Name != None:
                update_query_set += f"SubDepartment_Name='{SubDepartment_Name}',"
            if Total_Members != None:
                update_query_set += f"Total_Members={Total_Members},"
            if update_query_set != "":
                update_query_set += "Record_Status=1"
                update_department_table = f"UPDATE Master_Sub_Departments SET {update_query_set} WHERE SubDepartment_Id={SubDepartment_Id}"
                conn = db_model.dbConnect()
                cursor = conn.cursor()
                try:
                    cursor.execute(update_department_table)
                    conn.commit()
                    cursor.close()
                    return (
                        jsonify({"status": 200, "message": "Updated successfully"}),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 400,
                                "message": f"An error occurred while updating the character: {str(e)}",
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()
            else:
                return jsonify({"status": 400, "message": f"give me valid input"}), 400
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/create_designations", methods=["POST", "OPTIONS"])
def createDesignationsAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Department_Id = request.form.get("Department_Id", None)
            SubDepartment_Id = request.form.get("SubDepartment_Id", None)
            Designation_Name = request.form.get("Designation_Name", None)

            if Department_Id == None:
                return jsonify(
                    {"status": 400, "message": "Department_Id field are required"}
                )
            if SubDepartment_Id == None:
                return jsonify(
                    {"status": 400, "message": "SubDepartment_Id field are required"}
                )
            if Designation_Name == None:
                return jsonify(
                    {"status": 400, "message": "Designation_Name field are required"}
                )

            create_designation_table = f"""INSERT INTO Master_Designations(Department_Id,
                          SubDepartment_Id,Designation_Name,Record_Status)
                      VALUES ({Department_Id},{SubDepartment_Id},'{Designation_Name}',1)"""
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(create_designation_table)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Insert successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/get_subdepartment", methods=["GET"])
def getSubDepartmentAPI():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            conn = db_model.dbConnect()
            # get_subdept = "SELECT * FROM Master_Sub_Departments"
            get_subdept = f"""SELECT MS.SubDepartment_Id,MS.SubDepartment_Name,MS.Department_Id,MD.Department_Name FROM Master_Sub_Departments AS MS
                    INNER JOIN Master_Departments AS MD ON MS.Department_Id = MD.Department_Id                              
                    """
            sub_dep_df = pd.read_sql(get_subdept, conn)
            if len(sub_dep_df) > 0:
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": sub_dep_df.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/get_designations", methods=["GET"])
def getDesignationsAPI():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            conn = db_model.dbConnect()
            get_subdept = "SELECT * FROM Master_Designations"
            df = pd.read_sql(get_subdept, conn)
            if len(df) > 0:
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": df.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/get_department", methods=["GET"])
def getDepartmentAPI():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            conn = db_model.dbConnect()
            get_subdept = "SELECT * FROM Master_Departments"
            df = pd.read_sql(get_subdept, conn)
            if len(df) > 0:
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": df.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/update_designations", methods=["POST", "OPTIONS"])
def updateDesignationsAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Department_Id = request.form.get("Department_Id", None)
            Department_Name = request.form.get("Department_Name", None)
            Department_Type = request.form.get("Department_Type", None)
            Total_Members = request.form.get("Total_Members", None)
            if Department_Id == None:
                return jsonify(
                    {"status": 400, "message": "Department_Id field are required"}
                )
            update_query_set = ""
            if Department_Name != None:
                update_query_set += f"Department_Name='{Department_Name}',"
            if Department_Type != None:
                update_query_set += f"Department_Type='{Department_Type}',"
            if Total_Members != None:
                update_query_set += f"Total_Members={Total_Members},"
            if Total_Members != None:
                update_query_set += f"Total_Members={Total_Members},"
            if update_query_set != "":
                update_query_set += "Record_Status=1"
                update_department_table = f"UPDATE Master_Sub_Departments SET {update_query_set} WHERE Department_Id={Department_Id}"
                conn = db_model.dbConnect()
                cursor = conn.cursor()
                try:
                    cursor.execute(update_department_table)
                    conn.commit()
                    cursor.close()
                    return (
                        jsonify({"status": 200, "message": "Updated successfully"}),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 400,
                                "message": f"An error occurred while updating the character: {str(e)}",
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()
            else:
                return jsonify({"status": 400, "message": f"give me valid input"}), 400
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/director_search/assign_character", methods=["GET", "POST", "OPTIONS"])
def getCharacters():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight check successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response
    status, response, msg = utils.getAuthorizationDetails(request)
    if msg != "success":
        return jsonify({"status": 401, "message": msg}), response
    else:
        try:
            if request.method == "GET":
                conn = db_model.dbConnect()
                get_all_characters = "SELECT * FROM Master_Character"
                df = pd.read_sql(get_all_characters, conn)
                if not df.empty:
                    df = df.fillna("")
                    df["Assigned_date"] = pd.to_datetime(
                        df["Assigned_date"], dayfirst=True
                    ).fillna("NA")
                    df.loc[df["Assigned_date"] == "NA", "Assigned_date"] = ""
                    return jsonify(
                        {
                            "status": 200,
                            "message": "successfully",
                            "result": df.to_dict("records"),
                        }
                    )
                else:
                    return jsonify(
                        {"status": 400, "message": "No Data Found", "result": []}
                    )

            elif request.method == "POST":
                id_list = request.form.getlist("id")

                if not id_list:
                    return jsonify({"error": 'No "id" parameter provided'}), 400

                conn = db_model.dbConnect()
                # Select the specific columns you want and filter based on id_list
                get_characters = f"""
                SELECT * FROM Master_Character WHERE Character_id IN ({', '.join(id_list)})
                """
                df = pd.read_sql(get_characters, conn)

                if not df.empty:
                    # df = df.fillna("")
                    # df['Assigned_date'] = pd.to_datetime(df['Assigned_date'], dayfirst=True).fillna("NA")
                    # df.loc[df['Assigned_date'] == "NA", "Assigned_date"] = ""
                    df = utils.handle_NATType(df)
                    return jsonify(
                        {
                            "status": 200,
                            "message": "successfully",
                            "result": df.to_dict("records"),
                        }
                    )
                else:
                    return jsonify(
                        {"status": 400, "message": "No Data Found", "result": []}
                    )

        except Exception as ex:
            return jsonify({"error": str(ex)}), 500


@app.route("/api/director_search/assign_location", methods=["GET", "POST", "OPTIONS"])
def getLocations():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight check successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response
    status, response, msg = utils.getAuthorizationDetails(request)
    if msg != "success":
        return jsonify({"status": 401, "message": msg}), response
    else:
        try:
            if request.method == "GET":
                conn = db_model.dbConnect()
                get_all_characters = (
                    "SELECT ML.* FROM Master_Locations as ML "
                    "INNER JOIN Tbl_Scene_locations as SL ON ML.Location_id = SL.Location_id"
                )
                df = pd.read_sql(get_all_characters, conn)
                if not df.empty:
                    df = df.fillna("")
                    if "Created_on" in df.columns:
                        del df["Created_on"]
                    return jsonify(
                        {
                            "status": 200,
                            "message": "successfully",
                            "result": df.to_dict("records"),
                        }
                    )
                else:
                    return jsonify(
                        {"status": 400, "message": "No Data Found", "result": []}
                    )

            elif request.method == "POST":
                id_list = request.form.getlist("id")

                if not id_list:
                    return jsonify({"error": 'No "id" parameter provided'}), 400
                conn = db_model.dbConnect()
                # Select the specific columns you want and filter based on id_list
                get_characters = f"""
                SELECT ML.*
                FROM Master_Locations as ML 
                INNER JOIN Tbl_Scene_locations as SL ON ML.Location_id = SL.Location_id
                 where SL.Location_id IN ({', '.join(id_list)})
                """
                df = pd.read_sql(get_characters, conn)
                if not df.empty:
                    df = df.fillna("")
                    if "Created_on" in df.columns:
                        del df["Created_on"]
                    return jsonify(
                        {
                            "status": 200,
                            "message": "successfully",
                            "result": df.to_dict("records"),
                        }
                    )
                else:
                    return jsonify(
                        {"status": 400, "message": "No Data Found", "result": []}
                    )
        except Exception as ex:
            return jsonify({"error": str(ex)}), 500


# @app.route('/api/director_search/assign_location', methods = ['GET', 'POST'])
# def getLocations():
#     status, response, msg = utils.getAuthorizationDetails(request)
#     if msg!= 'success':
#         return jsonify({"status": 401, "message": msg}), response
#     try:
#         if request.method = 'GET':
#             conn = db_model.dbConnect()
#             get_all locations =


# 1. char list and update
# 2. AD LIST - Done
# 3. Driector List - Done
# 4. locaton list and update
# 5. Casting Call
@app.route("/api/director_list", methods=["POST", "OPTIONS"])
def getDirectorListAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response
        production_id = request.form.get("production_id", None)
        status, response, msg = utils.getAuthorizationDetails(request)

        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            conn = db_model.dbConnect()
            if production_id == None:
                get_director = (
                    f"SELECT * FROM Tbl_App_Users where Designation='Director'"
                )
            else:
                get_director = f"""SELECT * FROM Tbl_App_Users where
                                Designation='Director' AND User_id IN (SELECT User_id FROM Tbl_User_Productions WHERE Production_id = {production_id})"""
            df = pd.read_sql(get_director, conn)
            if len(df) > 0:
                df = df[
                    [
                        "Designation",
                        "Email_Id",
                        "Full_Name",
                        "Mobile_No",
                        "User_Name",
                        "User_id",
                    ]
                ]
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": df.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/asstdirector_list", methods=["POST", "OPTIONS"])
def getAsstDirectorListAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            conn = db_model.dbConnect()
            production_id = request.form.get("production_id", None)
            if production_id == None:
                get_director = (
                    f"SELECT * FROM Tbl_App_Users where Designation='Asst Director'"
                )
            else:
                get_director = f"""SELECT * FROM Tbl_App_Users where Designation='Asst Director' AND 
                User_id IN (SELECT User_id FROM Tbl_User_Productions WHERE Production_id = {production_id})"""
            df = pd.read_sql(get_director, conn)
            if len(df) > 0:
                df = df[
                    [
                        "User_id",
                        "Designation",
                        "Email_Id",
                        "Full_Name",
                        "Mobile_No",
                        "User_Name",
                    ]
                ]
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": df.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/update_assign_char", methods=["POST", "OPTIONS"])
def updateAssignCharAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Character_id = request.form.get("Character_id", None)
            Assigned_To = request.form.get("Assigned_To", None)
            if Character_id == None or eval(Character_id) == []:
                return (
                    jsonify(
                        {"status": 400, "message": "Character_id field are required"}
                    ),
                    400,
                )
            if Assigned_To == None:
                return (
                    jsonify(
                        {"status": 400, "message": "Assigned_To field are required"}
                    ),
                    400,
                )
            datetime_now = pd.to_datetime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            Character_id = list(eval(Character_id))
            update_data = """UPDATE Master_Character
                                   SET Assigned_To = ?,
                                       Assigned_date = ?
                                   WHERE Character_id IN ({})""".format(
                ",".join("?" for _ in Character_id)
            )
            print(update_data)
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(update_data, [Assigned_To, datetime_now] + Character_id)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Updated successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/update_assign_location", methods=["POST", "OPTIONS"])
def updateAssignLocationAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Location_Id = request.form.get("Location_Id", None)
            Assigned_To = request.form.get("Assigned_To", None)

            if Location_Id == None or eval(Location_Id) == []:
                return (
                    jsonify(
                        {"status": 400, "message": "Location_Id field are required"}
                    ),
                    400,
                )
            if Assigned_To == None:
                return (
                    jsonify(
                        {"status": 400, "message": "Assigned_To field are required"}
                    ),
                    400,
                )
            Location_id = list(eval(Location_Id))
            datetime_now = pd.to_datetime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(datetime_now)
            update_data = """UPDATE Master_Locations
                       SET Assigned_To = ?,
                           Assigned_date = ?
                       WHERE Location_Id IN ({})""".format(
                ",".join("?" for _ in Location_id)
            )
            print(update_data)
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(update_data, [Assigned_To, datetime_now] + Location_id)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Updated successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/approve_assign_char", methods=["POST", "OPTIONS"])
def ApproveAssignCharAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Scene_Character_Id = request.form.get("Scene_Character_Id", None)
            Character_id = request.form.get("Character_id", None)
            if Scene_Character_Id == None:
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": "Scene_Character_Id field are required",
                        }
                    ),
                    400,
                )
            if Character_id == None:
                return (
                    jsonify(
                        {"status": 400, "message": "Character_id field are required"}
                    ),
                    400,
                )

            datetime_now = pd.to_datetime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(datetime_now)
            update_data = f"""UPDATE Master_Locations SET Status = 'Approved' WHERE Character_id = {Character_id}
                        UPDATE Tbl_Scene_characters SET Status = 'Approved' WHERE Scene_Character_Id = {Scene_Character_Id}
                    """
            print(update_data)
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(update_data)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Updated successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/approve_assign_location", methods=["POST", "OPTIONS"])
def ApproveAssignLocationAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Location_Id = request.form.get("Location_Id", None)
            Scene_Location_Id = request.form.get("Scene_Location_Id", None)
            if Location_Id == None:
                return (
                    jsonify(
                        {"status": 400, "message": "Location_Id field are required"}
                    ),
                    400,
                )
            if Scene_Location_Id == None:
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": "Scene_Location_Id field are required",
                        }
                    ),
                    400,
                )

            datetime_now = pd.to_datetime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(datetime_now)
            update_data = f"""UPDATE Master_Locations SET Status = 'Approved' WHERE Location_Id = {Location_Id}
                        UPDATE Tbl_Scene_Locations SET Status = 'Approved' WHERE Scene_Location_Id = {Scene_Location_Id}
                    """
            print(update_data)
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(update_data)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Updated successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/get_actors", methods=["GET"])
def GetActors():
    try:
        conn = db_model.dbConnect()
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            user_id = response["id"]
            query = "SELECT * FROM Tbl_Actor_Details"
            df = pd.read_sql(query, conn)
            if len(df) > 0:
                return jsonify(
                    {
                        "status": 200,
                        "message": "records fetched successfully!",
                        "result": df.to_dict("records"),
                    }
                )
            else:
                return jsonify({"status": 204, "message": "No data Found"})
    except Exception as ex:
        conn.rollback()
        return (
            jsonify(
                {"error": f"An error occurred while fetching the details: {str(ex)}"}
            ),
            400,
        )

    finally:
        conn.close()


@app.route("/api/create_actor", methods=["POST", "OPTIONS"])
def createActorsAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            ActorName = request.form.get("ActorName", None)
            Gender = request.form.get("Gender", None)
            Height = request.form.get("Height", None)
            ActingAge = request.form.get("ActingAge", None)
            HairColour = request.form.get("HairColour", None)
            EyeColour = request.form.get("EyeColour", None)
            Language = request.form.get("Language", None)
            Email = request.form.get("Email", None)
            PhoneNumber = request.form.get("PhoneNumber", None)
            PerformingArts = request.form.get("PerformingArts", None)
            Athletics = request.form.get("Athletics", None)
            DanceAndMusic = request.form.get("DanceAndMusic", None)
            Address = request.form.get("Address", None)
            FilmExperience = request.form.get("FilmExperience", None)
            Roles = request.form.get("Roles", None)
            Films = request.form.get("Films", None)
            Role = request.form.get("Role", None)
            if ActorName == None:
                return jsonify(
                    {"status": 400, "message": "ActorName field are required"}
                )
            if Gender == None:
                return jsonify({"status": 400, "message": "Gender field are required"})

            # insert_query = '''
            # INSERT INTO Tbl_Actor_Details (ActorName, Gender, Height, ActingAge, HairColour, EyeColour, PhoneNumber,
            #     PerformingArts, Athletics, DanceAndMusic, Address, FilmExperience, Roles, Films, Role,Language, Email)
            # VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            # '''

            insert_query = """
            INSERT INTO Tbl_Actor_Details (ActorName, Gender, Height, ActingAge, HairColour, EyeColour, PhoneNumber,
                PerformingArts, Athletics, DanceAndMusic, Address, FilmExperience, Roles, Films, Role, Language, Email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            conn = db_model.dbConnect()
            cursor = conn.cursor()
            # data = (ActorName,Gender,Height,ActingAge, HairColour, EyeColour, PhoneNumber,PerformingArts, Athletics, DanceAndMusic,
            #               Address, FilmExperience, Roles, Films, Role, Language, Email)

            data = (
                ActorName,
                Gender,
                Height,
                ActingAge,
                HairColour,
                EyeColour,
                PhoneNumber,
                PerformingArts,
                Athletics,
                DanceAndMusic,
                Address,
                FilmExperience,
                Roles,
                Films,
                Role,
                Language,
                Email,
            )
            try:
                cursor.execute(insert_query, data)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Insert successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/create_location", methods=["POST", "OPTIONS"])
def createlocationsAPI():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "Preflight check successful"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Methods", "POST")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            LocationName = request.form.get("LocationName", None)
            LocationType = request.form.get("LocationType", None)
            Category = request.form.get("Category", None)
            Specifications = request.form.get("Specifications", None)
            BudgetDay = request.form.get("BudgetDay", None)
            Country = request.form.get("Country", None)
            Address = request.form.get("Address", None)
            OwnerDetails = request.form.get("OwnerDetails", None)
            PreviousFilms = request.form.get("PreviousFilms", None)
            Permissions = request.form.get("Permissions", None)

            if LocationName == None:
                return jsonify(
                    {"status": 400, "message": "LocationName field are required"}
                )
            if LocationType == None:
                return jsonify(
                    {"status": 400, "message": "LocationType field are required"}
                )

            # insert_query = '''
            # INSERT INTO Tbl_Actor_Details (ActorName, Gender, Height, ActingAge, HairColour, EyeColour, PhoneNumber,
            #     PerformingArts, Athletics, DanceAndMusic, Address, FilmExperience, Roles, Films, Role,Language, Email)
            # VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            # '''

            insert_query = """
            INSERT INTO Master_Locations (Location_Name, Location_Type, Category, Specification, Budget_day, Country, 
            Location_Description,Owner_details, Previous_Films, Permissions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            conn = db_model.dbConnect()
            cursor = conn.cursor()

            data = (
                LocationName,
                LocationType,
                Category,
                Specifications,
                BudgetDay,
                Country,
                Address,
                OwnerDetails,
                PreviousFilms,
                Permissions,
            )

            try:
                cursor.execute(insert_query, data)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Insert successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/upload_script", methods=["POST", "OPTIONS"])
def uploaded_file():
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight check successful"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response

    if "productname" in request.form:
        production_name = request.form["productname"]
        print(production_name)

    else:
        return {
            "status_code": 400,
            "status": "Failure",
            "message": "please specify productname",
        }

    if "file" in request.files:
        f = request.files["file"]

    else:
        return {
            "status_code": 400,
            "status": "Failure",
            "message": "please specify file",
        }

    f.save(os.path.join(config.UPLOAD_FOLDER, secure_filename(f.filename)))

    path = os.path.join(config.UPLOAD_FOLDER, secure_filename(f.filename))

    # print(path)

    ##------------------------------------------------------------------------------------------------------------------

    # """Code for Insertion of Script Data"""

    conn = db_model.dbConnect()
    cursor = conn.cursor()

    IdentityINSERT_ON_sql = "SET IDENTITY_INSERT Tbl_Script_Uploads ON"
    IdentityINSERT_OFF_sql = "SET IDENTITY_INSERT Tbl_Script_Uploads OFF"

    try:

        query = f"""
            select top(1) [Scene_Id] FROM [FilmPro].[dbo].[Tbl_Scene_details] order by [Scene_Id] desc
        """
        scene_detail_df = pd.read_sql(query, conn)

        query = f"""
            select top(1) [Script_Id] FROM [FilmPro].[dbo].[Tbl_Script_Uploads] order by [Script_Id] desc
        """
        script_df = pd.read_sql(query, conn)

        query = f"""
            select top(1) [Production_id] FROM [FilmPro].[dbo].[Tbl_User_Productions] order by [Production_id] desc
        """
        prod_df = pd.read_sql(
            query, conn
        )  # Change only this SQL query based on User Id fetch

        query = f"""
            select top(1) [Character_id] FROM [FilmPro].[dbo].[Master_Character] order by [Character_id] desc
        """
        char_df = pd.read_sql(
            query, conn
        )  # take the last updated master_character id and #Change only this SQL query based on User Id fetch

        query = f"""
            select top(1) [Location_Id] FROM [FilmPro].[dbo].[Master_Locations] order by [Location_Id] desc
        """
        loc_df = pd.read_sql(
            query, conn
        )  # take the last updated Master_Locations id and #Change only this SQL query based on User Id fetch

        query = f"""
            select top(1) [Scene_Character_Id] FROM [FilmPro].[dbo].[Tbl_Scene_characters] order by [Scene_Character_Id] desc
        """
        scene_char_df = pd.read_sql(
            query, conn
        )  # take the last updated Tbl_Scene_characters id and #Change only this SQL query based on User Id fetch

        query = f"""
            select top(1) [Scene_Location_Id] FROM [FilmPro].[dbo].[Tbl_Scene_Locations] order by [Scene_Location_Id] desc
        """
        scene_loc_df = pd.read_sql(
            query, conn
        )  # take the last updated Tbl_Scene_characters id and #Change only this SQL query based on User Id fetch

        if (
            (len(script_df) > 0)
            and (len(prod_df) > 0 and len(char_df) > 0)
            and (len(loc_df) > 0 and len(scene_char_df) > 0)
            and (len(scene_loc_df) > 0)
        ):
            scene_detail_id = scene_detail_df["Scene_Id"][0] + 1
            script_id = script_df["Script_Id"][0] + 1
            prod_id = prod_df["Production_id"][0]
            Master_char_id = char_df["Character_id"][0]
            Master_loc_id = loc_df["Location_Id"][0]
            Scene_char_id = scene_char_df["Scene_Character_Id"][0]
            Scene_loc_id = scene_loc_df["Scene_Location_Id"][0]

    except pyodbc.Error as e:
        print(f"Error fetching tables: {e}")

        return jsonify({"message": "Insertion of Script data unsuccessfull"}), 401

    print(
        scene_detail_id,
        script_id,
        prod_id,
        Master_char_id,
        Master_loc_id,
        Scene_char_id,
        Scene_loc_id,
    )

    script_sql = (
        """INSERT INTO dbo.Tbl_Script_Uploads (Script_Id, Production_id, Script_Name, No_of_Pages, Script_Upload_Path, Script_Description, Record_Status, Created_on, Created_By)
VALUES ("""
        + str(script_id)
        + """, """
        + str(prod_id)
        + """, '"""
        + str(production_name)
        + """', 4, '"""
        + str(path)
        + """', '"""
        + str(production_name)
        + """' , 'Open', convert(datetime,'18-06-12 01:44:09 AM',5), 0)"""
    )

    # cursor.execute(IdentityINSERT_ON_sql)

    cursor.execute(script_sql)
    conn.commit()

    cursor.execute(IdentityINSERT_OFF_sql)

    ##------------------------------------------------------------------------------------------------------------------

    # """Code for Insertion of Scene Data"""

    config.file_name = secure_filename(f.filename)

    (
        df1,
        characters,
        locations,
        scenes_names,
        scene_display_text,
        script_display_text,
    ) = main_func(
        file_path=config.UPLOAD_FOLDER,
        file_name=secure_filename(f.filename),
        status=True,
    )

    IdentityINSERT_ON_sql = "SET IDENTITY_INSERT Tbl_Scene_details ON"
    IdentityINSERT_OFF_sql = "SET IDENTITY_INSERT Tbl_Scene_details OFF"

    no_of_scenes = df1.shape[0]  # No of Scenes in the df1 taking only 10 for demo

    # cursor.execute(IdentityINSERT_ON_sql)

    for scene_id in range(0, no_of_scenes + 1):

        # print(df1.iloc[scene_id])

        typ_ = ""
        condi = ""
        loc = ""

        try:

            typ_ = df1.iloc[scene_id]["Internal_External"].replace("'", "")
            condi = df1.iloc[scene_id]["Day_Night"].replace("'", "")
            loc = df1.iloc[scene_id]["Location"].replace("'", "")

        except:
            pass

        scene_id += scene_detail_id
        scene_id += 1

        scene_sql = f"""INSERT INTO dbo.Tbl_Scene_details (Scene_Id, Production_id, Script_Id, Scene_Type, Scene_day_condition, Script_Pages, Scene_Location,
                                    Shoot_Location, Status, Short_description, Assigned_To, Record_Status, Created_on, Created_By)
    VALUES ({scene_id}, {prod_id}, {script_id}, '{typ_}', '{condi}', 1, '{loc}', '', 'Open', '', 999999, 1, convert(datetime,'18-06-12 04:27:09 AM',5), 999999)"""

        cursor.execute(scene_sql)
        conn.commit()

    # cursor.execute(IdentityINSERT_OFF_sql)

    ##------------------------------------------------------------------------------------------------------------------

    # """Code for Insertion of Charecter"""

    start_char_id = Master_char_id

    IdentityINSERT_ON_sql = "SET IDENTITY_INSERT Master_Character ON"
    IdentityINSERT_OFF_sql = "SET IDENTITY_INSERT Master_Character OFF"

    # cursor.execute(IdentityINSERT_ON_sql)

    for char_id in range(len(characters)):
        character_name = characters[char_id].replace("'", "")
        M_char_id = char_id + start_char_id + 1

        character_sql = f"""INSERT INTO dbo.Master_Character (Character_id, Character_Name) VALUES ({M_char_id}, '{character_name}')"""

        cursor.execute(character_sql)
        conn.commit()

    # cursor.execute(IdentityINSERT_OFF_sql)

    ##------------------------------------------------------------------------------------------------------------------

    # """Code for Insertion of Location Data"""

    start_loc_id = Master_loc_id

    IdentityINSERT_ON_sql = "SET IDENTITY_INSERT Master_Locations ON"
    IdentityINSERT_OFF_sql = "SET IDENTITY_INSERT Master_Locations OFF"

    # cursor.execute(IdentityINSERT_ON_sql)

    for loc_id in range(len(locations)):
        location_name = locations[loc_id].replace("'", "")

        M_loc_id = loc_id + start_loc_id + 1

        location_sql = f"""INSERT INTO dbo.Master_Locations (Location_Id, Location_Name) VALUES ({M_loc_id}, '{location_name}')"""

        cursor.execute(location_sql)
        conn.commit()

    # cursor.execute(IdentityINSERT_OFF_sql)

    ##------------------------------------------------------------------------------------------------------------------

    # """Code for Insertion of Scene_Charecter"""

    start_scene_char_id = Scene_char_id

    IdentityINSERT_ON_sql = "SET IDENTITY_INSERT Tbl_Scene_characters ON"
    IdentityINSERT_OFF_sql = "SET IDENTITY_INSERT Tbl_Scene_characters OFF"

    # cursor.execute(IdentityINSERT_ON_sql)

    df2 = df1[["Scene_number", "Scene_Characters"]].copy()

    no_of_scenes = df2.shape[0]

    pk_scene_char_id = start_scene_char_id + 1

    for scene_char_id in range(no_of_scenes):

        for char in df2.iloc[scene_char_id]["Scene_Characters"]:
            char = char.replace("'", "")
            cursor.execute(
                "SELECT Character_id FROM Master_Character WHERE Character_Name = ?;",
                (char),
            )
            char_id = cursor.fetchone()

            scene_char_id += scene_detail_id
            scene_char_id += 1

            scene_char_sql = f"""INSERT INTO dbo.Tbl_Scene_characters (Scene_Character_Id, Production_id, Scene_Id, Character_id) 
            VALUES ({pk_scene_char_id}, {prod_id}, {scene_char_id}, {char_id[0]})"""

            pk_scene_char_id += 1

            cursor.execute(scene_char_sql)
            conn.commit()

    # cursor.execute(IdentityINSERT_OFF_sql)

    ##------------------------------------------------------------------------------------------------------------------

    # """Code for Insertion of Scene_Location Data"""

    start_scene_loc_id = Scene_loc_id

    IdentityINSERT_ON_sql = "SET IDENTITY_INSERT Tbl_Scene_Locations ON"
    IdentityINSERT_OFF_sql = "SET IDENTITY_INSERT Tbl_Scene_Locations OFF"

    # cursor.execute(IdentityINSERT_ON_sql)

    df2 = df1[["Scene_number", "Location"]].copy()

    pk_scene_loc_id = start_scene_loc_id + 1

    no_of_scenes = df2.shape[0]

    for scene_loc_id in range(no_of_scenes):
        loc = df2.iloc[scene_loc_id]["Location"].replace("'", "")
        cursor.execute(
            "SELECT Location_Id FROM Master_Locations WHERE Location_Name = ?;", (loc)
        )
        loc_id = cursor.fetchone()

        scene_loc_id += scene_detail_id
        scene_loc_id += 1

        scene_loc_sql = f"""INSERT INTO dbo.Tbl_Scene_Locations (Scene_Location_Id, Production_id, Scene_Id, Location_Id) 
        VALUES ({pk_scene_loc_id}, {prod_id}, {scene_loc_id}, {loc_id[0]})"""

        pk_scene_loc_id += 1

        cursor.execute(scene_loc_sql)
        conn.commit()

    # cursor.execute(IdentityINSERT_OFF_sql)

    ##------------------------------------------------------------------------------------------------------------------

    cursor.close()

    final_data = {
        "status_code": 200,
        "message": "Insertion of Script data successfully",
        "len": df1.shape[0],
        "scene_numbers": df1.Scene_number.tolist(),
        "scenes_script": scene_display_text,
        "scene_names": scenes_names,
        "Script_text": script_display_text,
    }

    # Set CORS headers in the response

    response = jsonify(final_data)
    response.headers.add("Access-Control-Allow-Origin", "*")

    return response


@app.route("/api/char_assign_actor", methods=["POST"])
def charAsignActorAPI():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Character_id = request.form.get("Character_id", None)
            actor_id = request.form.get("actor_id", None)
            if Character_id == None:
                return jsonify(
                    {"status": 400, "message": "Character_id field are required"}
                )
            if actor_id == None:
                return jsonify(
                    {"status": 400, "message": "actor_id field are required"}
                )
            character_sql = f"UPDATE Master_Character SET seleted_actor_id = {actor_id} WHERE Character_id = {Character_id}"
            conn = db_model.dbConnect()
            cursor = conn.cursor()
            try:
                cursor.execute(character_sql)
                conn.commit()
                cursor.close()
                return jsonify({"status": 200, "message": "Insert successfully"}), 200
            except Exception as e:
                conn.rollback()
                return (
                    jsonify(
                        {
                            "status": 400,
                            "message": f"An error occurred while updating the character: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/select_character", methods=["POST"])
def selectCharacterAPI():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        msg = "success"
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Character_id = request.form.get("Character_id", None)
            if Character_id == None:
                return jsonify(
                    {"status": 400, "message": "Character_id field are required"}
                )
            else:
                conn = db_model.dbConnect()
                if not pd.isnull(Character_id):
                    mc_df = pd.read_sql(
                        f"Select * from Master_Character WHERE Character_id = {Character_id}",
                        conn,
                    )
                    final_data = {}
                    if len(mc_df) > 0:
                        final_data["character_data"] = mc_df.to_dict("records")[0]
                        actor_id = mc_df.iloc[0]["seleted_actor_id"]
                    if not pd.isnull(actor_id):
                        ad_df = pd.read_sql(
                            f"Select * from Tbl_Actor_Details WHERE actor_id = {mc_df.iloc[0]['seleted_actor_id']}",
                            conn,
                        )
                        if len(ad_df) > 0:
                            final_data["actor_data"] = ad_df.to_dict("records")[0]
                try:
                    return (
                        jsonify(
                            {
                                "status": 200,
                                "message": "successfully",
                                "result": final_data,
                            }
                        ),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 400,
                                "message": f"An error occurred while updating the character: {str(e)}",
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/select_location", methods=["POST"])
def selectLocationAPI():
    try:
        status, response, msg = utils.getAuthorizationDetails(request)
        msg = "success"
        if msg != "success":
            return jsonify({"status": 401, "message": msg}), response
        else:
            Location_Id = request.form.get("Location_Id", None)
            if Location_Id == None:
                return jsonify(
                    {"status": 400, "message": "Location_Id field are required"}
                )
            else:
                conn = db_model.dbConnect()
                query = f"""
                        select * from Master_Locations as ML
                        INNER JOIN Tbl_Scene_Locations as TL ON ML.Location_Id = TL.Location_Id 
                        WHERE TL.Location_Id ={Location_Id}"""
                if not pd.isnull(Location_Id):
                    mc_df = pd.read_sql(query, conn)
                    final_data = {}
                    if len(mc_df) > 0:
                        final_data = mc_df.to_dict("records")
                try:
                    return (
                        jsonify(
                            {
                                "status": 200,
                                "message": "successfully",
                                "result": final_data,
                            }
                        ),
                        200,
                    )
                except Exception as e:
                    conn.rollback()
                    return (
                        jsonify(
                            {
                                "status": 400,
                                "message": f"An error occurred while updating the location: {str(e)}",
                            }
                        ),
                        500,
                    )
                finally:
                    conn.close()
    except Exception as ex:
        return (
            jsonify(
                {
                    "status": 400,
                    "message": f"An error occurred while updating the sence: {str(ex)}",
                }
            ),
            400,
        )


@app.route("/api/master_location", methods=["POST"])
def getMasterLocations():
    status, response, msg = utils.getAuthorizationDetails(request)
    msg = "success"
    if msg != "success":
        return jsonify({"status": 401, "message": msg}), response
    else:
        try:
            conn = db_model.dbConnect()
            df = pd.read_sql("SELECT * FROM Master_Locations", conn)
            if not df.empty:
                df = df.fillna("")
                if "Created_on" in df.columns:
                    del df["Created_on"]
                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "result": df.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )

        except Exception as ex:
            return jsonify({"error": str(ex)}), 500


# @app.route('/api/status_character', methods=['POST'])
# def getOpenCharacter():
#     status, response, msg = utils.getAuthorizationDetails(request)
#     msg = "success"
#     if msg != "success":
#         return jsonify({"status": 401, "message": msg}), response
#     else:
#         try:
#             Status = request.form.get('status', "Open")
#             conn = db_model.dbConnect()
#             df = pd.read_sql(f"SELECT * FROM Tbl_Scene_characters where Status = '{str(Status)}'", conn)
#             if not df.empty:
#                 df = df.fillna("")
#                 if 'Created_on' in df.columns:
#                     del df['Created_on']
#                 return jsonify({"status": 200, "message": "successfully", 'result': df.to_dict("records")})
#             else:
#                 return jsonify({"status": 400, "message": "No Data Found", 'result': []})
#
#         except Exception as ex:
#             return jsonify({'error': str(ex)}), 500

# @app.route('/api/status_scence', methods=['POST'])
# def getOpenScence():
#     status, response, msg = utils.getAuthorizationDetails(request)
#     msg = "success"
#     if msg != "success":
#         return jsonify({"status": 401, "message": msg}), response
#     else:
#         try:
#             Status = request.form.get('status', "Open")
#             conn = db_model.dbConnect()
#             df = pd.read_sql(f"SELECT * FROM Tbl_Scene_details where Status = '{str(Status)}'", conn)
#             if not df.empty:
#                 df = df.fillna("")
#                 if 'Created_on' in df.columns:
#                     del df['Created_on']
#                 return jsonify({"status": 200, "message": "successfully", 'result': df.to_dict("records")})
#             else:
#                 return jsonify({"status": 400, "message": "No Data Found", 'result': []})
#
#         except Exception as ex:
#             return jsonify({'error': str(ex)}), 500

# @app.route('/api/status_location', methods=['POST'])
# def getOpenLocation():
#     status, response, msg = utils.getAuthorizationDetails(request)
#     msg = "success"
#     if msg != "success":
#         return jsonify({"status": 401, "message": msg}), response
#     else:
#         try:
#             Status = request.form.get('status', "Open")
#             conn = db_model.dbConnect()
#             df = pd.read_sql(f"SELECT * FROM Tbl_Scene_Locations where Status = '{str(Status)}'", conn)
#             if not df.empty:
#                 df = df.fillna("")
#                 if 'Created_on' in df.columns:
#                     del df['Created_on']
#                 return jsonify({"status": 200, "message": "successfully", 'result': df.to_dict("records")})
#             else:
#                 return jsonify({"status": 400, "message": "No Data Found", 'result': []})
#
#         except Exception as ex:
#             return jsonify({'error': str(ex)}), 500


@app.route("/api/status_scence", methods=["POST"])
def getOpenScence():
    status, response, msg = utils.getAuthorizationDetails(request)
    if msg != "success":
        return jsonify({"status": 401, "message": msg}), response
    else:
        try:
            status_values = ["Open", "Assigned", "Completed"]
            conn = db_model.dbConnect()

            # Using a single query to fetch all required statuses
            query = f"SELECT * FROM Tbl_Scene_details WHERE Status IN {tuple(status_values)}"
            result_df = pd.read_sql(query, conn)
            result_df = utils.handle_NATType(result_df)

            if not result_df.empty:
                result_df = result_df.fillna("")
                if "Created_on" in result_df.columns:
                    del result_df["Created_on"]

                # Split the DataFrame based on Status values
                df1 = result_df[result_df["Status"] == "Open"]
                df2 = result_df[result_df["Status"] == "Assigned"]
                df3 = result_df[result_df["Status"] == "Completed"]

                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "Open records": df1.to_dict("records"),
                        "Assigned records": df2.to_dict("records"),
                        "Submitted records": df3.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )

        except Exception as ex:
            return jsonify({"error": str(ex)}), 500


@app.route("/api/status_character", methods=["POST"])
def getOpenCharacter():
    status, response, msg = utils.getAuthorizationDetails(request)
    if msg != "success":
        return jsonify({"status": 401, "message": msg}), response
    else:
        try:
            status_values = ["Open", "Assigned", "Completed"]
            conn = db_model.dbConnect()

            # Using a single query to fetch all required statuses
            query = f"""SELECT SC.*, MC.Description FROM Master_Character as MC INNER JOIN 
            Tbl_Scene_characters as SC on MC.Character_id = SC.Character_id where SC.Status IN {tuple(status_values)}"""
            result_df = pd.read_sql(query, conn)
            result_df = utils.handle_NATType(result_df)

            if not result_df.empty:
                result_df = result_df.fillna("")
                if "Created_on" in result_df.columns:
                    del result_df["Created_on"]

                # Split the DataFrame based on Status values
                df1 = result_df[result_df["Status"] == "Open"]
                df2 = result_df[result_df["Status"] == "Assigned"]
                df3 = result_df[result_df["Status"] == "Completed"]

                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "Open records": df1.to_dict("records"),
                        "Assigned records": df2.to_dict("records"),
                        "Submitted records": df3.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )

        except Exception as ex:
            return jsonify({"error": str(ex)}), 500


@app.route("/api/status_location", methods=["POST"])
def getOpenLocation():
    status, response, msg = utils.getAuthorizationDetails(request)
    if msg != "success":
        return jsonify({"status": 401, "message": msg}), response
    else:
        try:
            status_values = ["Open", "Assigned", "Completed"]
            conn = db_model.dbConnect()

            # Using a single query to fetch all required statuses
            query = f"SELECT * FROM Tbl_Scene_Locations WHERE Status IN {tuple(status_values)}"
            result_df = pd.read_sql(query, conn)
            result_df = utils.handle_NATType(result_df)

            if not result_df.empty:
                result_df = result_df.fillna("")
                if "Created_on" in result_df.columns:
                    del result_df["Created_on"]

                # Split the DataFrame based on Status values
                df1 = result_df[result_df["Status"] == "Open"]
                df2 = result_df[result_df["Status"] == "Assigned"]
                df3 = result_df[result_df["Status"] == "Completed"]

                return jsonify(
                    {
                        "status": 200,
                        "message": "successfully",
                        "Open records": df1.to_dict("records"),
                        "Assigned records": df2.to_dict("records"),
                        "Submitted records": df3.to_dict("records"),
                    }
                )
            else:
                return jsonify(
                    {"status": 400, "message": "No Data Found", "result": []}
                )

        except Exception as ex:
            return jsonify({"error": str(ex)}), 500


if __name__ == "__main__":
    app.run(port=8001)
