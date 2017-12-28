This is the supervisor conf

```
[eventlistener:superslack]

command = python super_slack.py
directory = xxxx
user = fibo
autostart = true
autorestart = true
startsecs = 5
startretries = 3
events = PROCESS_STATE_RUNNING,PROCESS_STATE_EXITED,PROCESS_STATE_STOPPED,PROCESS_STATE_FATAL,SUPERVISOR_STATE_CHANGE
stderr_logfile = xxxx.log
```

`super_slack.py` just like a demo. If you want to use it relpace the method from `from base import util` or modify it if you like.

### About webhook:
- install **Incoming WebHooks** on a channel
- put the **webhook url** to the script  or use it modify my script and use it like `python super_slack.py -w xxx` 
