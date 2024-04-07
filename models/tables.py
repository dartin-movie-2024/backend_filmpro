from db_model import dbConnect

conn = dbConnect()
cursor = conn.cursor()


print("Connected to the database.")
# #  -- Create the Master_ProductionTypes table
# create_table_query = '''
# CREATE TABLE Master_ProductionTypes (
#     Production_Type_Id INT PRIMARY KEY IDENTITY(1,1),
#     Production_Type VARCHAR(255) UNIQUE,
#     Record_Status BIT DEFAULT 1,
#     Created_on DATETIME DEFAULT GETDATE()
# );
#     '''
#
# cursor.execute(create_table_query)
# conn.commit()
#
#
# #  -- Create the Tbl_Productions table with a foreign key reference to Master_ProductionTypes
# create_table_query = '''
# CREATE TABLE Tbl_Productions (
#     Production_id INT PRIMARY KEY IDENTITY(1,1),
#     Production_Name VARCHAR(255) UNIQUE,
#     Production_Type_Id INT,
#     Image_Path VARCHAR(255),
#     Record_Status BIT DEFAULT 1,
#     Created_at DATETIME DEFAULT GETDATE(),
#     Modify_at TIMESTAMP,
#     FOREIGN KEY (Production_Type_Id) REFERENCES Master_ProductionTypes(Production_Type_Id)
# );    '''
#
# cursor.execute(create_table_query)
# conn.commit()

# create_table_query = """INSERT INTO Master_ProductionTypes (Production_Type, Record_Status)
# VALUES ('Movie', 1);
#
# INSERT INTO Master_ProductionTypes (Production_Type, Record_Status)
# VALUES ('TV Show', 1);"""
#

# query = """
# INSERT INTO Tbl_Productions (Production_Name, Production_Type_Id, Image_Path, Record_Status)
# VALUES ('Avengers: Endgame', 3, 'avengers.jpg', 1);
#
# INSERT INTO Tbl_Productions (Production_Name, Production_Type_Id, Image_Path, Record_Status)
# VALUES ('Stranger Things', 4, 'stranger_things.jpg', 1);
#
# """

