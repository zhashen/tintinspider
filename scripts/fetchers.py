import time

from selenium.webdriver.common.by import By

from tintinspider.fetchers import SeleniumFetcher


class CentanetFetcher(SeleniumFetcher):

    def fetch_with_custom(self, url, k):
        tries = 0
        result = []
        while tries < self.max_tries:
            try:
                self.driver.get(url)
                self.driver.maximize_window()
                # Select latest listings
                time.sleep(1)
                self.driver.find_element(By.XPATH, "//i[@class='el-icon-caret-bottom']").click()
                time.sleep(1)
                self.driver.find_element(By.XPATH, "//ul[starts-with(@id, 'dropdown-menu') and contains(@x-placement, 'bottom-start')]/li[2]").click()
                time.sleep(1)
                # Pagination
                for _ in range(k):
                    result.append(self.driver.page_source)
                    self.driver.find_element(By.XPATH, "//button[@class='btn-next']").click()
                    time.sleep(3)
                break
            except Exception as e:
                print(str(e))
                tries += 1
                time.sleep(self.retry_delay)
        try:        
            return result
        except:
            return None