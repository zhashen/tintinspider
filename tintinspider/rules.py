import copy
import re
from typing import List
from urllib.parse import urljoin

from tintinspider.datamodels import Site, CategoryUrl


def rule_extract_iurls(candidate_urls, regex_iurls):
    result = []
    for url in candidate_urls:
        try:
            for regex in regex_iurls:
                if re.match(regex, url) is not None:
                    result.append(url)
                    break
        except:
            continue
    return result


## ------------ Pagination rules ------------
def _common_append_page_number(site: Site, is_first_time: bool, append: str):
    max_pages = site.first_maxpages if is_first_time is True else site.revisit_maxpages
    result = copy.deepcopy(site.root_curls)
    for url in site.root_curls:
        for i in range(2, max_pages + 1):
            url = url[:-1] if url.endswith('/') else url
            curl = url + append.format(i=i)
            result.append(curl)
    return result


# .../page/2
def rule_pagination_next_url_default(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '/page/{i}')
    return result

# ...?page=2
def rule_pagination_next_url_pageqm(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '?page={i}')
    return result

# .../?page=2
def rule_pagination_next_url_slashqm(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '/?page={i}')
    return result

# .../page2.html
def rule_pagination_next_url_pagedothtml(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '/page{i}.html')
    return result

# .../2/
def rule_pagination_next_url_slashnumber(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '/{i}/')
    return result

# .../archives/2
def rule_pagination_next_url_archives(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '/archives/{i}')
    return result

# .../page2
def rule_pagination_next_url_pagenum(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '/page{i}')
    return result

# ...2.html
def rule_pagination_next_url_numhtml(site: Site, is_first_time: bool):
    result = _common_append_page_number(site, is_first_time, '{i}.html')
    return result