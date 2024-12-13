import json
import re
import time

from bs4 import BeautifulSoup
from lxml import etree
import requests
from tqdm import tqdm

from tintinspider.fetchers import SeleniumFetcher


class BaseProxy:

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def get_proxies(self):
        raise NotImplementedError
    

class ProxyscrapeProxy(BaseProxy):

    def get_proxies(self):
        proxies = []
        try:
            r = requests.get("https://api.proxyscrape.com/v3/free-proxy-list/get?request=getproxies&proxy_format=ipport&format=json")
            data = json.loads(r.text)
            proxies = data['proxies']
            proxies = [f"{item['protocol']}://{item['proxy']}" for item in proxies if item['protocol'] in ['http', 'https'] ]
        except:
            pass
        return proxies


class  ZdayeProxy(BaseProxy):

    def get_proxies(self):
        proxies = []
        cities = ['guangdong']
        for city in cities[:1]:
            try:
                time.sleep(0.5)
                html = self.fetcher.fetch(f'https://www.zdaye.com/free/{city}_ip.html')
                soup = BeautifulSoup(html, 'html.parser')
                root = etree.HTML(str(soup))
                table = root.xpath("//table[@id='ipc']")[0]
                rows = table.xpath(".//tr")
                for row in rows:
                    cells = row.xpath(".//td")
                    try:
                        ip = cells[0].xpath(".//text()")[0]
                        port = cells[1].xpath(".//text()")[0]
                        proxies.append(f"http://{ip}:{port}")
                    except:
                        pass
            except:
                continue
        proxies = list(set(proxies))
        return proxies


class FreeproxylistProxy(BaseProxy):

    def get_proxies(self):
        proxies = []
        try:
            url = 'https://free-proxy-list.net/'
            html = self.fetcher.fetch(url)
            root = etree.HTML(html)
            table = root.xpath('//table[@class="table table-striped table-bordered"]')[0]
            items = table.xpath('.//tbody/tr')
            for item in items:
                values = item.xpath('.//td/text()')
                proxies.append(f'http://{values[0]}:{values[1]}')
        except:
            pass
        return proxies


class KuaidailiProxy(BaseProxy):

    def get_proxies(self):
        proxies = []
        try:
            urls = [f'https://www.kuaidaili.com/free/dps/{i}/' for i in range(1, 11)]
            for url in urls:
                time.sleep(0.5)
                try:
                    html = self.fetcher.fetch(url)
                    root = etree.HTML(html)
                    table = root.xpath('//tbody[@class="kdl-table-tbody"]')[0]
                    items = table.xpath('.//tr')
                    for item in items:
                        values = item.xpath('.//td/text()')
                        proxies.append(f'http://{values[0]}:{values[1]}')
                except:
                    continue
        except:
            pass
        return proxies


def get_proxies(fetcher):
    proxies = []
    p1 = ProxyscrapeProxy(fetcher)
    p2 = ZdayeProxy(fetcher)
    p3 = FreeproxylistProxy(fetcher)
    p4 = KuaidailiProxy(fetcher)
    for p in [p4]:
        proxies.extend(p.get_proxies())
    fetcher.close()
    return proxies