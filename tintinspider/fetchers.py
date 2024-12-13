from abc import ABC, abstractmethod
import re
import time
from typing import Any, Optional, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class BaseFetcher:
    load_timeout   : int = 5
    render_timeout : int = 3
    max_tries      : int = 3
    retry_delay    : int = 2


    def fetch(self, url: str, **kwargs) -> Optional[str]:
        """ Fetch the url and return the html content """
        pass

    def extract_next_urls(self, html: str, current_url: str) -> Optional[str]:
        """ Extract the next urls from the html content """
        result = []
        soup = BeautifulSoup(html, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a')]
        links = filter(lambda link: link is not None, links)
        links = [urljoin(current_url, link) for link in links]
        domain = current_url.split('/')[2]
        domain = domain.replace('www.', '')
        pattern = re.compile(r'^https?://[a-zA-Z0-9.-]*' + domain+r'.*')
        result = [link for link in links if re.match(pattern, link) is not None]
        result = [link.split('#')[0] for link in result]
        result = [link.split('?')[0] for link in result]
        result = list(set(result))
        return result


    def close(self):
        pass


class SeleniumFetcher(BaseFetcher):
    options     : Any           = None
    service     : Any           = None
    driver      : Any           = None

    def __init__(self, driver_path, user_agent, proxy=None, headless=True):
        options = webdriver.ChromeOptions()
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--silent')
        options.add_argument('--disable-logging')
        options.add_argument("--log-level=3")
        if headless is True:
            options.add_argument('--headless')
        if proxy is not None:
            options.add_argument(f'--proxy-server={proxy}')

        service = Service(driver_path)
        service.start()
        self.driver = webdriver.Chrome(service=service, options=options)


    def fetch(self, url, **kwargs) -> Optional[str]:
        """ Fetch the url and return the html content """
        tries = 0
        while tries < self.max_tries:
            try:
                self.driver.set_page_load_timeout(self.load_timeout) 
                self.driver.get(url)
                self.driver.implicitly_wait(self.render_timeout)
                # self.driver.maximize_window()
                break
            except Exception as e:
                tries += 1
                time.sleep(self.retry_delay)
        try:        
            return self.driver.page_source
        except:
            return None
    

    def _scroll_to_bottom(self):
        ratio = 1
        scroll_height = 2000
        document_height_before = self.driver.execute_script("return document.documentElement.scrollHeight")
        self.driver.execute_script(f"window.scrollTo(0, {int((document_height_before + scroll_height)*0.9)});")
        time.sleep(1)
        document_height_after = self.driver.execute_script("return document.documentElement.scrollHeight")
        time.sleep(1)


    def fetch_with_scrolling(self, url, k, **kwargs) -> Optional[str]:
        """ Scroll down k times and return the html content """
        tries = 0
        while tries < self.max_tries:
            try:
                self.driver.get(url)
                # self.driver.maximize_window()
                # self.driver.implicitly_wait(self.timeout)
                time.sleep(1)
                for _ in range(k):
                    self._scroll_to_bottom()
                break
            except Exception as e:
                tries += 1
                time.sleep(self.retry_delay)
        try:        
            return self.driver.page_source
        except:
            return None
    
    
    def fetch_with_clkbtn(self, url, xpath, k, **kwargs) -> Optional[str]:
        """ Click the button k times (e.g. Load More) and return the html content """
        tries = 0
        while tries < self.max_tries:
            try:
                self.driver.get(url)
                # self.driver.maximize_window()
                # self.driver.implicitly_wait(self.timeout)
                time.sleep(1)
                for _ in range(k):
                    try:
                        self._scroll_to_bottom()
                        self.driver.find_element(By.XPATH, xpath).click()
                        time.sleep(0.5)
                    except:  # perhaps no more next button to click
                        break
                break
            except Exception as e:
                tries += 1
                time.sleep(self.retry_delay)
        try:        
            return self.driver.page_source
        except:
            return None
    

    def fetch_with_custom(self, url, k, **kwargs) -> Optional[List[str]]:
        """ Extend this fetcher, customize your bot and return a list of htmls """
        return []


    def close(self):
        self.driver.close()
        self.driver.quit()