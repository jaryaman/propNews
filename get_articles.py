import requests
import pickle

def get_results(page_limit_per_request=10, results_per_page=100):
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
                     'pagesize={}&'.format(results_per_page)
                     'apiKey={}'.format(apiKey))
            response = requests.get(query)
            js = response.json()

            # Iterate over results in a page
            for k in range(results_per_page):
                article = js['articles'][k]
                desc = article['description']
                content = article['content']
                url = article['url']
                if content is not None:
                    dict_url_desc[url] = desc + ' ' + content
                else:
                    dict_url_desc[url] = desc

        except KeyError:
            break

    return dict_url_desc
