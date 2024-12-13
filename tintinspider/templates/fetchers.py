import time

from selenium.webdriver.common.by import By

from tintinspider.fetchers import SeleniumFetcher


class ToyFetcher(SeleniumFetcher):

    def fetch_with_custom(self, url, k):
        # Write your custom script to fetch a list of htmls
        # htmls = ....
        # return htmls
        pass

# ... more custom fetchers    