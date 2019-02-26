import requests
import pickle
from get_full_content import get_bbc_content

def get_new_results(page_limit_per_request=10, results_per_page=100, last_published):
    """Queries NewsAPI for articles up to page_limit_per_request (max 10) and
    returns a dictionary mapping URL: content, as well as the time the most recent article published was released"""

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
                     'from={}&'.format(last_published)
                     'sort=date_published&'
                     'pagesize={}&'.format(results_per_page)
                     'apiKey={}'.format(apiKey))
            response = requests.get(query)
            js = response.json()
            
            # store the maximum number of pages which can be accessed from this call
            max_page = js['totalResults']/results_per_page + 1 

            # Iterate over results in a page
            for k in range(results_per_page):
                article = js['articles'][k]
                desc = article['description']
                url = article['url']
                content = get_bbc_content(url)                
                if i == 0 & k == 0:
                    last_call = article['publishedAt']
                if content is not None:
                    dict_url_desc[url] = desc + ' ' + content
                else:
                    dict_url_desc[url] = desc

        except KeyError:
            break
        
        # Prevent any calls which would exceed the number of results in total
        if p >= max_page:
            break

    return dict_url_desc, last_call
