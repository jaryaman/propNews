import threading, time, datetime
import get_articles, score_articles
import pickle
import numpy as np
from pdb import set_trace
import sqlite3 as sq
import os

def create_db(db_filename, create_str):
    """ Create a SQLite database

    Parameters
    ----------------
    db_filename : A string, the name of the database to create

    Returns
    ----------------
    return_status : An bool, True if database is created, False if not
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

def add_quotes(s):
    return '"'+s+'"'

def save_news(db_filename, article_dict):
    ''' Insert article_dict into news

    Parameters
    ----------------

    '''
    conn = sq.connect(db_filename)
    c = conn.cursor()
    for url, url_dict in article_dict.items():
        insert_string = '''INSERT or IGNORE INTO news(
                        url,
                        score,
                        publishedAt)
                        VALUES(
                        {0},
                        {1},
                        {2}
                        )
                        '''.format(add_quotes(url),url_dict['score'],add_quotes(url_dict['published_at']))
        c.execute(insert_string)
    conn.commit()
    conn.close()

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

def tweet_news(tweepyapi,apiKey,qaly_path,error_log_filename, error_log_pointer, db_filename, is_first_time_setup,
qaly_thresh = 1.0, sample_log_qalys=True, dbg_mode=False):
    """
    Tweet a single news story drawn randomly, weighted by a QALY

    Parameters
    --------------
    tweepyapi : tweepy.api.API object, contains Twitter API credentials and allows tweeting
    apiKey : A string, the API key of the news API
    qaly_path : A string, directory of the QALY table
    error_log_filename : A string, file name for error log
    error_log_pointer : An IO pointer, the pointer to the error log
    db_filename : A string, the name of the news database
    is_first_time_setup : A bool, True if this is the first time the news databse has been created
    qaly_thresh : A float, threshold on qalys to tweet
    sample_log_qalys : A bool, sample the qalys in log-space
    dbg_mode : A bool, enter debug mode. Samples fewer pages from the API, since we have a daily budget
    """
    if dbg_mode:
        article_dict = get_articles.get_results(apiKey,page_limit_per_request = 1,results_per_page=10)
    else:
        if is_first_time_setup:
            article_dict = get_articles.get_results(apiKey)
        else:
            last_published = find_API_publish_time(db_filename)
            article_dict = get_articles.get_results(apiKey,last_published)
    if len(article_dict) < 5: # assume something went wrong with the API
        output=tweepyapi.update_status("Something went wrong with the API at " + str(datetime.datetime.now()))
        error_log_pointer = open(error_log_filename,'a')
        error_log_pointer.write('get_articles() error,'+str(datetime.datetime.now())+',NaN'+'\n')
        error_log_pointer.close()
        print('Error in get_articles()\n')
        return
    else:
        ## Calculate aggregate QALY scores for each article
        qaly_scorer = score_articles.get_qaly_data(qaly_path)
        article_dict = score_articles.score_all(article_dict, qaly_scorer)
        save_news(db_filename, article_dict)

        v = article_dict.values()
        v = list(v)
        qalys_scores = np.array([a['score'] for a in v])
        qaly_total = qalys_scores.sum()
        if qaly_total < qaly_thresh: # there aren't enough newsworthy stories
            output=tweepyapi.update_status("I didn't find anything interesting at " + str(datetime.datetime.now()))
            error_log_pointer = open(error_log_filename,'a')
            error_log_pointer.write("No news"+','+str(datetime.datetime.now())+',NaN'+'\n')
            error_log_pointer.close()
            print('No news\n')
            return
        if sample_log_qalys:
            qalys_scores = np.log(qalys_scores + 1.0) # sample qalys in log-space

        article_choice_index = np.random.choice(len(qalys_scores), p=qalys_scores/qalys_scores.sum())
        url = list(article_dict.keys())[article_choice_index]
        topics = v[article_choice_index]['topics']
        topics_string = ''
        for i, topic in enumerate(topics):
            if i == len(topics) - 1:
                topics_string+=topic
            else:
                topics_string+=topic+'; '
        try:
            output=tweepyapi.update_status(topics_string + '\n' + url)
            error_log_pointer = open(error_log_filename,'a')
            error_log_pointer.write('Success,'+str(datetime.datetime.now())+','+topics_string+'\n')
            error_log_pointer.close()
        except Exception as e:
            output=tweepyapi.update_status(e.reason+' Time: '+ str(datetime.datetime.now()))
            error_log_pointer = open(error_log_filename,'a')
            error_log_pointer.write(e.reason+','+str(datetime.datetime.now())+',NaN'+'\n')
            error_log_pointer.close()
            print(e.reason)
            return
    print('Done!')
