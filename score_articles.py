from keyword_parser import parse_keywords
import sqlite3 as sq
from get_full_content import get_url_content
import argparse
import datetime

dt_format = "%Y-%m-%dT%H:%M:%S"


def get_qaly_data(filename):
    """Parses a text file containing the table of topics, scores, and search strings

    Parameters
    ----------------
    filename : A string, the path to the score table

    Returns
    ----------------
    qaly_scorer : A dict, keys are tuples of keywords, all of which are necessary to be assigned a topic. Values are
                  tuples where value[0] is the score of the topic and value[1] is the topic ID
    """
    qaly_scorer = {}
    with open(filename, 'r') as infile:
        for linenum, line in enumerate(infile):
            if linenum == 0:
                continue

            topic, score, keywords, ref = line.split(',')
            keywords_set = parse_keywords(keywords)
            for keywords in keywords_set:
                qaly_scorer[tuple(keywords)] = (float(score), topic)

    return qaly_scorer


def score_article(article, qaly_scorer):
    """Assigns a score to text

    Parameters
    ----------------
    article : A string, the text of an article to score
    qaly_scorer : A dict, keys are tuples of keywords, all of which are necessary to be assigned a topic. Values are
                  tuples where value[0] is the score of the topic and value[1] is the topic ID

    Returns
    ----------------
    article_score : An int, the score of the article
    article_topics : A list of strings, the topics associated with the article
    """

    article_score = 0
    article_topics = []
    for keyword_set in qaly_scorer:
        if all(keyword in article for keyword in keyword_set):
            topic = qaly_scorer[keyword_set][1]
            if topic not in article_topics:
                article_score += qaly_scorer[keyword_set][0]
                article_topics.append(topic)
    return article_score, article_topics


def score_all(article_dict, qaly_scorer):
    """Associate a score with all articles in a dictionary of articles

    Parameters
    ----------------
    article_dict : A dict, the keys are URLs of articles, the values are dicts with the following keys
                        - 'content' : A string, the text of the article
                        - 'publishedAt' : A string, the time the article was published in the form YYYY-MM-DDTHH:MM:SS
    qaly_scorer : A dict, keys are tuples of keywords, all of which are necessary to be assigned a topic. Values are
                  tuples where value[0] is the score of the topic and value[1] is the topic ID

    Returns
    ----------------
    article_dict : Same as the parameter article_dict, with new entries in the value dicts
                    - 'score' : An int, the score of the article
                    - 'topics' : A list of strings, the topics of the article
    """
    for article_url in article_dict:
        article_score, article_topics = score_article(article_dict[article_url]['content'], qaly_scorer)
        article_dict[article_url]['score'] = article_score
        article_dict[article_url]['topics'] = article_topics
    return article_dict


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
    if len(topics) == 0:
        return 'NULL'
    else:
        topics_string = ''
        for i, topic in enumerate(topics):
            if i == len(topics) - 1:
                topics_string += topic
            else:
                topics_string += topic+'; '
        return topics_string


def resubmit_score_topics(db_filename, article_dict):
    """Update score and topics in news database

    Parameters
    ----------------
    db_filename : A string, the name of the news database
    article_dict: A dict of dicts, the keys are URLS, the values are dicts which must contain at least:
        score : A float, the score of the article
        topics : A list of strings, the topics associated with the URL
    """
    conn = sq.connect(db_filename)
    c = conn.cursor()
    for url, url_dict in article_dict.items():
        insert_string = '''UPDATE news SET score={0}, topics={1} WHERE url={2}
                        '''.format(url_dict['score'],
                                   add_quotes(get_topic_string(url_dict['topics'])),
                                   add_quotes(url))
        c.execute(insert_string)
    conn.commit()
    conn.close()
    print('News db updated!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Score articles in database.")
    parser.add_argument('-db_filename', default='news.db', type=str, nargs=1, help="The news database to score")
    parser.add_argument('-since', type=str, nargs=1,
                        help="""The earliest datetime to score in form YYYY-MM-DDTHH:MM:SS 
                        (default: 2 weeks prior to now)""")
    parser.add_argument('-qaly_path', type=str, nargs=1, default='global_prios/global_prios.csv',
                        help="Path to the QALY table (default =global_prios/global_prios.csv)")
    parser.add_argument('-url_path', default='url_content_lookup.csv', type=str, nargs=1,
                        help="Directory of the url lookup table")

    args = parser.parse_args()
    _db_filename = args.db_filename
    _qaly_path = args.qaly_path
    _url_path = args.url_path

    if args.since is not None:
        since = args.since[0]
        try:
            datetime.datetime.strptime(since, dt_format)
        except ValueError:
            raise ValueError("Incorrect data format, should be {}".format(dt_format))
    else:
        since = datetime.datetime.now() + datetime.timedelta(days=-14)
        since = datetime.datetime.strftime(since, dt_format)

    conn = sq.connect(_db_filename)
    c = conn.cursor()
    date_query = '''SELECT url FROM news
                        WHERE published_at > datetime('{}')
        '''.format(since)
    c.execute(date_query)
    recent_news = c.fetchall()
    conn.close()

    # Score URLs
    _qaly_scorer = get_qaly_data(_qaly_path)

    _article_dict = {}
    for i, _url_temp in enumerate(recent_news):
        _url = _url_temp[0]
        if i % 20 == 0:
            print("{0} of {1}".format(i, len(recent_news)))
        content = get_url_content(_url_path, _url)
        _article_score, _article_topics = score_article(content, _qaly_scorer)
        _article_dict[_url] = {'score': _article_score,
                               'topics': _article_topics}

    resubmit_score_topics(_db_filename, _article_dict)

