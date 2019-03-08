import tweepy
import tweeting
import getopt
import sys


def usage():
    print("""propNews -- tweet news stories periodically
    
    Requirements
    -----------------
    
    newsapi_key.txt : A text file, in the directory above propNews, contains API keys.
    
    Deployment
    -----------------
    
    To run on an AWS instance:
        $ tmux
        $ python main.py [-options]
    and hit "ctrl+b d" to detach. Then
        $ logout 
    
    To run locally:
        $ python main.py [-options]    
        
    Options
    ------------------
    
    -d		Run in debug mode. 
    
            Only lightly call NewsAPI. You may want to run
            $ mv news.db news.db.temp
            before running the script in debug mode. The 
            script will most likely end in "No news".
            
    -h      Help.
    
            Prints this message and exits.
    """)


try:
    opts, args = getopt.getopt(sys.argv[1:], "dh")
except Exception as err:
    print(str(err))
    usage()
    sys.exit()

dbg_mode = False
for opt, arg in opts:
    if opt == '-d':
        dbg_mode = True
    elif opt == '-h':
        usage()
        sys.exit()
    else:
        usage()
        sys.exit()


credentials_dir = '../'
twitter_credentials_filename = 'twitter_API_keys.txt'  # this must be placed in the directory above the repo
news_api_filename = 'newsapi_key.txt'

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
apiKey = fp.read().split()[0]

# Set twitter credentials
auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
tweepyapi = tweepy.API(auth)

qaly_path = 'global_prios/global_prios.csv'
url_path = 'url_content_lookup.csv'


# Create API database
db_filename = 'news.db'

create_str = '''CREATE TABLE IF NOT EXISTS news (
                url TEXT PRIMARY KEY,
                score REAL NOT NULL,
                topics TEXT,
                published_at DATETIME,
                source TEXT
                )
            '''
is_first_time_setup = tweeting.create_db(db_filename, create_str)

periodicity_s = 3600
max_time = 7*24*3600

tweet_time_window = 3*24.0  # hours
news_refresh_period = 24.0/3  # hours

tweet_thread = tweeting.RepeatEvery(periodicity_s, tweeting.tweet_news, tweepyapi, apiKey, qaly_path, url_path,
                                    db_filename, is_first_time_setup, tweet_time_window, news_refresh_period,
                                    dbg_mode=dbg_mode)

print('Starting')
tweet_thread.start()
tweet_thread.join(max_time)
tweet_thread.stop()
print('Stopped')
