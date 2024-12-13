import argparse
import multiprocessing
import time

from tintinspider.controller import Controller

import config
import fetchers


# Create custom fetchers and bind them to site codes
driver_path = config.config['selenium']['driver_path']
user_agent  = config.config['selenium']['user_agent']
dict_fetchers = {}
dict_fetchers['centanet'] = fetchers.CentanetFetcher(driver_path, user_agent)

if __name__ == '__main__':

    ctrl = Controller(config.config, dict_fetchers)

    parser = argparse.ArgumentParser()
    parser.add_argument(
            'command', 
            choices=[
                    'gen_iurls', 'crawl_iurls', 'stat_iurls',
                ]
        )
    parser.add_argument('--n_workers', type=int)
    parser.add_argument('--site_code', type=str)
    args = parser.parse_args()

    if args.command == 'gen_iurls':
        ctrl.start_generating_iurls()

    elif args.command == 'crawl_iurls':
        n_workers = args.n_workers
        site_code = args.site_code
        if n_workers is None:
            n_workers = 5

        ctrl.start_crawling_iurls(n_workers, site_code)

    elif args.command == 'stat_iurls':
        ctrl.stat_iurls()
