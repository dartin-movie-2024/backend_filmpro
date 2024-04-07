#Import Libraries
import re
import config
import numpy as np
import pandas as pd
# from docx import Document

pd.set_option('display.max_columns', 10000)
pd.set_option('display.max_rows', 10000)


#Functions

def information(path, char_lis):
    df2 = pd.read_csv(path)
    df2['N_charcters'] = df2.Scene_Characters.map(len)
    # print(df2.head(5))
    char_scenes_dict ={}
    for i in char_lis:
        lst= []
        for j in range(1,df2.shape[0]):
            [lst.append(df2['Scene_number'].loc[j]) if i == x else '' for x in (re.sub('[^A-Za-z, ]+', '', df2['Scene_Characters'].loc[j]).split(', '))]
        char_scenes_dict[i] = lst
    loc_list = list(set(df2['Location'].tolist()))
    loc_scenes_dict ={}
    for i in loc_list:
        lst= []
        for j in range(1,df2.shape[0]):
            [lst.append(df2['Scene_number'].loc[j]) if i == df2['Location'].loc[j] else '']
        loc_scenes_dict[i] = lst
    day_list = list(set(df2['Day_Night'].tolist()))
    day_scenes_dict ={}
    for i in day_list:
        lst= []
        for j in range(1,df2.shape[0]):
            [lst.append(df2['Scene_number'].loc[j]) if i == df2['Day_Night'].loc[j] else '']
        day_scenes_dict[i] = lst
    return day_scenes_dict, df2 ,char_scenes_dict, loc_scenes_dict
    

def extract_scene_headings(film_script_txtfile_path):
    # A couple options on regex patterns, depending on script format. Might need tweaks per script
    regexp = r'(((INT\.|EXT\.)\s[A-Z]+.*)|((INT\.|EXT\.)\s+[A-Z]+.*)|((INT\.|EXT\.)\s[A-Z]+)|((INT\.|EXT\.)\s[0-9]+.*)|\
        ((INT\./EXT\.|EXT\./INT\.)\s[A-Z]+.*)|((INT\.|EXT\.)\s[0-9]+)|((INT\./EXT\.|EXT\./INT\.)\s[0-9]+.*)|(INT\.\s+.*|EXT\.\s+.*)\
        |((INT\.|EXT\.)\s[A-Z]+\W+.+)|((INT|EXT)\s[A-Z]+.*)|((INT|EXT)\s+[A-Z]+.*)|((INT|EXT)\s[A-Z]+)|((INT|EXT)\s[0-9]+.*)\
        |((INT/EXT|EXT/INT)\s[A-Z]+.*)|((INT|EXT)\s[0-9]+)|((INT/EXT|EXT/INT)\s[0-9]+.*)|((I/E\.|E/I\.)\s+[A-Z].*)\
        |((INT\.|EXT\.)\s\'\d+\s[A-Z]+.*)|((INT\.|EXT\.)[A-Z]+.*)|((INT|EXT)\s[A-Z]+\W+.+)|((I/E\.|E/I\.)\s+.*))\n'
    

    
    with open(film_script_txtfile_path, "r", encoding='utf-8', errors='ignore') as r:
      film_string = [row for row in r]

    places = [
        re.findall(regexp, line)
        for line in film_string
        if re.findall(regexp, line)
    ]
    
    #print(places)
    return [place[0] for place in places] if places else None
  
  
def ele_upper(list1):
    for i in range(len(list1)):
          list1[i] = list1[i].upper()
    return list1

def my_function(x):
  return list(dict.fromkeys(x))

