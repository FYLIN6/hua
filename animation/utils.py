import json
from pathlib import Path
import time
from datetime import  datetime

# general constants
SCREENSIZE = WIDTH, HEIGHT = 1000, 600

# define some colors
BLACK = (0, 0, 0)
GREY = (160, 160, 160)
YELLOW = (255, 255, 0)
RED = (242, 47, 47)
GREEN = (93, 242, 98)
ROSE = (94, 11, 21)
SAND = (252, 186, 3)
ORANGE = (235, 128, 52)
PURPLE = (133, 50, 168)
DARK_PURPLE = (63, 40, 66)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
SEAGREEN = (46, 139, 87)
LightGREY = (211, 211, 211)
DimGREY = (105, 105, 105)


def load_input_files():
    """
    Load all json files except obstacle.json
    """
    data = []
    target_dir = Path(__file__).parent / "InputFiles/"
    json_files = [str(pp) for pp in target_dir.glob("**/*.json")]
    for each in json_files:
        if not each.endswith("obstacle.json") and not each.endswith("area.json"):
            with open(each, "r", encoding='utf-8-sig') as f:
                data.append(json.load(f))
    return data

def load_obstacle_file():
    """
    Load obstacle.json
    """
    data = []
    target_dir = Path(__file__).parent / "InputFiles/obstacle.json"
    with open(target_dir) as f:
        data.append(json.load(f))

    return data

def load_area_file():
    """
    Load area.json
    """
    data =[]
    target_dir = Path(__file__).parent / "InputFiles/area.json"
    with open(target_dir) as f:
        data.append(json.load(f))

    return data

def get_font_path(type="Regular"):
    """
    Load fonts for text display
    """
    target_dir = Path(__file__).parent / "Fonts/"
    fonts = [str(pp) for pp in target_dir.glob("**/*.ttf")]
    
    for each in fonts:
        if each.endswith(type+".ttf"):
            return each
    
    return get_font_path() 

# deprecated
def get_t0():
    """
    Get earliest time across all movers
    """
    t0 = 1800000000 # arbitrary time many years later
    data = load_input_files()
    for each in data:
        t = datetime_to_timestamp(each['start_time'])
        if t < t0: t0 = t
    return t0

# deprecated
def get_tf():
    """
    Get latest time across all movers
    """
    tf = 0 # arbitrary time many years later
    data = load_input_files()
    for each in data:
        t = datetime_to_timestamp(each['end_time'])
        if t > tf: tf = t
    return tf

def datetime_to_timestamp(datetime_str="2022-01-01 00:05:00"):
    """
    Convert datetime string to unix time

    @param datetime_str: Datetime string
    """
    try:
        return time.mktime(datetime.strptime(datetime_str,"%Y-%m-%d %H:%M:%S").timetuple())
    except:
        s = "2022" + datetime_str[4:]
        return time.mktime(datetime.strptime(s,"%Y-%m-%d %H:%M:%S").timetuple())



if __name__ == "__main__":
    t1 = datetime_to_timestamp()
    t2 = datetime_to_timestamp("2022-01-01 00:05:30")
    print(t2-t1)
    