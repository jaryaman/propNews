# code for using mercury API with python taken from github 
# https://github.com/kennethreitz/mercury-parser and adapted for python 3

import requests
import maya
import pickle

MERCURY_API = 'https://mercury.postlight.com/parser?url='

class ParsedArticle(object):
    """docstring for ParsedArticle"""
    def __init__(self, parser):
        super(ParsedArticle, self).__init__()
        self._parser = parser

        self.title = None
        self.content = None
        self.date_published = None
        self.lead_image_url = None
        self.dek = None
        self.url = None
        self.domain = None
        self.excerpt = None
        self.word_count = None
        self.direction = None
        self.total_pages = None
        self.rendered_pages = None
        self.next_page_url = None

    def __repr__(self):
        return '<ParsedArticle url={0!r}>'.format(self.url)

    @classmethod
    def from_dict(klass, d, parser):

        # The new ParsedArticle.
        p = klass(parser=parser)

        # Add all values from returned JSON object to instance.
        for key, value in d.items():
            setattr(p, key, value)

        # Proper Datetimes.
        if p.date_published:
            p.date_published = maya.MayaDT.from_iso8601(p.date_published).datetime()

        return p

    def next(self):
        if self.next_page_url:
            return self._parser.parse(self.next_page_url)


class ParserAPI(object):
    def __init__(self, api_key):
        super(ParserAPI, self).__init__()
        self.api_key = api_key
        self._session = requests.Session()

    def parse(self, url):
        url = '{0}{1}'.format(MERCURY_API, url)
        headers = {'x-api-key': self.api_key}

        r = self._session.get(url, headers=headers)
        p = ParsedArticle.from_dict(r.json(), parser=self)
        return p

def get_results(page_limit_per_request=50, results_per_page=20):
    """Queries NewsAPI for articles up to page_limit_per_request (max 50) and
    returns a dictionary mapping URL: content."""
    
    mercury = ParserAPI(api_key='uNQyRItUfR78vKZsuRKi4MkAVSCCxHwGbOgPGGq3')
    dict_url_desc = {}  # stores articles indexed by URL
    # Iterate over pages - rate limited
    for i in range(page_limit_per_request):
        try:
            if i % 10 == 0:
                print('Accessing page {}'.format(i))
            p = i + 1
            page_str = 'page={}&'.format(p)
            query = ('https://newsapi.org/v2/everything?sources=bbc-news&'
                     +page_str+
                     'sort=date_published&'
                     'apiKey=9d2e6fa594ef4c6c9d030886d5322618')
            response = requests.get(query)
            js = response.json()
            
            # Iterate over results in a page
            for k in range(results_per_page):
                article = js['articles'][k]
                desc = article['description']
                url = article['url']
                p = mercury.parse(url)
                content = p.content
                if content is not None:
                    dict_url_desc[url] = desc + ' ' + content
                else:
                    dict_url_desc[url] = desc

        except KeyError:
            break

    return dict_url_desc
"""
# Export results as a pickled dictionary
dict_url_desc_out = open('dict_url_desc_out.pkl', 'wb')
pickle.dump(dict_url_desc, dict_url_desc_out)
dict_url_desc_out.close()
"""