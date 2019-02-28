# propNews
Systems &amp; Signals group project for rationally-reported news

## How to log in to the AWS instance

```
ssh propnews # ssh into the AWS instance
tmux attach # if there are any running sessions
```
If there are running sessions, you will see the output. Otherwise, to run the script

```
tmux
cd propnews
ipython
run main.py
```
then `ctrl+b d` to detach the tmux session, and `ctrl+d` to log out of the EC2 instance
