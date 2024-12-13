## Build a web scraping project
Create a new project by running
```
ttspider create_project --name <project_name> --where <project_path>
```

* Config MongoDB and Selenium in config.py
* Use s1_add_site.ipynb to figure out the regex of item urls, test custom fetcher and add new sites.
* In fetchers.py, implement custom fetchers for each site. In main.py, a dict of fetchers with site codes as keys and custom fetcher objects as values will be passed to controller. E.g.
```
class ToyFetcher(SeleniumFetcher):

    def fetch_with_custom(self, url, k):
        # Write your custom script to fetch a list of htmls
        # htmls = ....
        # return htmls
        pass

# ... more custom fetchers    

fetchers = {
    'toy': ToyFetcher
}
    

```

* Start generating item urls
```
python main.py gen_iurls
```

* Start crawling item urls
```
python main.py crawl_iurls --n_workers 5
```

## Init MongoDB
In config.py, configure mongodb server, database name and the 4 collection names
```
"mongodb": {
    "server": "mongodb://localhost:27017",  # Change this to your mongodb server
    "database": "tintinspider",  # Change this to your mongodb database
    "coll_sites": "crawl_sites",  # List of sites to crawl
    "coll_iurls": "crawl_iurls",  # Store the list of item urls to be crawled
    "coll_curls": "crawl_curls",  # Store the list of category urls to be crawled
    "coll_items": "crawl_items",  # Store the crawled items
}
```

Create the database and 4 collections in DB. Create indices for each collection as follows:
* crawl_iurls: url 
* crawl_curls: url
* crawl_items: url, status

## Add Site
```
site_info = {
    "code" : "",              # Unique site code. Use lower case letter only
    "name" : "",              # Site name
    "homepage" : "",          # Site homepage, optional
    "rule_pagination" : "",   # "next_url_...", "click", "scroll", "custom"
    "clk_xpath" : "",         # if pagination is "click", specify Xpath for "Load more"-kind button
    "first_maxpages" : 3,     # Max pagination for first-time scraping
    "revisit_maxpages" : 3,   # Max pagination for periodic scraping
    "revisit_freq" : 14400,   # Revisit frequency by seconds
    "root_curls" : [          # Entry URLs. Pagniation will be applied to this list of URLs.
    ],
    "root_curls_nopages" : [  # Another set of entry URLs. No pagination. 
    ],
    "regex_iurls" : [         # Specify regex of item URLs
    ],
    "priority" : 1,           # The higher, the more prioritized. 0 means the site is inactive.
}

```

## Tune regex_iurls
In s1_add_site.ipynb, the following code snippet allows you to tune regex_iurls to extract item URLs
```
from tintinspider.rules import rule_extract_iurls

url = '' # url to scrape
regex_iurls = [r'']  # try different regex strings here

def get_item_urls(url, regex_iurls):
    html = fetcher.fetch(url)
    next_urls = fetcher.extract_next_urls(html, url)  # only urls in the same domain
    iurls = rule_extract_iurls(next_urls, regex_iurls)
    print(f'Item URLs: {len(iurls)}')
    print('-'*17)
    print('Top 3 Item URLs are: ')
    for i in range(3):
        print(iurls[i])
```

## Tune custom fetchers
In s1_add_site.ipynb, the following allows you to tune the custom fetcher
```
class YourFetcher(SeleniumFetcher):  # Name your custom fetcher

    def fetch_with_custom(self, url, k):
        pass

fetcher2 = YourFetcher(   # Use your custom fetcher
    driver_path = conf['selenium']['driver_path'],
    user_agent  = conf['selenium']['user_agent'],
    proxy       = None,
    headless    = True,  # False if you want to see the browser
)

url = 'https://hk.centanet.com/findproperty/list/buy'
htmls = fetcher2.fetch_with_custom(url, 3)
print(f'Fetched {len(htmls)} pages')

# Test if you can extract item URLs from the scrapped htmls
iurls = []
for html in htmls:
    u = get_item_urls(html, regex_iurls)
    iurls.extend(u)
print(f'Total {len(iurls)} item URLs')
print('-'*17)
print('Top 3 Item URLs are: ')
for i in range(3):
    print(iurls[i])
```