
from bs4 import BeautifulSoup
import urllib3
import certifi
import re

def get_bbc_content(url):
    """
    Takes a given URl from BBC news and returns all relevant article content

    Parameters
    ----------------
    url, url of article - must be of for www.bbc.co.uk/news/* to get correct content
    """

    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
    content = http.request('GET', url)
    soup = BeautifulSoup(content.data, "lxml")
    story_raw = BeautifulSoup(''.join([str(s) for s in soup.find_all(class_=re.compile('story-body__inner'))]), "lxml")
    story_processed = re.sub('<[^<>]*>','',' '.join([str(s) for s in story_raw.find_all('p')]))

    return story_processed

def get_guardian_content(url):
    """
    Takes a given URl from the guardian and returns all relevant article content

    Parameters
    ----------------
    url, url of article - must be of for www.theguardian.com/* to get correct content
    """
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
    content = http.request('GET', url)
    soup = BeautifulSoup(content.data, "lxml")
    story_raw = BeautifulSoup(''.join([str(s) for s in soup.find_all(class_=re.compile('article__body'))]), "lxml")
    story_processed = re.sub('<[^<>]*>','',' '.join([str(s) for s in story_raw.find_all('p')]))

    return story_processed

def get_reuters_content(url):
    """
    Takes a given URl from the guardian and returns all relevant article content

    Parameters
    ----------------
    url, url of article - must be of for www.reuters.com/* (or any specific country's version) to get correct content
    """
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',ca_certs=certifi.where())
    content = http.request('GET', url)
    soup = BeautifulSoup(content.data, "lxml")
    story_raw = BeautifulSoup(''.join([str(s) for s in soup.find_all(class_=re.compile('StandardArticleBody_container'))]), "lxml")
    story_processed = re.sub('<[^<>]*>','',' '.join([str(s) for s in story_raw.find_all('p')]))

    return story_processed