def extract_scene_characters(filename):
    
    # read the data into a list (each row is one list element)
    with open(filename, "r", encoding='utf-8', errors='ignore') as f:
        data = [row for row in f]
    
    dat = []
    for x in data:
        x = re.sub(r'\(.*\)', '', x)
        x = re.sub(r'\-|\#\d+', '', x)
        #x = re.sub(r"[^a-zA-Z0-9.,?'\n ]+", '', x)
        x = re.sub(r"POINT OF VIEW", 'Point of view', x)
        x = re.sub(r"TEXT", 'Text', x)
        x = re.sub(r"NEXT", 'Next', x)
        dat.append(x.replace('\t', ' ').lstrip(" "))
    
    scenes = []
    for l in dat:
        match = re.search(r'(((INT\.|EXT\.)\s[A-Z]+.*)|((INT\.|EXT\.)\s+[A-Z]+.*)|((INT\.|EXT\.)\s[A-Z]+)|((INT\.|EXT\.)\s[0-9]+.*)|\
        ((INT\./EXT\.|EXT\./INT\.)\s[A-Z]+.*)|((INT\.|EXT\.)\s[0-9]+)|((INT\./EXT\.|EXT\./INT\.)\s[0-9]+.*)|(INT\.\s+.*|EXT\.\s+.*)\
        |((INT\.|EXT\.)\s[A-Z]+\W+.+)|((INT|EXT)\s[A-Z]+.*)|((INT|EXT)\s+[A-Z]+.*)|((INT|EXT)\s[A-Z]+)|((INT|EXT)\s[0-9]+.*)\
        |((INT/EXT|EXT/INT)\s[A-Z]+.*)|((INT|EXT)\s[0-9]+)|((INT/EXT|EXT/INT)\s[0-9]+.*)|((I/E\.|E/I\.)\s+[A-Z].*)\
        |((INT\.|EXT\.)\s\'\d+\s[A-Z]+.*)|((INT\.|EXT\.)[A-Z]+.*)|((INT|EXT)\s[A-Z]+\W+.+)|((I/E\.|E/I\.)\s+.*))\n', l)
        if match:
            scenes.append(match.group(1))
    scenes = [x.strip(" ") for x in scenes]
        
    characters = []
    for x in dat:
        xters = re.findall(r'(^[A-Z]+[A-Z]+\n)|(^[A-Z]+[A-Z]+\s+\n)|(^[A-Z]+\.\s+[A-Z]+\n)|(^[A-Z]+[A-Z]+\s+[A-Z]+[A-Z]+\s\n)\
        |(^[A-Z]+[A-Z]+\s+[A-Z]+[A-Z]+\s+[A-Z]+[A-Z]+\n)|(^[A-Z]+[A-Z]+\s+[A-Z]+[A-Z]+\n)|(^[A-Z]+[A-Z]+\'S\s+[A-Z]+[A-Z]+\s+[A-Z]+[A-Z]+\n)\
        |(^[A-Z]+[A-Z]+\'S\s+[A-Z]+[A-Z]+\n)|(^[A-Z]+[A-Z]+\'S\s+[A-Z]+[A-Z]+\s+\n)|(^MR\s+[A-Z]+[A-Z]+|MRS\s+[A-Z]+[A-Z]+\n)\
        |(^[A-Z]+[A-Z]+\s+\&\s+[A-Z]+[A-Z]+\n)|(^MR\s+[A-Z]+[A-Z]+|MRS\s+[A-Z]+[A-Z]+\s+\n)', x)
        characters.append(xters)
        
    characters = [x for x in characters if x != []]
    refined_characters = []
    for c in characters:
        cc = [tuple(filter(None, i)) for i in c]
        refined_characters.append(cc)
    refined_xters = [x[0][0] for x in refined_characters]
    
    best_ = ['BEST DIRECTOR', 'BEST ADAPTED SCREENPLAY', 'BROADCASTING STATUS', 'BEST COSTUME DESIGN', 'TWENTIETH CENTURY FOX', 'BEST ORIGINAL SCORE', 'BEST ACTOR', 'BEST SUPPORTING ACTOR', 'BEST CINEMATOGRAPHY', 'BEST PRODUCTION DESIGN', 'BEST FILM EDITING', 'BEST SOUND MIXING', 'BEST SOUND EDITING', 'BEST VISUAL EFFECTS']
    transitions = ['RAPID CUT TO:', 'TITLE CARD', 'FINAL SHOOTING SCRIPT', 'CUT TO BLACK', 'CUT TO:', 'SUBTITLE:', 'SMASH TO:', 'BACK TO:', 'FADE OUT:', 'END', 'CUT BACK:', 'CUT BACK', 'DISSOLVE TO:', 'CONTINUED', 'RAPID CUT', 'RAPID CUT TO', 'FADE TO:', \
                   'FADE IN:', 'FADE OUT:', 'FADES TO BLACK', 'FADE TO', 'CUT TO', 'FADE TO BLACK', 'FADE UP:', 'BEAT', 'CONTINUED:', 'FADE IN', \
                   'TO:', 'CLOSE-UP','WIDE ANGLE', 'WIDE ON LANDING', 'THE END', 'FADE OUT','CONTINUED:', 'TITLE:', 'FADE IN','DISSOLVE TO','CUT-TO','CUT TO', 'CUT TO BLACK',\
                   'INTERCUT', 'INSERT','CLOSE UP', 'CLOSE', 'ON THE ROOF', 'BLACK', 'BACK IN SILENCE', 'TIMECUT', 'BACK TO SCENE',\
                   'REVISED', 'PERIOD', 'PROLOGUE', 'TITLE', 'SPLITSCREEN.', 'BLACK.',\
                   'FADE OUT', 'CUT HARD TO:', 'OMITTED', 'DISSOLVE', 'WIDE SHOT', 'NEW ANGLE']
    movie_characters = []
    for x in refined_xters:
        x = re.sub(r'INT\..*|EXT\..*', '', x)
        x = re.sub(r'ANGLE.*', '', x)
        trans = re.compile("({})+".format("|".join(re.escape(c) for c in transitions)))
        x = trans.sub(r'', x)
        best = re.compile("({})+".format("|".join(re.escape(c) for c in best_)))
        x = best.sub(r'', x)
        movie_characters.append(x.replace('\n', '').strip())
    movie_characters = [x.strip() for x in movie_characters if x]
    
    return scenes, movie_characters, dat


