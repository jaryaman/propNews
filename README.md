# propNews

Systems &amp; Signals group project for proportionally-reported news.

## Requirements

To run the code, the following files must exist in the directory above this
repository

- `newsapi_key.txt`
- `twitter_API_keys.txt`

see `Dropbox/hackathon_qaly/Tweeting_technical_stuff` which contains these
files. These files are kept in the directory above this repository to avoid accidental
commits to GitHub. Also, the `tweepy` module is required:
```
$ easy_install tweepy
```

## How to run on your own machine

Type:
```
$ python main.py
```

For extra options, type
```
$ python main.py -h
```
for help.

## How to run on an AWS instance

For setting up ssh for the existing AWS instance, see details in
`/Dropbox/hackathon_qaly/Tweeting_technical_stuff/credentials_and_ec2_access.md`

Then,

```
ssh propnews # ssh into the AWS instance
tmux attach # if there are any running sessions
```
If there is a running session, you will see the output from `main.py`. Kill the
process by hitting ctrl+c (or sometimes ctrl+shift+c) a few times.

If there are no running sessions, then
```
tmux
cd propnews
python main.py
```
then `ctrl+b d` to detach the tmux session, and `ctrl+d` to log out of the EC2
instance.

## How to make your own twitter bot

See `setup_EC2_instructions.md` for details.

## Re-scoring the news database
If you change the global priorities file, you may want to re-score the articles without discarding the news database. This can be done with
```
$ python score_articles.py
```
see
```
$ python score_articles.py -h
```
for help

### It's not working!!

Try
```
$ mv news.db news.db.temp
$ python main.py
```
or, for the impatient,
```
$ mv news.db news.db.temp
$ python main.py -d
```
which runs in debug mode (calling the NewsAPI only once).
