import requests
import pickle
from get_full_content import get_bbc_content # get_full_content has bbc, guardian and reuters specific functions that are compatible with their respective sources as taken from newsapi
from pdb import set_trace
import os
import sqlite3 as sq

import datetime


from IPython import get_ipython
ipython = get_ipython()
ipython.magic("reload_ext autoreload")
ipython.magic("autoreload 2")

def find_API_publish_time(db_filename, lag_mins=20):
    """
    Find the time since the last call to NewsAPI, to determine time for news database update

    Parameters
    -------------
    db_filename : A string, the name of the news database
    lag_mins : An int, the number of minutes backwards in time since the newest article that the API should be called from. This is to take into account latency between a story being published on the website and being discoverable on NewsAPI.

    Returns
    ------------

    """

    if os.path.exists(db_filename):
        conn = sq.connect(db_filename)
        c = conn.cursor()
        date_query = '''SELECT publishedAt FROM news
                        ORDER BY publishedAt
                        LIMIT 1
        '''
        c.execute(date_query)
        date_latest = c.fetchall()[0][0]
        conn.close()

        # Subtract lag_mins
        dt_format = "%Y-%m-%dT%H:%M:%S"
        date_latest_dtm = datetime.datetime.strptime(date_latest, dt_format)
        last_published_dtm = date_latest_dtm + datetime.timedelta(minutes=-lag_mins)
        last_published = datetime.datetime.strftime(last_published_dtm,dt_format)
        return last_published
    else:
        raise Exception('News database not found!')



def get_new_results(last_published, page_limit_per_request=10, results_per_page=100): #last published needs an input from the dataframe of the most recent article we have access to
    """
    Query NewsAPI for URLs and metadata

    Parameters
    ---------------

    Returns
    ---------------


    """

    article_dict = {}  # stores articles indexed by URL
    # Iterate over pages - rate limited
    for i in range(page_limit_per_request):
        try:
            if i % 10 == 0:
                print('Accessing page {}'.format(i))
            p = i + 1
            page_str = 'page={}&'.format(p)
            pagesize_str = 'pagesize={}&'.format(results_per_page)
            apikey_str = 'apiKey={}'.format(apiKey)
            last_published_str = 'from={}&'.format(last_published)
            query = ('https://newsapi.org/v2/everything?sources=bbc-news&'# can change source here to guardian-uk or reuters so long as the appropriate content scraping function is used
                     +page_str+
                     +last_published_str+
                     'sort=date_published&'
                     +pagesize_str
                     +apikey_str) # must go at the end
            response = requests.get(query)
            js = response.json()

            # store the maximum number of pages which can be accessed from this call
            max_page = js['totalResults']/results_per_page + 1

            # Iterate over results in a page
            for k in range(results_per_page):
                article = js['articles'][k]
                desc = article['description']
                url = article['url']
                content = get_bbc_content(url)   # doesnt yet include storing publishedAt
                publishedAt = article['publishedAt'][:-1]
                if content is not None:
                    article_dict[url] = {'content':desc + ' ' + content,
                                        'published_at':publishedAt}
                else:
                    article_dict[url] = {'content':desc,
                                        'published_at':publishedAt}

        except KeyError:
            break

        # Prevent any calls which would exceed the number of results in total
        if p >= max_page:
            break

    return article_dict
