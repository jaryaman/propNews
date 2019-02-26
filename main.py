import tweepy
import tweeting
from IPython import get_ipython
import sqlite3 as sq

'''
To run this script:

$ tmux
$ python main.py

Then detach the session by typing ctrl+b d
'''

# Make changes to functions on the fly
ipython = get_ipython()
ipython.magic("reload_ext autoreload")
ipython.magic("autoreload 2")


credentials_dir = '../'
credentials_filename = 'twitter_API_keys.txt' # this must be placed in the directory above the repo

# Parse twitter credentials from the text file, see https://developer.twitter.com/en/apps
fp = open(credentials_dir+credentials_filename,'r')
creds = fp.read().splitlines()
for c in creds:
    if 'API_key=' in c:
        consumer_token=c.split('=')[1]
    if 'API_secret_key=' in c:
        consumer_secret=c.split('=')[1]
    if 'Access_token=' in c:
        access_token=c.split('=')[1]
    if 'Access_token_secret=' in c:
        access_token_secret=c.split('=')[1]

# Set twitter credentials
auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
tweepyapi = tweepy.API(auth)

qaly_path = 'global_prios/global_prios.csv'

# Set up error log
error_log_filename = 'error_log.txt'
error_log_pointer = open(error_log_filename,'w')
error_log_pointer.write('Type,Time,Topic\n')
error_log_pointer.close()

# Create API database
db_filename = 'news.db'
create_str = '''CREATE TABLE IF NOT EXISTS news (
                 url TEXT PRIMARY KEY,
                 contents TEXT NOT NULL,
                 publishedAt DATETIME
                 )
            '''
tweeting.create_db(db_filename, create_str)

periodicity_s = 3600
max_time = 7*24*3600

thread = tweeting.RepeatEvery(periodicity_s, tweeting.tweet_news, tweepyapi, qaly_path, error_log_filename, error_log_pointer, dbg_mode=True)

print('Starting')
thread.start()
thread.join(max_time)
thread.stop()
print('Stopped')
