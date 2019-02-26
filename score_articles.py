from keyword_parser import parse_keywords
from pdb import set_trace
def get_qaly_data(filepath):
    qaly_scorer = {}
    with open(filepath, 'r') as infile:
        for linenum, line in enumerate(infile):
            if linenum == 0:
                continue

            topic, score, keywords, ref = line.split(',')
            #keywords = keywords.split(' AND ')
            #keywords = tuple([i.strip() for i in keywords]) # remove whitespace
            keywords_set = parse_keywords(keywords)
            for keywords in keywords_set:
            	qaly_scorer[tuple(keywords)] = (float(score), topic)

    return qaly_scorer

def score_article(article, qaly_scorer):
    article_score = 0
    article_topics = []
    for keyword_set in qaly_scorer:
        if all(keyword in article for keyword in keyword_set):
            article_score += qaly_scorer[keyword_set][0]
            article_topics.append(qaly_scorer[keyword_set][1])
    return article_score, article_topics

def score_all(article_dict, qaly_scorer):
    for article_url in article_dict:
        article_score, article_topics = score_article(article_dict[article_url]['content'], qaly_scorer)
        article_dict[article_url]['score'] = article_score
        article_dict[article_url]['topics'] = article_topics
    return article_dict