# query = """
# CREATE TABLE Tbl_App_Users (
#     User_id INT PRIMARY KEY IDENTITY(1,1),
#     User_Name VARCHAR(255) UNIQUE,
#     Password VARCHAR(255), -- You should store encrypted passwords securely
#     Full_Name VARCHAR(255),
#     Mobile_No VARCHAR(15) UNIQUE,
#     Email_Id VARCHAR(255) UNIQUE,
#     Account_Source VARCHAR(20), -- Assuming maximum length is 20 characters
#     Designation VARCHAR(20), -- Assuming maximum length is 20 characters
#     User_Status BIT,
#     Record_Status CHAR(1) CHECK (Record_Status IN ('D', 'Y', 'N')),
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_by INT
# );
#
# """
# cursor.execute(query)
# conn.commit()
#
# # -- Inserting a new user into the Tbl_App_Users table
# Admin/Director/Asst. Director
# query = """
# INSERT INTO Tbl_App_Users (User_Name, Password, Full_Name, Mobile_No, Email_Id, Account_Source, Designation, User_Status, Record_Status, Created_by)
# VALUES ('kumar', 'test123', 'Kumar', '1234567892', 'test2@email.com', 'Signup', 'Asst Director', 1, 'Y', 1);
# """
#
# cursor.execute(query)
# conn.commit()
# -- Create the Master_Departments table
# -- Create the Master_Sub_Departments table
# -- Create the Master_Designations table
# query = """
# CREATE TABLE Master_Departments (
#     Department_Id INT PRIMARY KEY IDENTITY(1,1),
#     Production_id INT REFERENCES Tbl_Productions(Production_id),
#     Department_Name VARCHAR(255),
#     Department_Type VARCHAR(255),
#     Total_Members INT,
#     Record_Status BIT,
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP
# );
#
# CREATE TABLE Master_Sub_Departments (
#     SubDepartment_Id INT PRIMARY KEY IDENTITY(1,1),
#     Production_id INT REFERENCES Tbl_Productions(Production_id),
#     Department_Id INT REFERENCES Master_Departments(Department_Id),
#     SubDepartment_Name VARCHAR(255),
#     Total_Members INT,
#     Record_Status BIT,
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP
# );
# CREATE TABLE Master_Designations (
#     Designation_Id INT PRIMARY KEY IDENTITY(1,1),
#     Department_Id INT REFERENCES Master_Departments(Department_Id),
#     SubDepartment_Id INT REFERENCES Master_Sub_Departments(SubDepartment_Id),
#     Designation_Name VARCHAR(255),
#     Record_Status BIT,
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP
# );
#
# """
# -- Inserting data into the Master_Departments table
# -- You can add more rows as needed
# -- Inserting data into the Master_Sub_Departments table
# -- You can add more rows as needed
# -- Inserting data into the Master_Designations table
# -- You can add more rows as needed
# query = """
#
# INSERT INTO Master_Departments (Production_id, Department_Name, Department_Type, Total_Members, Record_Status)
# VALUES (3, 'Production Department', 'Main', 10, 1);
#
# INSERT INTO Master_Departments (Production_id, Department_Name, Department_Type, Total_Members, Record_Status)
# VALUES (4, 'Post-production', 'Supporting', 8, 1);
#
#
# INSERT INTO Master_Sub_Departments (Production_id, Department_Id, SubDepartment_Name, Total_Members, Record_Status)
# VALUES (3, 1, 'Editing', 5, 1);
#
# INSERT INTO Master_Sub_Departments (Production_id, Department_Id, SubDepartment_Name, Total_Members, Record_Status)
# VALUES (4, 2, 'Sound Mixing', 3, 1);
#
#
# INSERT INTO Master_Designations (Department_Id, SubDepartment_Id, Designation_Name, Record_Status)
# VALUES (3, 1, 'Editor', 1);
#
# INSERT INTO Master_Designations (Department_Id, SubDepartment_Id, Designation_Name, Record_Status)
# VALUES (4, 1, 'Assistant Editor', 1);
#
#
#
#
#
#
# """
# -- Create the Tbl_Crew_Info table
# -- Create the Tbl_Crew_Account_Details table
# -- Create the Tbl_Crew_User_Rights table
# query = """
#
# CREATE TABLE Tbl_Crew_Info (
#     Crew_Id INT PRIMARY KEY IDENTITY(1,1),
#     Production_id INT REFERENCES Tbl_Productions(Production_id),
#     Department_Id INT REFERENCES Master_Departments(Department_Id),
#     SubDepartment_Id INT REFERENCES Master_Sub_Departments(SubDepartment_Id),
#     Designation_Id INT REFERENCES Master_Designations(Designation_Id),
#     Crew_Name VARCHAR(255),
#     Gender VARCHAR(10),
#     Reporting_Crew_Id INT,
#     Date_Of_Birth DATE,
#     Date_of_join DATE,
#     Band VARCHAR(255),
#     Grade VARCHAR(255),
#     Mobile_No VARCHAR(15),
#     Contact_No VARCHAR(15),
#     Email_Id VARCHAR(255),
#     Address VARCHAR(255),
#     Photo_Path VARCHAR(255),
#     Qualification VARCHAR(255),
#     Languages_Known VARCHAR(255),
#     Special_Skills VARCHAR(255),
#     Previous_Exp VARCHAR(255),
#     Is_verified BIT,
#     Record_Status BIT,
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT,
#     Last_Updated_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Last_Updated_By INT
# );
#
#
# CREATE TABLE Tbl_Scene_characters (
#     Scene_Character_Id INT IDENTITY(1,1) PRIMARY KEY,
#     Production_id INT,
#     Scene_Id INT,
#     Character_id INT,
#     Script_pages VARCHAR(255),
#     Features_Required VARCHAR(255),
#     No_Of_Scenes INT,
#     Shoot_Time_Minutes INT,
#     Screen_Time_Minutes INT,
#     Status VARCHAR(255),
#     Assigned_To INT,
#     Assigned_date TIMESTAMP,
#     Record_Status VARCHAR(255),
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );

# CREATE TABLE Tbl_Character_Actor_Dates (
#     Date_id INT PRIMARY KEY IDENTITY(1,1),
#     Scene_Character_Id INT REFERENCES Tbl_Scene_characters(Scene_Character_Id),
#     Estimated_Time VARCHAR(255), -- Adjust the length as needed
#     Criticality VARCHAR(255), -- Adjust the length as needed
#     From_date DATE,
#     To_date DATE,
#     Flexible VARCHAR(255), -- Adjust the length as needed
#     More_dates INT,
#     Extra_from_date DATE,
#     Extra_to_date DATE,
#     Sent_Update VARCHAR(255), -- Adjust the length as needed
#     Record_Status VARCHAR(255), -- Adjust the length as needed
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );

