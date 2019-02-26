import requests
import pickle
from get_full_content import get_bbc_content



def get_results(page_limit_per_request=50, results_per_page=20):
    """Queries NewsAPI for articles up to page_limit_per_request (max 50) and
    returns a dictionary mapping URL: content."""
    
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
                content = get_bbc_content(url) 
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