1. Make an account with http://aws.amazon.com and go to https://eu-west-1.console.aws.amazon.com/console/home?region=eu-west-1#
2. Click on Instances and Launch Instance
3. Follow the steps, make an Ubuntu 18.04 instance with t2.micro (free tier)
4. Set up SSH (see https://www.youtube.com/watch?v=l53QjtPvF_A) and SSH into the instance
5. Then, inside the instance:

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade
sudo apt-get autoremove
sudo apt-get autoclean
wget https://repo.anaconda.com/archive/Anaconda3-2018.12-Linux-x86_64.sh
bash Anaconda3-2018.12-Linux-x86_64.sh
```

Make sure
`export PATH="/home/ubuntu/anaconda3/bin:$PATH"`
is the final line of `.bashrc`, or add the line if it isn't. Then,

```
source .bashrc
rm Anaconda3-2018.12-Linux-x86_64.sh
git clone https://github.com/jaryaman/propNews
easy_install tweepy
```

6. Go to https://developer.twitter.com/en/apply-for-access and make a developer account. For the Callback URL, put anything e.g. http://wwwf.imperial.ac.uk/~nsjones/jones.htm. Generate Consumer API keys and Access token & access token secret.

(TODO: Give details on making your own NewsAPI API keys)

7. Make your own version of `twitter_API_keys.txt` and run `main.py`
