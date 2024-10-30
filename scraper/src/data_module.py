from dataclasses import dataclass
from datetime import datetime

@dataclass
class PostData():    
    user_name: str
    post_date: datetime
    comment: str
    rating: int

@dataclass
class PageData():
    peak: str
    route: str
    grade: str
    posts: list[PostData]