# -- Create the Master_Character table in Microsoft SQL Server
# CREATE TABLE Master_Character (
#     Character_id INT IDENTITY(1,1) PRIMARY KEY,
#     Character_Name VARCHAR(255),
#     Character_Type VARCHAR(255),
#     Full_Name VARCHAR(255),
#     Mobile_No1 VARCHAR(20),
#     Mobile_No2 VARCHAR(20),
#     Email_Id VARCHAR(255),
#     Height VARCHAR(10),
#     Weight VARCHAR(10),
#     Acting_Age INT,
#     Actual_Age INT,
#     Date_Of_Birth DATE,
#     Gender VARCHAR(10),
#     Description TEXT,
#     Hair_colour VARCHAR(50),
#     Eye_Colour VARCHAR(50),
#     Athlethics VARCHAR(255),
#     Arts VARCHAR(255),
#     Music VARCHAR(255),
#     Dance VARCHAR(255),
#     Key_Features TEXT,
#     Photo_Path1 VARCHAR(255),
#     Photo_Path2 VARCHAR(255),
#     Photo_Path3 VARCHAR(255),
#     Address VARCHAR(255),
#     Area VARCHAR(255),
#     State VARCHAR(255),
#     Country VARCHAR(255),
#     Film_Exp VARCHAR(255),
#     Roles_Played TEXT,
#     Films_Played TEXT,
#     Status VARCHAR(255),
#     Submitted VARCHAR(255), -- You may want to specify a length for this column
#     Assigned_To INT,
#     Assigned_date TIMESTAMP,
#     Record_Status BIT, -- Using BIT data type for boolean (0 or 1)
#     Created_on DATETIME DEFAULT GETDATE(),
#     Created_By INT
# );
# CREATE TABLE Tbl_Script_Uploads (
#     Script_Id INT PRIMARY KEY IDENTITY(1,1),
#     Production_id INT REFERENCES Tbl_Productions(Production_id),
#     Script_Name VARCHAR(255), -- Adjust the length as needed
#     No_of_Pages INT,
#     Script_Upload_Path VARCHAR(255), -- Adjust the length as needed
#     Script_Description TEXT,
#     Record_Status VARCHAR(255), -- Adjust the length as needed
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );
# CREATE TABLE Tbl_Scene_details (
#     Scene_Id INT PRIMARY KEY IDENTITY(1,1),
#     Production_id INT REFERENCES Tbl_Productions(Production_id),
#     Script_Id INT REFERENCES Tbl_Script_Uploads(Script_Id),
#     Scene_Type VARCHAR(255), -- Adjust the length as needed
#     Scene_day_condition VARCHAR(255), -- Adjust the length as needed
#     Script_Pages VARCHAR(255), -- Adjust the length as needed
#     Scene_Location VARCHAR(255), -- Adjust the length as needed
#     Shoot_Location VARCHAR(255), -- Adjust the length as needed
#     Scene_time DATETIME,
#     Shoot_Time DATETIME,
#     Short_description VARCHAR(255), -- Adjust the length as needed
#     Status VARCHAR(255), -- Adjust the length as needed
#     Assigned_To INT,
#     Assigned_date TIMESTAMP,
#     Record_Status VARCHAR(255), -- Adjust the length as needed
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );
# CREATE TABLE Tbl_Scene_Stunts (
#     Id INT PRIMARY KEY IDENTITY(1,1),
#     Scene_Id INT REFERENCES Tbl_Scene_details(Scene_Id),
#     Stunt_Details VARCHAR(255), -- Adjust the length as needed
#     Description VARCHAR(255), -- Adjust the length as needed
#     Record_Status BIT, -- BIT data type for Boolean values (0 or 1)
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );
#
# CREATE TABLE Tbl_Scene_Costumes (
#     Id INT PRIMARY KEY IDENTITY(1,1),
#     Scene_Id INT REFERENCES Tbl_Scene_details(Scene_Id),
#     Costume VARCHAR(255), -- Adjust the length as needed
#     Description VARCHAR(255), -- Adjust the length as needed
#     Record_Status BIT, -- BIT data type for Boolean values (0 or 1)
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );
# CREATE TABLE Tbl_Scene_Art (
#     Id INT IDENTITY(1,1) PRIMARY KEY,
#     Scene_Id INT REFERENCES Tbl_Scene_details(Scene_Id),
#     Makeup_Required VARCHAR(255), -- You can specify the maximum length as needed
#     Description VARCHAR(255), -- You can specify the maximum length as needed
#     Record_Status BIT,
#     Created_on DATETIME,
#     Created_By INT
# );

