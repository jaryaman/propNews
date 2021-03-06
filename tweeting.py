import threading
import time
import get_articles
import numpy as np
import sqlite3 as sq
import os
import datetime
import os

dt_format = "%Y-%m-%dT%H:%M:%S"


def create_db(db_filename, create_str):
    """Create a SQLite database

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



def fetch_news_since(db_filename, query_db_from):
    """Fetch news since a particular time from database

    Parameters
    -------------
    db_filename : A string, the name of the news database
    query_db_from : A string of the form YYYY-MM-DDTHH:MM:SS, the earliest time to query the database from

    Returns
    -------------
    recent_news : A list of tuples corresponding to entries of the news database, where the date published is greater
                  than query_from
    """
    conn = sq.connect(db_filename)
    c = conn.cursor()
    date_query = '''SELECT * FROM news
                    WHERE published_at > datetime('{}')
    '''.format(datetime.datetime.strftime(query_db_from, dt_format))
    c.execute(date_query)
    recent_news = c.fetchall()
    conn.close()
    return recent_news


def tweet_news(tweepyapi, api_key, qaly_path, url_path, db_filename, tweet_time_window,
               news_refresh_period, qaly_thresh=1.0, sample_log_qalys=True, dbg_mode=False, lag_minutes=20):
    """Tweet a single news story drawn randomly, weighted by a QALY, over a time window extending into the past

    Parameters
    --------------
    tweepyapi : tweepy.api.API object, contains Twitter API credentials and allows tweeting
    api_key : A string, the API key of the news API
    qaly_path : A string, directory of the QALY table
    url_path : A string, the directory of the URL lookup table for news sources
    db_filename : A string, the name of the news database
    tweet_time_window : A float, the number of hours prior to now to draw from the news database to tweet from
    news_refresh_period : A float, the period in hours between refreshing the news database
    lag_minutes : A string, the number of minutes of lag to call NewsAPI since the most recent article in the database

    qaly_thresh : A float, threshold on qalys to tweet
    sample_log_qalys : A bool, sample the qalys in log-space
    dbg_mode : A bool, if True enter debug mode
    """

    create_str = '''CREATE TABLE IF NOT EXISTS news (
                    url TEXT PRIMARY KEY,
                    score REAL NOT NULL,
                    topics TEXT,
                    published_at DATETIME,
                    source TEXT
                    )
                '''

    is_first_time_setup = create_db(db_filename, create_str)

    if is_first_time_setup:
        if dbg_mode:
            print('DBG MODE')
            get_articles.get_many_results(api_key, db_filename, qaly_path, url_path, page_limit_per_request=1,
                                          results_per_page=10)
        else:
            print('Building database. This may take some time...')
            get_articles.get_many_results(api_key, db_filename, qaly_path, url_path)
            os.system("cp {0} {0}.bckup".format(db_filename))

    # Check if the news database is out of date, TODO: handle the case when database exists but is empty
    last_article_publish_time = get_articles.find_newest_db_article(db_filename, lag_minutes=0)
    last_article_publish_time_dtm = datetime.datetime.strptime(last_article_publish_time, dt_format)
    query_db_from = datetime.datetime.now() - datetime.timedelta(hours=tweet_time_window)
    delta = datetime.datetime.now() - last_article_publish_time_dtm

    hours_since_last_article = delta.days*24.0 + delta.seconds/3600.0
    if not dbg_mode:
        if hours_since_last_article > news_refresh_period:
            print('Last published article: {}'.format(last_article_publish_time))
            print('Time difference to now: {} (hours)'.format(hours_since_last_article))
            print('News db outdated. Updating...')
            query_from = get_articles.find_newest_db_article(db_filename, lag_minutes=lag_minutes)
            get_articles.get_many_results(api_key, db_filename, qaly_path, url_path, query_from=query_from)
            os.system("cp {0} {0}.bckup".format(db_filename))
    else:
        print('DBG: Skipping time window check')

    # Pull articles that are within the tweet time window
    recent_news = fetch_news_since(db_filename, query_db_from)

    qalys_scores = np.array([a[1] for a in recent_news])
    qaly_total = qalys_scores.sum()
    if qaly_total < qaly_thresh:  # there aren't enough newsworthy stories
        _ = tweepyapi.update_status("I didn't find anything interesting in the past {0} hrs, at: {1}".format(
            tweet_time_window, str(datetime.datetime.now())))
        print('No news\n')
        return

    # Sample articles according to score
    if sample_log_qalys:
        qalys_scores = np.log(qalys_scores + 1.0)  # sample qalys in log-space

    # Tweet
    article_choice_index = np.random.choice(len(qalys_scores), p=qalys_scores/qalys_scores.sum())
    url = recent_news[article_choice_index][0]
    topics = recent_news[article_choice_index][2]
    _ = tweepyapi.update_status(topics + ' {}'.format(str(datetime.datetime.now())) + '\n' + url)

    print('Tweet!')