def secne_text_extract(file_path, file_name, scene_number):
      
      film_script_txtfile_path=file_path+file_name

      headings = extract_scene_headings(film_script_txtfile_path)
  
      scenes = []
      for i in headings:
        scenes.append(i[0])

      top = scene_number-1
      bottom = scene_number

      with open(film_script_txtfile_path, "r", encoding='utf-8', errors='ignore') as r:
            film_string = [row for row in r]

      scene_text = " ".join(film_string).split(scenes[top])[1].split(scenes[bottom])[0]

      return scene_text


def main_func(file_path, file_name, status=False):
  sc,mc,dat = extract_scene_characters(file_path+file_name)
  characters_list = list( dict.fromkeys(mc))
  a = extract_scene_headings(film_script_txtfile_path=file_path+file_name)
  
  # print(a)
  scenes = []
  for i in a:
    scenes.append(i[0])

  scenes_index = []
  for l in range(len(dat)):
    match = re.search(r'(INT\.|EXT\.).*.', dat[l])
    if match:
      scenes_index.append(l)
  
  scenes_index.sort()
  
  dia_list = []
  for i in range(len(scenes_index)):
    if i == len(scenes_index)-1:
      dia_list.append(dat[scenes_index[i]:-1])
    else:
      dia_list.append(dat[scenes_index[i]:scenes_index[i+1]])
  
  sc_ch1 = []
  for k in dia_list:
    scene_characters = []
    k = ele_upper(k)
    for i in characters_list:
      for j in k:
        if i in j:
          scene_characters.append(i)
    sc_ch1.append(scene_characters)
  
  new = []
  for i in sc_ch1:
    if i != None:
      a = my_function(i)
      new.append(a)
    else:
      new.append(None)

   # create an Empty DataFrame object
  Edf = pd.DataFrame()
  Edf['Location'] = scenes
  scenes_df = Edf.copy()
  df = scenes_df.replace({'Location': {';': '.', '-': '.',':': '.',' – ': '.'}}, regex=True)
  df.index = np.arange(1, len(df)+1)
  df['Scene_number'] = df.index
  df1 = df.copy()
  df1['Internal_External'] = df1['Location'].str.extract('(INT|Int|EXT|Ext)', expand=True)
  df1['Day_Night'] = df1['Location'].str.extract('(DAY|day|Day|Night|NIGHT|MORNING|Morning|Afternoon|AFTERNOON)', expand=True)
  df1['Location'] = df1['Location'].str.split('.').str[1]
  df1['Scene_Characters'] = new
  location_list = df1.Location.unique()

  # return df1, characters_list, location_list
  scenes_names = None
  scene_display_text = None
  script_display_text = None
  return df1, characters_list, location_list, scenes_names, scene_display_text, script_display_text

   

  
    
    
    