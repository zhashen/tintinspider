from datetime import datetime
from importlib import resources
import os
import pandas as pd
import random
import shutil
import time

import tintinspider
from tintinspider.datamodels import *
from tintinspider import db
from tintinspider.fetchers import SeleniumFetcher
from tintinspider.rules import *
from tintinspider.spiders import MultiThreadSpider


def create_project(name, where):
    if where == '.':
        where = os.getcwd()
    path = os.path.join(where, name)
    if os.path.exists(path):
        raise Exception(f"Folder {path} already exists")
    # Create project structure
    os.makedirs(path)
    # copy every file from templates folder to project folder
    with resources.path(tintinspider, 'templates') as source_folder_path:
        for file_name in os.listdir(source_folder_path):
            source_path = os.path.join(source_folder_path, file_name)
            destination_path = os.path.join(path, file_name)
            if os.path.isfile(source_path):
                shutil.copy(source_path, destination_path)


class Controller:
    
    def __init__(self, config, fetchers: dict = {}):
        # TODO: use pydantic to enforce type check
        self.config = config
        self.db = db.MongodbObject(config['mongodb'])
        self.fetchers = {
            'default': SeleniumFetcher(    
                driver_path = config['selenium']['driver_path'],
                user_agent  = config['selenium']['user_agent'],
                proxy       = None,
                headless    = True,
            )
        }
        self.fetchers.update(fetchers)
    

    def add_site(self, site_info):
        site = Site(**site_info)
        self.db.coll_sites().update_one({'code': site.code}, {'$set': site.dict()}, upsert=True)


    def start_generating_iurls(self):
        while True:
            # 1. Iterate through all sites, either generating item urls, or generating category urls which will be used to generate item urls
            sites = [Site(**site) for site in self.db.coll_sites().find({}, {'_id': 0})]
            sites = sorted(sites, key=lambda site: site.priority, reverse=True)
            for site in sites:
                if site.priority == 0:  # inactive site
                    continue
                if site.last_visited == '':
                    is_first_time = True
                else:
                    is_first_time = False
                    now = datetime.now().timestamp()
                    last_visisted_ts = datetime.strptime(site.last_visited, '%Y-%m-%d %H:%M:%S').timestamp()
                    if now - last_visisted_ts < site.revisit_freq:
                        continue
                # Pagination is done via visiting sub page urls, e.g. /page/2, /page-2, ...
                curls_obj = self._gen_curls_for_site(site, is_first_time)
                for co in curls_obj:
                    self.db.coll_curls().update_many({'url': co.url}, {'$set': co.dict()}, upsert=True)
                site.last_visited = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
                self.db.coll_sites().update_one({'code': site.code}, {'$set': {'last_visited': site.last_visited}})
                # Pagination is done via scrolling or clicking. Generate iurls directly
                n_new_iurls = 0
                iurls = []
                # TODO: refactor the following by avoiding if-else branch
                if site.rule_pagination == 'scroll':
                    for curl in site.root_curls:
                        iurls = self.gen_iurls_by_scrolling(site, is_first_time, curl)
                        self._process_iurls_from_curl(iurls, curl, site)
                elif site.rule_pagination == 'click':
                    for curl in site.root_curls:
                        iurls = self.gen_iurls_by_clicking(site, is_first_time, curl, site.clk_xpath)
                        self._process_iurls_from_curl(iurls, curl, site)
                elif site.rule_pagination == 'custom':
                    for curl in site.root_curls:
                        iurls = self.gen_iurls_by_custom(site, is_first_time, curl)
                        self._process_iurls_from_curl(iurls, curl, site)


            # 2. Crawl category urls to generate item urls
            # TODO: 1. use spider for multi-threading; 2. handle priority
            curls_obj = [CategoryUrl(**co) for co in self.db.coll_curls().find({'status': 0}, {'_id': 0})]
            default_fetcher = self.fetchers['default']
            for co in curls_obj:
                try:
                    site = Site(**(self.db.coll_sites().find_one({'code': co.site_code}, {'_id': 0})))
                    curl = co.url
                    html = default_fetcher.fetch(curl)
                    time.sleep(0.2)
                    # Add new Item URLs
                    next_urls = default_fetcher.extract_next_urls(html, curl)
                    iurls = rule_extract_iurls(next_urls, site.regex_iurls)
                    n_new_iurls = 0
                    for iurl in iurls:
                        if self.db.coll_iurls().find_one({'url': iurl}) is None:
                            self.db.coll_iurls().insert_one(ItemUrl(url=iurl, site_code=site.code, status=0).dict())
                            n_new_iurls += 1
                    # Done with current Category URL
                    co.status = 1
                    self.db.coll_curls().update_one({'url': co.url}, {'$set': {'status': co.status}})
                    print(f'Done: new article urls: {n_new_iurls}, category url: {co.url}, type: next_url')
                except:
                    continue

    def start_crawling_iurls(self, n_workers=2, site_code=None):
        # Clean status 2 to 0
        self.db.coll_iurls().update_many({'status': 2}, {'$set': {'status': 0}})
        if site_code is not None:
            urls_todo = [ItemUrl(**item) for item in self.db.coll_iurls().find({'status': 0, 'site_code': site_code}, {'_id': 0})]
        else:
            urls_todo = [ItemUrl(**item) for item in self.db.coll_iurls().find({'status': 0}, {'_id': 0})]
        random.shuffle(urls_todo)
        spider = MultiThreadSpider(self.config)
        spider.set_crawl_sleep(0.2)
        spider.set_queue_urls(urls_todo)
        spider.start(n_workers)


    def _gen_curls_for_site(self, site: Site, is_first_time: bool) -> Optional[List[CategoryUrl]]:
        r_curls = site.root_curls_nopages
        # Get curls from pagination
        if site.rule_pagination not in ['scroll', 'click', 'custom']:
            if len(site.root_curls) > 0:
                func_pagination = f'rule_pagination_{site.rule_pagination}'
                func = globals()[func_pagination]
                curls = func(site, is_first_time)
            else:
                curls = []
            r_curls += curls
        result = []
        for curl in r_curls:
            result.append(CategoryUrl(url=curl, site_code=site.code, status=0))
        return result
    

    def gen_iurls_by_scrolling(self, site: Site, is_first_time: bool, curl: str):
        max_pages = site.first_maxpages if is_first_time is True else site.revisit_maxpages
        html = self.fetchers['default'].fetch_with_scrolling(curl, max_pages)
        next_urls = self.fetchers['default'].extract_next_urls(html, curl)
        iurls = rule_extract_iurls(next_urls, site.regex_iurls)
        return iurls
    

    def gen_iurls_by_clicking(self, site: Site, is_first_time: bool, curl: str, clk_xpath: str):
        max_pages = site.first_maxpages if is_first_time is True else site.revisit_maxpages
        html = self.fetchers['default'].fetch_with_clkbtn(curl, clk_xpath, max_pages)
        next_urls = self.fetchers['default'].extract_next_urls(html, curl)
        iurls = rule_extract_iurls(next_urls, site.regex_iurls)
        return iurls


    def gen_iurls_by_custom(self, site: Site, is_first_time: bool, curl: str):
        max_pages = site.first_maxpages if is_first_time is True else site.revisit_maxpages
        fetcher = self.fetchers[site.code] if self.fetchers.get(site.code) is not None else self.fetchers['default']
        htmls = fetcher.fetch_with_custom(curl, max_pages)
        result = []
        for html in htmls:
            next_urls = fetcher.extract_next_urls(html, curl)
            result.extend(next_urls)
        iurls = rule_extract_iurls(result, site.regex_iurls)
        return iurls


    def _process_iurls_from_curl(self, iurls, curl, site):
        n_new_iurls = 0
        if len(iurls) > 0:
            for iurl in iurls:
                if self.db.coll_iurls().find_one({'url': iurl}) is None:
                    self.db.coll_iurls().insert_one(ItemUrl(url=iurl, site_code=site.code, status=0).dict())
                    n_new_iurls += 1
            print(f'Done: new item urls: {n_new_iurls}, category url: {curl}')
    

    def stat_iurls(self):
        # Show for each site: total, done, todo
        stats = [
            item for item in 
            self.db.coll_iurls().aggregate([
            {
                '$group': {
                    '_id': '$site_code',
                    'total': {'$sum': 1},
                    'done': {'$sum': {'$cond': [{'$eq': ['$status', 1]}, 1, 0]}},
                    'todo': {'$sum': {'$cond': [{'$eq': ['$status', 0]}, 1, 0]}},
                }
            }])
        ]
        df_stats = pd.DataFrame(stats)
        df_stats = df_stats.sort_values(by='total', ascending=False)
        # Add a total row
        df_stats.loc['Total'] = df_stats.sum()
        df_stats.loc['Total', '_id'] = 'Total'
        print(df_stats)
    