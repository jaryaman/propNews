import requests
from get_full_content import get_url_content
import os
import sqlite3 as sq
import score_articles
import datetime

dt_format = "%Y-%m-%dT%H:%M:%S"


def find_newest_db_article(db_filename, lag_minutes=0):
    """Find the time of the newest article in the database, with lag

    Parameters
    -------------
    db_filename : A string, the name of the news database
    lag_minutes : An int, the number of minutes backwards in time since the newest article that the API should be called
                  from. This is to take into account latency between a story being published on the website and being
                  discoverable on NewsAPI.

    Returns
    ------------
    query_from : A string of the form YYYY-MM-DDTHH:MM:SS, the time of the newest article in the database, with lag
    """

    if os.path.exists(db_filename):
        conn = sq.connect(db_filename)
        c = conn.cursor()
        date_query = '''SELECT published_at FROM news
                        ORDER BY published_at
                        DESC
                        LIMIT 1
        '''
        c.execute(date_query)
        date_latest = c.fetchall()[0][0]
        conn.close()

        # Subtract lag_minutes
        date_latest_dtm = datetime.datetime.strptime(date_latest, dt_format)
        query_from_dtm = date_latest_dtm + datetime.timedelta(minutes=-lag_minutes)
        query_from = datetime.datetime.strftime(query_from_dtm,dt_format)
        return query_from
    else:
        raise Exception('News database not found!')


def add_quotes(s):
    """Add quotes to a string
    """
    return '"'+s+'"'


def get_topic_string(topics):
    """Convert a list of topics into a string

    Parameters
    --------------
    topics : A list of strings, the topics associated with the URL

    Returns
    --------------
    topic_string : A human-readable string formatted as a list of string
    """
    if len(topics)==0:
        return 'NULL'
    else:
        topics_string = ''
        for i, topic in enumerate(topics):
            if i == len(topics) - 1:
                topics_string += topic
            else:
                topics_string += topic+'; '
        return topics_string
    

def update_news_db(db_filename, article_dict):
    """Append article_dict into news database

    Parameters
    ----------------
    db_filename : A string, the name of the news database
    article_dict: A dict of dicts, the keys are URLS, the values are dicts which must contain at least:
        score : A float, the score of the article
        topics : A list of strings, the topics associated with the URL
        published_at : A string, of the form YYYY-MM-DDTHH:MM:SS, the datetime the article was published
    """
    conn = sq.connect(db_filename)
    c = conn.cursor()
    for url, url_dict in article_dict.items():
        insert_string = '''INSERT or IGNORE INTO news(
                        url,
                        score,
                        topics,
                        published_at,
                        source)
                        VALUES(
                        {0},
                        {1},
                        {2},
                        {3},
                        {4}
                        )
                        '''.format(add_quotes(url), url_dict['score'],
                                   add_quotes(get_topic_string(url_dict['topics'])),
                                   add_quotes(url_dict['publishedAt']),
                                   add_quotes(url_dict['source']))
        c.execute(insert_string)
    conn.commit()
    conn.close()
    print('News db updated!')


def get_many_results(api_key, db_filename, qaly_path, url_path, query_from=None, page_limit_per_request=10,
                     results_per_page=100):
    """Query NewsAPI for URLs and metadata, score articles, and save to news database

    Parameters
    ---------------
    api_key : A string, the NewsAPI API key
    db_filename : A string, the name of the news database
    qaly_path : A string, directory of the QALY table
    url_path : A string, directory of the url lookup table
    query_from : A string, the time to query the API from, of the form YYYY-MM-DDTHH:MM:SS
    page_limit_per_request : An int, Maximum number of pages to request from the API
    results_per_page : An int, Maximum number of results to request per page from the API
    """

    # Iterate over pages - rate limited
    for i in range(page_limit_per_request):
        article_dict = {}  # stores articles indexed by URL. Reset every page to spare memory
        try:
            p = i + 1
            page_str = 'page={}&'.format(p)
            pagesize_str = 'pagesize={}&'.format(results_per_page)
            api_key_str = 'apiKey={}'.format(api_key)
            source_str = 'sources='
            with open(url_path, 'r') as infile:
                for line_num, line in enumerate(infile):
                    if line_num == 0:
                        continue
                    source, keyword, delimiter = line.split(',')
                    source_str += source + ','
            source_str += '&'
            
            if query_from is not None:
                query_from_str = 'from={}&'.format(query_from)
                query = ('https://newsapi.org/v2/everything?'
                         + source_str
                         + page_str
                         + query_from_str +
                         'sort=date_published&'
                         + pagesize_str
                         + api_key_str)
            else:
                query = ('https://newsapi.org/v2/everything?'
                         + source_str
                         + page_str +
                         'sort=date_published&'
                         + pagesize_str
                         + api_key_str)
            response = requests.get(query)
            js = response.json()
            # store the maximum number of pages which can be accessed from this call
            max_page = js['totalResults']/results_per_page + 1
            print('Accessing page {0}'.format(p))

            # Iterate over results in a page
            for k in range(len(js['articles'])):
                if k % 20 == 0:
                    print('Processing result {0} of {1}'.format(k, len(js['articles'])))
                article = js['articles'][k]
                desc = article['description']
                url = article['url']
                content = get_url_content(url_path, url)
                published_at = article['publishedAt'][:-1]
                if content is not None:
                    article_dict[url] = {'content': desc + ' ' + content,
                                         'publishedAt': published_at,
                                         'source': source_str}
                else:
                    article_dict[url] = {'content': desc,
                                         'publishedAt': published_at,
                                         'source': source_str}
            qaly_scorer = score_articles.get_qaly_data(qaly_path)
            article_dict = score_articles.score_all(article_dict, qaly_scorer)
            update_news_db(db_filename, article_dict)
        except KeyError as e:
            print(e)
            print('WARNING: Key error in calling API. Some articles may be lost.')
            break

        # Prevent any calls which would exceed the number of results in total
        if p >= max_page:
            break
