import threading, time, datetime
import get_articles, score_articles
import pickle
import numpy as np
from pdb import set_trace
import sqlite3 as sq
import os
import datetime

dt_format = "%Y-%m-%dT%H:%M:%S"

def create_db(db_filename, create_str):
    """ Create a SQLite database

    Parameters
    ----------------
    db_filename : A string, the name of the database to create
    create_str : A string, an SQLite command to create the database

    Returns
    ----------------
    return_status : An bool, True if database is created, False if the file already exists
    """
    if not os.path.exists(db_filename):
        conn = sq.connect(db_filename)
        c = conn.cursor()
        c.execute(create_str)
        conn.commit()
        conn.close()
        return True
    else:
        return False


# Class for repetitive actions
class RepeatEvery(threading.Thread):
    """
    Class to repeat a function, with arguments, with a given periodicity

    Parameters
    -----------------
    interval : A float, the amount of time in seconds between calling the function
    func : A function to be called repetitively
    *args : Positional arguments for func
    *kwargs : Named arguments for func
    """
    def __init__(self, interval, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.interval = interval  # seconds between calls
        self.func = func          # function to call
        self.args = args          # optional positional argument(s) for call
        self.kwargs = kwargs      # optional keyword argument(s) for call
        self.runable = True
    def run(self):
        while self.runable:
            self.func(*self.args, **self.kwargs)
            time.sleep(self.interval)
    def stop(self):
        self.runable = False

def fetch_news_since(db_filename, query_db_from):
    # TODO: Finish this function
    """
    Fetch news since a particular time from database

    Parameters
    -------------
    db_filename : A string, the name of the news database
    query_from : A string of the form YYYY-MM-DDTHH:MM:SS, the earliest time to query the database from

    Returns
    -------------
    recent_news : A [XXXXXXXXXX] (TODO: Finish)

    """
    conn = sq.connect(db_filename)
    c = conn.cursor()
    date_query = '''SELECT * FROM news
                    WHERE publishedAt > datetime('{}')
    '''.format(datetime.datetime.strftime(query_db_from,dt_format))
    c.execute(date_query)
    recent_news = c.fetchall()
    conn.close()
    return recent_news

def tweet_news(tweepyapi,apiKey,qaly_path, db_filename, is_first_time_setup, tweet_time_window, news_refresh_period,
qaly_thresh = 1.0, sample_log_qalys=True, dbg_mode=False):
    """
    Tweet a single news story drawn randomly, weighted by a QALY

    Parameters
    --------------
    tweepyapi : tweepy.api.API object, contains Twitter API credentials and allows tweeting
    apiKey : A string, the API key of the news API
    qaly_path : A string, directory of the QALY table
    db_filename : A string, the name of the news database
    is_first_time_setup : A bool, True if this is the first time the news databse has been created
    tweet_time_window : A float, the number of hours prior to now to draw from the database to tweet from
    news_refresh_period : A float,

    qaly_thresh : A float, threshold on qalys to tweet
    sample_log_qalys : A bool, sample the qalys in log-space
    """

    if is_first_time_setup:
        set_trace()
        assert False
        if dbg_mode:
            print('DBG MODE')
            get_articles.get_results(apiKey,db_filename,qaly_path,query_from=query_from,
                                                    page_limit_per_request=1,
                                                    results_per_page=10)
        else:
            print('Building database. This may take some time...')
            get_articles.get_results(apiKey,db_filename,qaly_path)

    # Check if the database is out of date
    last_article_publish_time = get_articles.find_newest_db_article(db_filename, lag_mins=0)
    last_article_publish_time_dtm = datetime.datetime.strptime(last_article_publish_time, dt_format)
    query_db_from = datetime.datetime.now() - datetime.timedelta(hours=tweet_time_window)
    delta = datetime.datetime.now() - last_article_publish_time_dtm

    hours_since_last_article = delta.days*24.0 + delta.seconds/3600.0
    if not dbg_mode:
        if hours_since_last_article > news_refresh_period:
            print('Last published article: {}'.format(last_article_publish_time))
            print('Time difference to now: {} (hours)'.format(hours_since_last_article))
            print('News db outdated. Updating...')
            query_from = get_articles.find_newest_db_article(db_filename, lag_mins=20) # TODO: should pass lag in as a variable
            get_articles.get_results(apiKey,db_filename,qaly_path,query_from=query_from)
    else:
        print('DBG: Skipping time window check')


    # Pull articles that are within the time window

    # Tweet
    recent_news = fetch_news_since(db_filename, query_db_from)

    qalys_scores = np.array([a[1] for a in recent_news])
    qaly_total = qalys_scores.sum()
    if qaly_total < qaly_thresh: # there aren't enough newsworthy stories
        output=tweepyapi.update_status("I didn't find anything interesting in the past {} hrs, at:".format(tweet_time_window) +
         str(datetime.datetime.now()))
        print('No news\n')
        return
    if sample_log_qalys:
        qalys_scores = np.log(qalys_scores + 1.0) # sample qalys in log-space

    article_choice_index = np.random.choice(len(qalys_scores), p=qalys_scores/qalys_scores.sum())
    url = recent_news[article_choice_index][0]
    topics = recent_news[article_choice_index][2]
    output=tweepyapi.update_status(topics +' {}'.format(str(datetime.datetime.now())) + '\n' + url)

    print('Done!')
