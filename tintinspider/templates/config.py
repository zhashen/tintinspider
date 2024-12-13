config = {
    "mongodb": {
        "server": "mongodb://localhost:27017",  # Change this to your mongodb server
        "database": "tintinspider",  # Change this to your mongodb database
        "coll_sites": "crawl_sites",  # List of sites to crawl
        "coll_iurls": "crawl_iurls",  # Store the list of item urls to be crawled
        "coll_curls": "crawl_curls",  # Store the list of category urls to be crawled
        "coll_items": "crawl_items",  # Store the crawled items
    },

    "selenium": {
        "driver_path": r"C:\Installers\chromedriver-130-win64\chromedriver.exe",  # Change this to your chromedriver path
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
}