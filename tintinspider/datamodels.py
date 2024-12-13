from abc import ABC
from typing import Optional, List

from pydantic import BaseModel


class Site(BaseModel):
    code               : str
    name               : str
    homepage           : str
    priority           : int = 1  # the higher the more important. 0 means not to crawl
    root_curls         : List[str] = []        # category urls
    root_curls_nopages : List[str] = []       # category urls without pagination
    rule_pagination    : str       = 'single'  # single, next_btn, next_url, scroll. can extend more sub types
    clk_xpath          : str       = ''        # xpath for clicking next page
    revisit_freq       : int       = 86400     # seconds
    revisit_maxpages   : int       = 5         # max category subpages to revisit
    first_maxpages     : int       = 50
    regex_iurls        : List[str] = []        # regex for article urls
    last_visited       : str       = ''


class ItemUrl(BaseModel):
    url          : str
    site_code    : str
    status       : int = 0  # 0: new, 1: visited, 2: error
    crawled_time : str = ''


class CategoryUrl(BaseModel):
    url       : str
    site_code : str
    status    : int = 0  # 0: new, 1: visited, 2: error


class Item(BaseModel):
    url       : str
    site_code : str
    html      : str
    status    : int = 0  # 0: new, 1: processed