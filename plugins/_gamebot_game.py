from urllib.parse import unquote
from threading import Thread
import time
import sys

from time import sleep
from plugins import _process_action
from plugins import _process_chat
from plugins import _process
from plugins import _gamebot
from plugins import _gamebot_status
from plugins import _ready
from plugins import _respond
from plugins import _control
from plugins import _focus
from plugins import _scb
from dateutil import tz
import pyautogui as PAG
import os,sys
from lib.controllerFtpLogScum import Controller_Ftp_Log_Scum

import configparser
import time, pytz
from datetime import datetime, timedelta, timezone
import requests, json, asyncio, re
from random import *
import subprocess
import lib.fileio as fileio


class RunBot(Thread):


    def __init__(self, respond, control, ready, process, gb_chk, prc_chat, prc_action, test = False):
        Thread.__init__(self)
        self.daemon = True
        self.RES = respond
        self.CON = control
        self.PRC = process
        self.RDY = ready
        self.test = test
        self.GB_CHK = gb_chk
        self.PRC_CHAT = prc_chat
        self.PRC_ACTION = prc_action
        self.start()

    def run(self):
        global busyWork
        #global busyCheck
        try:
          listActions = {
              "shop": [-222000, -116916, 2000, 2000],
              "start_pack_point": [-222000, -116916, 2000, 2000],
              "messages": [],
              "list_user_command": [],
          }

          time_random_event = randint(180, 225)
          file_name_event_last = r"logs\spawn_event.txt"
          fileio.create_if_not_created(file_name_event_last)
          timezone_paris = tz.gettz('Europe/Paris')
          statut = 'start'

          PAG.press('esc')
          PAG.press('x')
          PAG.press('t')

          self.PRC_CHAT.teleportOrigin()
          time.sleep(1)
          self.PRC_CHAT.viewInfoPlayer()

          last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
          last_check_new_player = 0
          last_check_is_reboot = 0
          last_check_alert_reboot = 0
          last_check_bot_online = 0
          self.RES.printer("Ready On Load command")
          url = "https://rpfrance.inov-agency.com/check_bot.php?status=run"
          r = requests.get(url)

          while True:
              try:
                  print('Running...')
                  try:
                      self.RES.printer('statut:' + str(statut))
                      response = None
                      while response == None:
                          try:
                              response = subprocess.check_output(
                                  ['ping', '-n', '1', '-w','2', 'google.fr'],
                                  stderr=subprocess.STDOUT,  # get all output
                                  universal_newlines=True  # return string not bytes
                              )
                              self.RES.printer("Ping Ok")
                          except subprocess.CalledProcessError:
                              self.RES.printer('Error ping')
                              response = None
                              time.sleep(1)


                      if(statut == 'sleep' or statut == 'start'):
                          task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkLoginUser())
                          #loop = asyncio.get_event_loop()
                          loop = asyncio.new_event_loop()
                          asyncio.set_event_loop(loop)
                          list_player = loop.run_until_complete(task)
                          self.RES.printer(list_player)
                          self.RES.printer("NbrPlayer sleep: "+str(len(list_player)))

                          if(statut == 'sleep' and len(list_player) >= 1):
                              self.GB_CHK.setBusy(False)
                              statut = 'run'
                              last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                              self.RES.start('START')
                              if(not self.self.RDY.doIt()):
                                  self.RES.addError('Unable to get ready (MAIN)')
                              self.RES.send()
                              PAG.press('esc')
                              PAG.press('x')
                              PAG.press('t')
                              self.PRC_CHAT.teleportOrigin()
                          elif(statut == 'start' and len(list_player) > 1):
                              last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                              statut = 'run'
                              self.GB_CHK.setBusy(False)
                          elif(statut == 'start' and len(list_player) <= 1):
                              self.RES.printer('Sleep No player')
                              statut = 'sleep'
                              self.GB_CHK.setBusy(True)
                              self.RES.printer("Ca fait un petit bout de temps que personne n'as commandé! Je m'ennuis. Je rentre me recharger")
                              self.CON.stopGame()
                              time.sleep(60)

                      elif(statut == 'run'):
                          if(self.GB_CHK.getBusy() and statut != 'start'):
                              self.RES.printer("Bot Busy" + str(self.GB_CHK.getBusy()))
                              sleep(30)
                          self.GB_CHK.setBusy(False)
                          '''
                          if(statut == 'start'):
                              last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                              statut = 'run'
                          '''

                          '''
                          deltatime = datetime.now(timezone.utc) - timedelta(hours=0, minutes=20, seconds=0)
                          deltatime = deltatime.strftime('%Y%m%d%H%M%S')
                          if(int(last_command_user) <= int(deltatime)):
                          '''
                          if(self.isTimeOut(last_command_user, 30)):
                              task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkLoginUser())
                              #loop = asyncio.get_event_loop()
                              loop = asyncio.new_event_loop()
                              asyncio.set_event_loop(loop)
                              list_player = loop.run_until_complete(task)
                              #self.RES.printer(list_player)
                              self.RES.printer("NbrPlayer run:" + str(len(list_player)))
                              if(len(list_player) <= 1):
                                  self.RES.printer('Sleep No player')
                                  statut = 'sleep'
                                  self.GB_CHK.setBusy(True)
                                  self.RES.printer("Ca fait un petit bout de temps que personne n'as commandé! Je m'ennuis. Je rentre me recharger")
                                  self.CON.stopGame()
                                  time.sleep(60)
                                  #PAG.keyDown('alt')
                                  #PAG.press('F4')
                                  #PAG.keyUp('alt')

                          time_hour = datetime.now(timezone_paris).strftime('%H%M')
                          if(self.isTimeOut(last_check_new_player, 10)):
                              try:
                                  self.GB_CHK.setBusy(True)
                                  last_check_new_player = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                                  self.RES.printer('Check new player')
                                  #task_newbiland = asyncio.ensure_future(self.PRC_ACTION.checkIsPlayerNewbieLand())
                                  #loop2 = asyncio.get_event_loop()
                                  #loop2.run_until_complete(task_newbiland)
                              except:
                                  pass
                              self.GB_CHK.setBusy(False)

                          #HORDE Z
                          m_time = os.path.getmtime(file_name_event_last)
                          # convert timestamp into DateTime object
                          last_time = datetime.fromtimestamp(m_time).strftime('%Y%m%d%H%M%S')
                          deltatime = (datetime.now() - timedelta(hours=0, minutes=time_random_event, seconds=0)).strftime('%Y%m%d%H%M%S')
                          if(int(last_time) <= int(deltatime)):
                              #self.GB_CHK.setBusy(True)
                              time_random_event = randint(180, 225)
                              time.sleep(1)
                              #self.PRC_ACTION.spawn_zombie_horde(file_name_event_last)
                              #self.GB_CHK.setBusy(False)
                          #HORDE Z

                          if(
                              (time_hour == '0550' or time_hour == '1150' or time_hour == '1750' or time_hour == '2350')
                              and self.isTimeOut(last_check_alert_reboot,300)
                          ):
                              last_check_alert_reboot = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                              PAG.click(115,500)
                              self.GB_CHK.setBusy(True)
                              self.PRC_CHAT.send("#Announce Tempête dans moins de 10min")
                              self.GB_CHK.setBusy(False)
                          elif(time_hour == '0559' or time_hour == '1159' or time_hour == '1759' or time_hour == '2359'):
                              statut = 'sleep'
                              self.GB_CHK.setBusy(True)
                              self.CON.stopGame()
                              time.sleep(360)
                              self.GB_CHK.setBusy(False)
                              statut == 'run'
                              self.RES.start('START')
                              if(not self.self.RDY.doIt()):
                                  self.RES.addError('Unable to get ready (MAIN)')
                              self.RES.send()
                              last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                              PAG.press('esc')
                              PAG.press('x')
                              PAG.press('t')
                              self.PRC_CHAT.teleportOrigin()
                              time.sleep(60)
                              url = "https://rpfrance.inov-agency.com/check_bot.php?status="+statut
                              r = requests.get(url)
                              self.PRC_CHAT.viewInfoPlayer()

                      if(self.GB_CHK.getBusy() == False):
                          task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkCommandUser())
                          #loop = asyncio.get_event_loop()
                          loop = asyncio.new_event_loop()
                          asyncio.set_event_loop(loop)
                          listActions['list_user_command'] = loop.run_until_complete(task)
                          self.RES.printer(listActions)

                          if(listActions['list_user_command'] != False and listActions['list_user_command'] != []):
                              for user_command in listActions['list_user_command']:
                                  last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                                  self.RES.printer(last_command_user)

                                  code_banque = ''
                                  code_shop_banque = ''
                                  value_item = 0
                                  try:
                                      code_banque = user_command['code_banque']
                                      code_shop_banque = user_command['code_shop_banque']
                                      value_item = int(user_command['value_item'])
                                  except:
                                      pass

                                  prop_user = {
                                      "userID": user_command['userID'],
                                      "userName": user_command['userName'],
                                      "messages": {
                                          "starterPack" : ":[Bot]: ・ @{user} Tu vas recevoir un pack d'objet de départ. Prepares toi à être transporté!",
                                          },
                                      "command_chat": user_command['command_chat'],
                                      "player_info": self.getPlayerInfo(user_command['userID']),
                                      "code_banque": code_banque,
                                      "code_shop_banque": code_shop_banque,
                                      "value_item": value_item,
                                  }
                                  self.RES.printer(prop_user)
                                  if(statut == 'sleep'):
                                      statut == 'run'
                                      self.GB_CHK.setBusy(False)
                                      self.PRC_ACTION.sendAlertDiscord(prop_user['player_info']['discord_id'],"Bonjour! J\'etais en train de me reposer, le temps d'arriver à mon poste et je suis à toi dans quelques instant pour traiter ta demande.")
                                      self.RES.start('START')
                                      if(not self.self.RDY.doIt()):
                                          self.RES.addError('Unable to get ready (MAIN)')
                                      self.RES.send()
                                      self.GB_CHK.setBusy(True)
                                      PAG.press('esc')
                                      PAG.press('x')
                                      PAG.press('t')
                                      self.PRC_CHAT.teleportOrigin()
                                      time.sleep(60)
                                      self.PRC_CHAT.viewInfoPlayer()
                                      self.GB_CHK.setBusy(False)


                                  if(prop_user['player_info'] != False):
                                      PAG.click(115,500)
                                      self.GB_CHK.setBusy(True)
                                      prop_user = self.PRC_CHAT.preMsg(prop_user)
                                      if(user_command['command_chat'] == 'claim_starter_pack'):
                                          self.RES.printer("Claim Starter Pack"+ user_command['command_chat'])
                                          self.PRC_ACTION.getStarterPack(prop_user)
                                      elif(user_command['command_chat'] == 'teleport_portal_in'):
                                          self.PRC_ACTION.teleportPortal('in',prop_user)
                                      elif(user_command['command_chat'] == 'teleport_portal_out'):
                                          self.PRC_ACTION.teleportPortal('out',prop_user)
                                      elif(user_command['command_chat'] == 'jump'):
                                          self.PRC_ACTION.teleportToJump(prop_user)
                                      elif(user_command['command_chat'] == 'horde'):
                                          time_random_event = randint(180, 225)
                                          self.PRC_ACTION.spawnZombieHorde(file_name_event_last)
                                      elif(user_command['command_chat'] == 'restart'):
                                          self.CON.restart()
                                          time.sleep(120)
                                      elif(user_command['command_chat'] == 'ping'):
                                          self.PRC_CHAT.send("Pong")
                                      elif(user_command['command_chat'] == 'go_shop'):
                                          self.PRC_ACTION.teleportToShop(prop_user)
                                      elif(user_command['command_chat'] == 'return_position_players'):
                                          self.PRC_ACTION.teleportUserLastPos(prop_user)
                                      elif(user_command['command_chat'] == 'teleport_event'):
                                          self.PRC_ACTION.teleportUserToEvent(prop_user)
                                      elif(user_command['command_chat'] == 'teleport_event_dead'):
                                          self.PRC_ACTION.teleportUserToEvent(prop_user, False)
                                      elif(user_command['command_chat'].lower().startswith('bug_teleport_to_zone')):
                                          self.PRC_ACTION.teleportToZone(prop_user)
                                      elif(user_command['command_chat'].lower().startswith('buy_car_market')):
                                          self.PRC_ACTION.buyCarMarket(prop_user)
                                      elif(user_command['command_chat'].lower().startswith('buy_aircraft_market_player')):
                                          self.PRC_ACTION.buyAirCraftMarket(prop_user,'player')
                                      elif(user_command['command_chat'].lower().startswith('buy_boat_market_player')):
                                          self.PRC_ACTION.buyBoatMarket(prop_user,'player')
                                      elif(user_command['command_chat'].lower().startswith('buy_aircraft_market')):
                                          self.PRC_ACTION.buyAirCraftMarket(prop_user,'market')
                                      elif(user_command['command_chat'].lower().startswith('banque_withdrawal_money')):
                                          self.PRC_ACTION.banqueWithDrawal(prop_user)
                                      self.GB_CHK.setBusy(False)

                                          #self.PRC_ACTION.getStarterPack(prop_user)

                                      '''
                                      elif(user_command['command_chat'] == 'bank_chest'):
                                          self.PRC_ACTION.teleportToBankChest(prop_user)
                                      elif(user_command['command_chat'] == 'bank_entrance'):
                                          self.PRC_ACTION.teleportToBank(prop_user, 'entrance')
                                      elif(user_command['command_chat'] == 'bank_exit'):
                                          self.PRC_ACTION.teleportToBank(prop_user, 'exit')
                                      elif(user_command['command_chat'] == 'go_shop'):
                                          self.PRC_ACTION.teleportToShop(prop_user)
                                      elif(user_command['command_chat'] == 'back_shop'):
                                          self.PRC_ACTION.teleportUserLastPos(prop_user)
                                      '''
                                      #elif(re.match(r"bug_teleport_to_zone", user_command['command_chat'])):
                      else:
                          self.RES.printer("Bot is busy")

                  except Exception as e:
                      self.RES.printer('Error in main loop'+ str(e))
                      try:
                          exception_type, exception_object, exception_traceback = sys.exc_info()
                          self.RES.addError(str(e), str(exception_type))
                          self.RES.send()
                          if(not self.self.RDY.doIt()):
                              self.CON.restart()
                              time.sleep(120)
                      except:
                          self.CON.restart()
                          time.sleep(120)
                          pass
                  if(statut == 'run' or statut == 'start'):
                      self.GB_CHK.setBusy(False)

                  deltatime = datetime.now(timezone.utc) - timedelta(hours=0, minutes=30, seconds=0)
                  deltatime = deltatime.strftime('%Y%m%d%H%M%S')

                  self.RES.printer('AT END??')

                  if(last_check_bot_online >= 4):
                      try:
                          last_check_bot_online = 0
                          url = "https://rpfrance.inov-agency.com/check_bot.php?status="+statut
                          r = requests.get(url)
                          self.RES.printer('last_check_bot_online status update')
                      except:
                          self.RES.printer('Error in check bot online')
                          pass
                  last_check_bot_online = last_check_bot_online + 1

                  if(int(last_command_user) >= int(deltatime)):
                      time.sleep(20)
                  else:
                      time.sleep(45)
              except Exception as e:
                  print("gamebot_run",e)

        except Exception as e:
          print(e)



    def runttt(self):
        listActions = {
            "shop": [-222000, -116916, 2000, 2000],
            "start_pack_point": [-222000, -116916, 2000, 2000],
            "messages": [],
            "list_user_command": [],
        }

        time_random_event = randint(180, 225)
        file_name_event_last = r"logs\spawn_event.txt"
        fileio.create_if_not_created(file_name_event_last)
        timezone_paris = tz.gettz('Europe/Paris')
        statut = 'start'

        PAG.press('esc')
        PAG.press('x')
        PAG.press('t')

        self.PRC_CHAT.teleportOrigin()
        time.sleep(60)
        self.PRC_CHAT.viewInfoPlayer()

        last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        last_check_new_player = 0
        last_check_is_reboot = 0
        last_check_alert_reboot = 0
        last_check_bot_online = 0
        self.RES.printer("Ready On Load command")
        url = "https://rpfrance.inov-agency.com/check_bot.php?status=run"
        r = requests.get(url)
        loop = True
        while True:
            print('loop :) ')
            try:
                self.RES.printer('statut:' + str(statut))
                response = None
                while response == None:
                    try:
                        response = subprocess.check_output(
                            ['ping', '-n', '1', '-w','2', 'google.fr'],
                            stderr=subprocess.STDOUT,  # get all output
                            universal_newlines=True  # return string not bytes
                        )
                        self.RES.printer("Ping Ok")
                    except subprocess.CalledProcessError:
                        self.RES.printer('Error ping')
                        response = None
                        time.sleep(1)


                if(statut == 'sleep' or statut == 'start'):
                    task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkLoginUser())
                    #loop = asyncio.get_event_loop()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    list_player = loop.run_until_complete(task)
                    self.RES.printer(list_player)
                    self.RES.printer("NbrPlayer sleep: "+str(len(list_player)))

                    if(statut == 'sleep' and len(list_player) >= 1):
                        self.GB_CHK.setBusy(False)
                        statut = 'run'
                        last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                        self.RES.start('START')
                        if(not self.self.RDY.doIt()):
                            self.RES.addError('Unable to get ready (MAIN)')
                        self.RES.send()
                        PAG.press('esc')
                        PAG.press('x')
                        PAG.press('t')
                        self.PRC_CHAT.teleportOrigin()
                    elif(statut == 'start' and len(list_player) > 1):
                        last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                        statut = 'run'
                        self.GB_CHK.setBusy(False)
                    elif(statut == 'start' and len(list_player) <= 1):
                        self.RES.printer('Sleep No player')
                        statut = 'sleep'
                        self.GB_CHK.setBusy(True)
                        self.RES.printer("Ca fait un petit bout de temps que personne n'as commandé! Je m'ennuis. Je rentre me recharger")
                        self.CON.stopGame()
                        time.sleep(60)

                elif(statut == 'run'):
                    if(self.GB_CHK.getBusy() and statut != 'start'):
                        self.RES.printer("Bot Busy" + str(self.GB_CHK.getBusy()))
                        sleep(30)
                    self.GB_CHK.setBusy(False)
                    '''
                    if(statut == 'start'):
                        last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                        statut = 'run'
                    '''

                    '''
                    deltatime = datetime.now(timezone.utc) - timedelta(hours=0, minutes=20, seconds=0)
                    deltatime = deltatime.strftime('%Y%m%d%H%M%S')
                    if(int(last_command_user) <= int(deltatime)):
                    '''
                    if(self.isTimeOut(last_command_user, 30)):
                        task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkLoginUser())
                        #loop = asyncio.get_event_loop()
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        list_player = loop.run_until_complete(task)
                        #self.RES.printer(list_player)
                        self.RES.printer("NbrPlayer run:" + str(len(list_player)))
                        if(len(list_player) <= 1):
                            self.RES.printer('Sleep No player')
                            statut = 'sleep'
                            self.GB_CHK.setBusy(True)
                            self.RES.printer("Ca fait un petit bout de temps que personne n'as commandé! Je m'ennuis. Je rentre me recharger")
                            self.CON.stopGame()
                            time.sleep(60)
                            #PAG.keyDown('alt')
                            #PAG.press('F4')
                            #PAG.keyUp('alt')

                    time_hour = datetime.now(timezone_paris).strftime('%H%M')
                    if(self.isTimeOut(last_check_new_player, 10)):
                        try:
                            self.GB_CHK.setBusy(True)
                            last_check_new_player = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                            self.RES.printer('Check new player')
                            #task_newbiland = asyncio.ensure_future(self.PRC_ACTION.checkIsPlayerNewbieLand())
                            #loop2 = asyncio.get_event_loop()
                            #loop2.run_until_complete(task_newbiland)
                        except:
                            pass
                        self.GB_CHK.setBusy(False)

                    #HORDE Z
                    m_time = os.path.getmtime(file_name_event_last)
                    # convert timestamp into DateTime object
                    last_time = datetime.fromtimestamp(m_time).strftime('%Y%m%d%H%M%S')
                    deltatime = (datetime.now() - timedelta(hours=0, minutes=time_random_event, seconds=0)).strftime('%Y%m%d%H%M%S')
                    if(int(last_time) <= int(deltatime)):
                        #self.GB_CHK.setBusy(True)
                        time_random_event = randint(180, 225)
                        time.sleep(1)
                        #self.PRC_ACTION.spawn_zombie_horde(file_name_event_last)
                        #self.GB_CHK.setBusy(False)
                    #HORDE Z

                    if(
                        (time_hour == '0550' or time_hour == '1150' or time_hour == '1750' or time_hour == '2350')
                        and self.isTimeOut(last_check_alert_reboot,300)
                    ):
                        last_check_alert_reboot = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                        PAG.click(115,500)
                        self.GB_CHK.setBusy(True)
                        self.PRC_CHAT.send("#Announce Tempête dans moins de 10min")
                        self.GB_CHK.setBusy(False)
                    elif(time_hour == '0559' or time_hour == '1159' or time_hour == '1759' or time_hour == '2359'):
                        statut = 'sleep'
                        self.GB_CHK.setBusy(True)
                        self.CON.stopGame()
                        time.sleep(360)
                        self.GB_CHK.setBusy(False)
                        statut == 'run'
                        self.RES.start('START')
                        if(not self.self.RDY.doIt()):
                            self.RES.addError('Unable to get ready (MAIN)')
                        self.RES.send()
                        last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                        PAG.press('esc')
                        PAG.press('x')
                        PAG.press('t')
                        self.PRC_CHAT.teleportOrigin()
                        time.sleep(60)
                        url = "https://rpfrance.inov-agency.com/check_bot.php?status="+statut
                        r = requests.get(url)
                        self.PRC_CHAT.viewInfoPlayer()

                if(self.GB_CHK.getBusy() == False):
                    task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkCommandUser())
                    #loop = asyncio.get_event_loop()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    listActions['list_user_command'] = loop.run_until_complete(task)
                    self.RES.printer(listActions)

                    if(listActions['list_user_command'] != False and listActions['list_user_command'] != []):
                        for user_command in listActions['list_user_command']:
                            last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                            self.RES.printer(last_command_user)

                            code_banque = ''
                            code_shop_banque = ''
                            value_item = 0
                            try:
                                code_banque = user_command['code_banque']
                                code_shop_banque = user_command['code_shop_banque']
                                value_item = int(user_command['value_item'])
                            except:
                                pass

                            prop_user = {
                                "userID": user_command['userID'],
                                "userName": user_command['userName'],
                                "messages": {
                                    "starterPack" : ":[Bot]: ・ @{user} Tu vas recevoir un pack d'objet de départ. Prepares toi à être transporté!",
                                    },
                                "command_chat": user_command['command_chat'],
                                "player_info": self.getPlayerInfo(user_command['userID']),
                                "code_banque": code_banque,
                                "code_shop_banque": code_shop_banque,
                                "value_item": value_item,
                            }
                            self.RES.printer(prop_user)
                            if(statut == 'sleep'):
                                statut == 'run'
                                self.GB_CHK.setBusy(False)
                                self.PRC_ACTION.sendAlertDiscord(prop_user['player_info']['discord_id'],"Bonjour! J\'etais en train de me reposer, le temps d'arriver à mon poste et je suis à toi dans quelques instant pour traiter ta demande.")
                                self.RES.start('START')
                                if(not self.self.RDY.doIt()):
                                    self.RES.addError('Unable to get ready (MAIN)')
                                self.RES.send()
                                self.GB_CHK.setBusy(True)
                                PAG.press('esc')
                                PAG.press('x')
                                PAG.press('t')
                                self.PRC_CHAT.teleportOrigin()
                                time.sleep(60)
                                self.PRC_CHAT.viewInfoPlayer()
                                self.GB_CHK.setBusy(False)


                            if(prop_user['player_info'] != False):
                                PAG.click(115,500)
                                self.GB_CHK.setBusy(True)
                                prop_user = self.PRC_CHAT.preMsg(prop_user)
                                if(user_command['command_chat'] == 'claim_starter_pack'):
                                    self.RES.printer("Claim Starter Pack"+ user_command['command_chat'])
                                    self.PRC_ACTION.getStarterPack(prop_user)
                                elif(user_command['command_chat'] == 'teleport_portal_in'):
                                    self.PRC_ACTION.teleportPortal('in',prop_user)
                                elif(user_command['command_chat'] == 'teleport_portal_out'):
                                    self.PRC_ACTION.teleportPortal('out',prop_user)
                                elif(user_command['command_chat'] == 'jump'):
                                    self.PRC_ACTION.teleportToJump(prop_user)
                                elif(user_command['command_chat'] == 'horde'):
                                    time_random_event = randint(180, 225)
                                    self.PRC_ACTION.spawnZombieHorde(file_name_event_last)
                                elif(user_command['command_chat'] == 'restart'):
                                    self.CON.restart()
                                    time.sleep(120)
                                elif(user_command['command_chat'] == 'ping'):
                                    self.PRC_CHAT.send("Pong")
                                elif(user_command['command_chat'] == 'go_shop'):
                                    self.PRC_ACTION.teleportToShop(prop_user)
                                elif(user_command['command_chat'] == 'return_position_players'):
                                    self.PRC_ACTION.teleportUserLastPos(prop_user)
                                elif(user_command['command_chat'] == 'teleport_event'):
                                    self.PRC_ACTION.teleportUserToEvent(prop_user)
                                elif(user_command['command_chat'] == 'teleport_event_dead'):
                                    self.PRC_ACTION.teleportUserToEvent(prop_user, False)
                                elif(user_command['command_chat'].lower().startswith('bug_teleport_to_zone')):
                                    self.PRC_ACTION.teleportToZone(prop_user)
                                elif(user_command['command_chat'].lower().startswith('buy_car_market')):
                                    self.PRC_ACTION.buyCarMarket(prop_user)
                                elif(user_command['command_chat'].lower().startswith('buy_aircraft_market_player')):
                                    self.PRC_ACTION.buyAirCraftMarket(prop_user,'player')
                                elif(user_command['command_chat'].lower().startswith('buy_boat_market_player')):
                                    self.PRC_ACTION.buyBoatMarket(prop_user,'player')
                                elif(user_command['command_chat'].lower().startswith('buy_aircraft_market')):
                                    self.PRC_ACTION.buyAirCraftMarket(prop_user,'market')
                                elif(user_command['command_chat'].lower().startswith('banque_withdrawal_money')):
                                    self.PRC_ACTION.banqueWithDrawal(prop_user)
                                self.GB_CHK.setBusy(False)

                                    #self.PRC_ACTION.getStarterPack(prop_user)

                                '''
                                elif(user_command['command_chat'] == 'bank_chest'):
                                    self.PRC_ACTION.teleportToBankChest(prop_user)
                                elif(user_command['command_chat'] == 'bank_entrance'):
                                    self.PRC_ACTION.teleportToBank(prop_user, 'entrance')
                                elif(user_command['command_chat'] == 'bank_exit'):
                                    self.PRC_ACTION.teleportToBank(prop_user, 'exit')
                                elif(user_command['command_chat'] == 'go_shop'):
                                    self.PRC_ACTION.teleportToShop(prop_user)
                                elif(user_command['command_chat'] == 'back_shop'):
                                    self.PRC_ACTION.teleportUserLastPos(prop_user)
                                '''
                                #elif(re.match(r"bug_teleport_to_zone", user_command['command_chat'])):
                else:
                    self.RES.printer("Bot is busy")

            except Exception as e:
                self.RES.printer('Error in main loop'+ str(e))
                try:
                    exception_type, exception_object, exception_traceback = sys.exc_info()
                    self.RES.addError(str(e), str(exception_type))
                    self.RES.send()
                    if(not self.self.RDY.doIt()):
                        self.CON.restart()
                        time.sleep(120)
                except:
                    self.CON.restart()
                    time.sleep(120)
                    pass
            if(statut == 'run' or statut == 'start'):
                self.GB_CHK.setBusy(False)

            deltatime = datetime.now(timezone.utc) - timedelta(hours=0, minutes=30, seconds=0)
            deltatime = deltatime.strftime('%Y%m%d%H%M%S')

            self.RES.printer('AT END??')

            if(last_check_bot_online >= 4):
                try:
                    last_check_bot_online = 0
                    url = "https://rpfrance.inov-agency.com/check_bot.php?status="+statut
                    r = requests.get(url)
                    self.RES.printer('last_check_bot_online status update')
                except:
                    self.RES.printer('Error in check bot online')
                    pass
            last_check_bot_online = last_check_bot_online + 1

            if(int(last_command_user) >= int(deltatime)):
                time.sleep(20)
            else:
                time.sleep(45)
