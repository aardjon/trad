from data_module import PostData, PageData
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

def parse_user_name(user_as_string):
    result = re.search(r"^(.*?)((\|\|\|)|(\|.*?\|\|\|))(.*)$", user_as_string)
    if len(result.groups()) != 5:
        raise Exception("User name could not be parsed")
    
    user_name = result.group(1)
    post_date = datetime.strptime(result.group(5), "%d.%m.%Y %H:%M")
    
    return user_name, post_date   

def parse_rating(rating_as_string):
    rating_map = {
        "--- (Kamikaze)": -3,
        "-- (sehr schlecht)": -2,
        "- (schlecht)": -1,
        "+++ (Herausragend)": 3,
        "++ (sehr gut)": 2,
        "+ (gut)": 1
    }

    return rating_map.get(rating_as_string, 0)

def parse_posts(post_table):    
    result = []
    for i in range(1, len(post_table)):
        result.append(parse_post(post_table.loc[i]))
    return result

def parse_post(post): 
    user = parse_user_name(post[0])
    comment = post[1]
    rating = parse_rating(post[2])
    return PostData(user[0], user[1], comment, rating)  

def parse_page(page_text):
    soup = BeautifulSoup(page_text, "html.parser")

    title_result = re.search(r"(.*) - (.*)", soup.title.string)

    if len(title_result.groups()) != 2:
        raise Exception("Page has no valid title.")
    
    peak = title_result.group(1)
    route = title_result.group(2)

    paragraphs = soup.find('p').getText()
    grade_result = re.search(r".*?\[(.*?)\].*", paragraphs)
    if len(grade_result.groups()) != 1:
        raise Exception("Page has no valid grade.")
    
    grade = grade_result.group(1).strip()

    df_list = pd.read_html(page_text.replace('<br>','|')) # this parses all the tables in webpages to a list
    df = df_list[3]
    posts = parse_posts(df)
    return PageData(peak, route, grade, posts)   