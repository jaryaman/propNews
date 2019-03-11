import tweepy
import tweeting
import argparse

parser = argparse.ArgumentParser(description="Tweet news stories periodically according to global priorities.")
parser.add_argument('-dbg_mode', default=False, type=bool, nargs=1, help="Run in debug mode (default = False)")
parser.add_argument('-tw_cred', default='twitter_API_keys.txt', type=str, nargs=1,
                    help="Contains Twitter API credentials. Must be in directory above repo.")
parser.add_argument('-news_cred', default='newsapi_key.txt', type=str, nargs=1,
                    help="Contains NewsAPI key. Must be in directory above repo.")
parser.add_argument('-url_path', default='url_content_lookup.csv', type=str, nargs=1,
                    help="Directory of the url lookup table")
parser.add_argument('-qaly_path', type=str, nargs=1, default='global_prios/global_prios.csv',
                    help="Path to the QALY table (default =global_prios/global_prios.csv)")
parser.add_argument('-db_filename', default='news.db', type=str, nargs=1,
                    help="Name of news database. Default = news.db")

parser.add_argument('-periodicity_s', default=3600, type=float, nargs=1,
                    help="Tweet periodicity (s). Default=3600.")
parser.add_argument('-max_time', default=7*24*3600, type=float, nargs=1,
                    help="Duration to tweet (s). Default=604800 (1 week).")
parser.add_argument('-tweet_time_window', default=2*7*24.0, type=float, nargs=1,
                    help="Time window to search into the past for news (hours). Default=336 (2 weeks).")
parser.add_argument('-news_refresh_period', default=24.0/3, type=float, nargs=1,
                    help="Periodicity to update news database (hours). Default = 8.")


args = parser.parse_args()
dbg_mode = args.dbg_mode
twitter_credentials_filename = args.tw_cred
news_api_filename = args.news_cred
url_path = args.url_path
qaly_path = args.qaly_path
db_filename = args.db_filename
periodicity_s = args.periodicity_s
max_time = args.max_time
tweet_time_window = args.tweet_time_window
news_refresh_period = args.news_refresh_period

credentials_dir = '../'

# Parse twitter credentials from the text file, see https://developer.twitter.com/en/apps
fp = open(credentials_dir+twitter_credentials_filename, 'r')
credentials = fp.read().splitlines()
fp.close()

consumer_token = credentials[0].split('=')[1]
consumer_secret = credentials[1].split('=')[1]
access_token = credentials[2].split('=')[1]
access_token_secret = credentials[3].split('=')[1]

# Get news API key
fp = open(credentials_dir+news_api_filename, 'r')
api_key = fp.read().split()[0]

# Set twitter credentials
auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
tweepyapi = tweepy.API(auth)

tweet_thread = tweeting.RepeatEvery(periodicity_s, tweeting.tweet_news, tweepyapi, api_key, qaly_path, url_path,
                                    db_filename, tweet_time_window, news_refresh_period,
                                    dbg_mode=dbg_mode)

print('Starting')
tweet_thread.start()
tweet_thread.join(max_time)
tweet_thread.stop()
print('Stopped')
