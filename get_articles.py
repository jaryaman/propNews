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
    query_from : A string of the form YYYY-MM-DDTHH:MM:SS, the time to query the API from

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
        query_from = datetime.datetime.strftime(query_from_dtm,dt_format)
        return query_from
    else:
        raise Exception('News database not found!')



def get_results(apiKey, query_from=None, page_limit_per_request=10, results_per_page=100):
    """
    Query NewsAPI for URLs and metadata

    Parameters
    ---------------
    apiKey : A string, the NewsAPI API key
    query_from : A string, the time to query the API from of the form YYYY-MM-DDTHH:MM:SS
    page_limit_per_request : An int, Maximum number of pages to request from the API
    results_per_page : An int, Maximum number of results to request per page from the API

    Returns
    ---------------
    article_dict : A dict of dicts, the keys are URLs, and the values are dicts containing
        contents : A string, the contents of the URL
        published_at : A string, the datetime the article was published of the form YYYY-MM-DDTHH:MM:SS
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
            if query_from is not None:
                query_from_str = 'from={}&'.format(query_from+'Z')
                query = ('https://newsapi.org/v2/everything?sources=bbc-news&'# can change source here to guardian-uk or reuters so long as the appropriate content scraping function is used
                         +page_str+
                         +last_published_str+
                         'sort=date_published&'
                         +pagesize_str
                         +apikey_str) # must go at the end
            else:
                query = ('https://newsapi.org/v2/everything?sources=bbc-news&'# can change source here to guardian-uk or reuters so long as the appropriate content scraping function is used
                         +page_str+
                         'sort=date_published&'
                         +pagesize_str
                         +apikey_str) # must go at the end
            response = requests.get(query)
            js = response.json()

            # store the maximum number of pages which can be accessed from this call
            max_page = js['totalResults']/results_per_page + 1

            # Iterate over results in a page
            for k in range(results_per_page):
                if k % 200 == 0:
                    print('Processing result {}'.format(k))
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
