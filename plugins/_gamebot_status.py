from urllib import response
from urllib.parse import unquote
from threading import Thread
import datetime
from datetime import timedelta, timezone
import time
import sys
import requests
import json


busyWork = True
busyCheck = False


class CheckStatus(Thread):

    RES = None
    CON = None
    interval = None

    def __init__(self, respond, control, interval = 10):
        Thread.__init__(self)
        self.interval = interval
        self.RES = respond
        self.CON = control
        self.daemon = True
        self.start()

    def run(self):
        global busyWork
        #global busyCheck
        while True:
            try:
              deltatime = datetime.datetime.now(timezone.utc) - timedelta(hours=0, minutes=6, seconds=0)
              deltatime = deltatime.strftime('%Y%m%d%H%M%S')
              url = "https://rpfrance.inov-agency.com/check_bot.php?check=true&time="+str(deltatime)
              r = requests.get(url)
              json_obj = json.loads(r.text)
              #print(deltatime, json_obj['last_check'])
              if(int(json_obj['last_check']) <= int(deltatime)):
                  #print('Off Line : '+str(int(deltatime)-int(json_obj['last_check'])))
                  if(json_obj['status'] == 'restart'):
                      emoji = "♻️"
                  else:
                      url = "https://rpfrance.inov-agency.com/check_bot.php?status=restart"
                      r = requests.get(url)
                      emoji = "🔴"
                      self.RES.addError('Unable to get ready (GB_CHK)')
                      self.RES.send()
                      self.CON.restart()
                      time.sleep(120)
              else:
                  if(json_obj['status'] == 'run'):
                      emoji = "🟢"
                  else:
                      emoji = "🟡"
              print("Status Bot",emoji)
              time.sleep(self.interval)
            except Exception as e:
                print("gamebot_run",e)


