from keyword_parser import parse_keywords
import sqlite3 as sq
import sys
import argparse
import datetime


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
            article_score += qaly_scorer[keyword_set][0]
            article_topics.append(qaly_scorer[keyword_set][1])
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Score articles in database.")
    parser.add_argument('filename', type=str, nargs=1, help="The news database to score")
    parser.add_argument('-since', type=str, nargs=1,
                        help="The earliest datetime to score in form YYYY-MM-DDTHH:MM:SS (default: 2 weeks from now)")

    args = parser.parse_args()
    db_filename = args.filename[0]
    if args.since is not None:
        since = args.since[0]
    else:
        since = datetime.datetime.now()



    # db_filename = str(sys.argv[0])
    # conn = sq.connect(db_filename)
    # c = conn.cursor()
    # date_query = '''SELECT * FROM news
    #                     WHERE published_at > datetime('{}')
    #     '''.format(datetime.datetime.strftime(query_db_from, dt_format))
    # c.execute(date_query)
    # recent_news = c.fetchall()
    # conn.close()
