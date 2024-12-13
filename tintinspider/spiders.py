from datetime import datetime, timedelta
import queue
import random
import threading
import time

from bs4 import BeautifulSoup
import pymongo

from tintinspider import db as tdb
from tintinspider.fetchers import SeleniumFetcher
import tintinspider.proxy as tproxy
from tintinspider.datamodels import *


def _get_func(module, site_code):
    try:
        func = getattr(module, f'parse_{site_code}')
    except:
        func = getattr(module, 'parse_default')
    return func


class MultiThreadSpider:

    def __init__(self, config):
        self.queue_urls = queue.Queue()
        self.queue_proxies = queue.Queue()
        self.queue_results = queue.Queue()
        self.result_handler = None
        self.crawl_sleep = 0.2
        self.db = tdb.MongodbObject(config['mongodb'])
        self.config = config


    def set_crawl_sleep(self, sleep):
        self.crawl_sleep = sleep


    def set_result_handler(self, handler):
        self.result_handler = handler


    def set_queue_urls(self, urls):
        for url in urls:
            self.queue_urls.put(url)


    def thread_func(self):
        proxy = None
        fetcher = None
        while True:
            if not self.queue_urls.empty():
                iurl = self.queue_urls.get()
            else:
                print('No more urls to crawl')
                return None

            if proxy is None:
                if not self.queue_proxies.empty():
                    proxy = self.queue_proxies.get()
                else:
                    print('No more proxies')
                    return None
            
            if fetcher is None:
                if proxy == 'self':
                    fetcher = SeleniumFetcher(self.config['selenium']['driver_path'], self.config['selenium']['user_agent'], proxy=None)
                else:
                    fetcher = SeleniumFetcher(self.config['selenium']['driver_path'], self.config['selenium']['user_agent'], proxy=proxy) 
            self.db.coll_iurls().update_one({'url': iurl.url}, {'$set': {'status': 2}}) # indicate they are being processed
            html = self.crawl(iurl.url, fetcher)
            time.sleep(self.crawl_sleep)
            if html is None:
                print(f'Failed to crawl: {iurl.url}, proxy: {proxy}')
                self.queue_urls.put(iurl)
                if proxy != 'self':
                    fetcher.close()
                    proxy = None
                    fetcher = None
            else:
                self.queue_results.put((iurl, html, proxy))
    

    def _display_time_delta(self, seconds):
        sec = timedelta(seconds=seconds)
        d = datetime(1,1,1) + sec
        return '{} days, {:02}:{:02}:{:02}'.format(d.day-1, d.hour, d.minute, d.second)


    def _is_proxy_working(self, test_html):
        thres = 3000
        try:
            if len(test_html) > thres:
                return True
            else:
                return False
        except:
            return False


    def crawl(self, url, fetcher):
        html = fetcher.fetch(url)
        if self._is_proxy_working(html) is False:
            return None
        else:
            return html
    

    def start(self, n_workers=2):
        flag_no_more_urls = False
        print(f'urls to crawl: {self.queue_urls.qsize()}')

        while True:
            # Store proxies into a queue
            print('Getting proxies...', )
            fetcher = SeleniumFetcher(self.config['selenium']['driver_path'], self.config['selenium']['user_agent'], proxy=None)
            proxies = tproxy.get_proxies(fetcher)
            print('Done, got', len(proxies), 'proxies.')
            if self.queue_proxies.qsize() == 0:
                self.queue_proxies.put('self')
            for item in proxies:
                self.queue_proxies.put(item)

            # Results are put by threads into a queue
            if self.queue_results is not None:
                while not self.queue_results.empty():
                    self.queue_results.get()
            else:
                self.queue_results = queue.Queue()

            threads = []
            for i in range(n_workers):
                thread = threading.Thread(target=self.thread_func)
                thread.start()
            
            check_freq = 60
            total_done = 0
            total_spent = 0
            while True:
                time.sleep(check_freq)
                # Store crawled results to DB
                done = 0
                dict_proxy_done = {}
                while not self.queue_results.empty():
                    item = self.queue_results.get()
                    iurl = item[0]
                    proxy = item[2]
                    html = item[1]  # here html is certainly not None
                    end_time = datetime.now()
                    # Update article url status
                    self.db.coll_iurls().update_one(
                        {'url': iurl.url}, 
                        {'$set': {'status': 1, 'crawled_time': end_time.strftime('%Y-%m-%d %H:%M:%S')}},
                    )
                    # Store html to Article and also parse it
                    item = Item(url=iurl.url, site_code=iurl.site_code, html=html)
                    soup = BeautifulSoup(item.html, 'html.parser')
                    item.status = 1

                    self.db.coll_items().insert_one(item.dict())
                    dict_proxy_done.setdefault(proxy, 0)
                    dict_proxy_done[proxy] += 1
                    done += 1

                total_done += done
                total_spent += check_freq
                throughput = round(total_done/total_spent, 2) if total_spent > 0 else 0
                efficiency = round(1/throughput, 2) if throughput > 0 else -1
                print('-'*17)
                for proxy in dict_proxy_done.keys():
                    print(f'{proxy}: {dict_proxy_done[proxy]}')
                print('-'*17)
                print(f'Newly done: {done}')
                print(f'Total done: {total_done}')
                print(f'Throughput: {throughput}')
                print(f'Efficiency: {efficiency}')
                n_undone_urls = self.queue_urls.qsize()
                print(f'Proxy Pool: {self.queue_proxies.qsize()}')
                print(f'Undone: {n_undone_urls}')
                eta = int(n_undone_urls/throughput) if throughput > 0 else -1
                if eta > 0:
                    print(f'ETA: {self._display_time_delta(eta)}')
                else:
                    print('ETA: forever...')
                print('-'*17)

                if self.queue_proxies.qsize() == 0:
                    print('No more proxies...')
                    break
                # If too few tasks, add more.
                # Warning: it is possible that some tasks are being processed, so they are not in the queue,
                # and their status are still 0 in DB. This may result in duplicate articles crawled in DB. But
                # the number should be very small. You can deduplicate them in later ETLs.
                if self.queue_urls.qsize() == 0:
                    urls_todo = [ItemUrl(**item) for item in self.db.coll_iurls().find({'status': 0}, {'_id': 0})]
                    random.shuffle(urls_todo)
                    for url in urls_todo:
                        self.queue_urls.put(url)