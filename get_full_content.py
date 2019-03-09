from bs4 import BeautifulSoup
import urllib3
import certifi
import re


def get_url_content(url_lookup, url):
    """Takes a given URl and returns all relevant article content

    Parameters
    ----------------
    url_lookup, A string, the path to database of URLs for which content can be taken
    url, url we wish to query
    """

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    content = http.request('GET', url)
    soup = BeautifulSoup(content.data, "lxml")
    story_processed = None  # Ensures None is returned if URL is incompatible format
    with open(url_lookup, 'r') as infile:
        for line_num, line in enumerate(infile):
            line = line[:-1]  # remove \n
            if line_num == 0:
                continue
            source, keyword, delimiter = line.split(',')

            if keyword in url:
                story_raw = BeautifulSoup(''.join([str(s) for s in soup.find_all(class_=re.compile(delimiter))]),
                                          'lxml')
                story_processed = re.sub('<[^<>]*>', '', ' '.join([str(s) for s in story_raw.find_all('p')]))

    return story_processed