# CREATE TABLE Tbl_Scene_Makeup (
#     Id INT IDENTITY(1,1) PRIMARY KEY,
#     Scene_Id INT REFERENCES Tbl_Scene_details(Scene_Id),
#     Makeup_Required VARCHAR(255), -- Adjust the length as needed
#     Description VARCHAR(255), -- Adjust the length as needed
#     Record_Status BIT, -- BIT data type for Boolean values (0 or 1)
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );



query = """
CREATE TABLE Tbl_Crew_Account_Details (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Crew_Id INT REFERENCES Tbl_Crew_Info(Crew_Id),
    Account_Number VARCHAR(20),
    Bank_Name VARCHAR(255),
    IFSC_Code VARCHAR(11),
    PAN_Number VARCHAR(10),
    Payment_type VARCHAR(255),
    Bank_Cheque_Path VARCHAR(255),
    Record_Status BIT,
    Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    Created_By INT,
    Last_Updated_on DATETIME,
    Last_Updated_By INT
);
"""


# cursor.execute(query)
# conn.commit()
#
# select * from Master_Locations
#
#
#
# Master_Locations
# Tbl_Scene_Locations
# Tbl_Scene_Special_Requirements
#
#
#
#
# CREATE TABLE Master_Locations (
#     id INT IDENTITY(1,1) PRIMARY KEY,
#     Location_Id INT REFERENCES Tbl_Scene_Locations(Location_Id),
#     Location_Name VARCHAR(255), -- You can specify the maximum length as needed
#     Location_Type VARCHAR(255), -- You can specify the maximum length as needed
#     Category VARCHAR(255), -- You can specify the maximum length as needed
#     Specification VARCHAR(255), -- You can specify the maximum length as needed
#     Area VARCHAR(255), -- You can specify the maximum length as needed
#     State VARCHAR(255), -- You can specify the maximum length as needed
#     Country VARCHAR(255), -- You can specify the maximum length as needed
#     Location_Description VARCHAR(255), -- You can specify the maximum length as needed
#     Owner_details VARCHAR(255), -- You can specify the maximum length as needed
#     Permissions VARCHAR(255), -- You can specify the maximum length as needed
#     Previous_Films VARCHAR(255), -- You can specify the maximum length as needed
#     Budget_day VARCHAR(255), -- You can specify the maximum length as needed
#     Budget_Night VARCHAR(255), -- You can specify the maximum length as needed
#     Photo_Path1 VARCHAR(255), -- You can specify the maximum length as needed
#     Photo_Path2 VARCHAR(255), -- You can specify the maximum length as needed
#     Photo_Path3 VARCHAR(255), -- You can specify the maximum length as needed
#     Photo_Path4 VARCHAR(255), -- You can specify the maximum length as needed
#     Photo_Path5 VARCHAR(255), -- You can specify the maximum length as needed
#     Status VARCHAR(255), -- You can specify the maximum length as needed
#     Assigned_To INT,
#     Assigned_date TIMESTAMP,
#     Record_Status VARCHAR(255), -- You can specify the maximum length as needed
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );
#
#
#
# CREATE TABLE Tbl_Scene_Locations (
#     id INT PRIMARY KEY IDENTITY(1,1),
#     Scene_Location_Id INT REFERENCES Tbl_Scene_Special_Requirements(Scene_Location_Id),
#     Production_id INT REFERENCES Tbl_Productions(Production_id),
#     Scene_Id INT REFERENCES Tbl_Scene_details(Scene_Id),
#     Location_Id INT REFERENCES Master_Locations(Location_Id),
#     Special_requirements VARCHAR(255), -- Adjust the length as needed
#     AD_Instructions VARCHAR(255), -- Adjust the length as needed
#     No_Of_Scenes INT,
#     Shoot_Time_Minutes INT,
#     Screen_Time_Minutes INT,
#     Status VARCHAR(255), -- Adjust the length as needed
#     Assigned_To INT,
#     Assigned_date TIMESTAMP,
#     Record_Status BIT, -- BIT data type for Boolean values (0 or 1)
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );
#
#
# CREATE TABLE Tbl_Scene_Special_Requirements (
#     Requirement_Id INT PRIMARY KEY IDENTITY(1,1),
#     Scene_Location_Id INT REFERENCES Tbl_Scene_Locations(Scene_Location_Id),
#     Requirement VARCHAR(255), -- Adjust the length as needed
#     Priority VARCHAR(255), -- Adjust the length as needed
#     Record_Status VARCHAR(255), -- Adjust the length as needed
#     Record_Status_Bool BIT, -- BIT data type for Boolean values (0 or 1)
#     Created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
#     Created_By INT
# );
#
# select * from Tbl_Scene_Locations