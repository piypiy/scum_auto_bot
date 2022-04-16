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
# Path to the file
time_random_event = randint(180, 225)
file_name_event_last = r"logs\spawn_event.txt"
fileio.create_if_not_created(file_name_event_last)

PAG.FAILSAFE = False
PAG.PAUSE = 0.18
printToConsole = True

url = "https://rpfrance.inov-agency.com/check_bot.php?status=restart"
r = requests.get(url)

RES = _respond.Respond(printToConsole)
FOC = _focus.Focus(RES)
SCB = _scb.SCB(RES, PAG)
CON = _control.Control(RES, SCB, FOC, PAG)
#CON.stopGame()


PRC_CHAT = _process_chat.Chat(RES, CON, SCB, PAG)
PRC_ACTION = _process_action.Action(RES, CON, SCB, PRC_CHAT, PAG)
PRC = _process.Process(RES, CON, PRC_CHAT, PRC_ACTION, PAG, printToConsole)
RDY = _ready.Ready(RES, FOC, CON, PRC_CHAT)
timezone_paris = tz.gettz('Europe/Paris')

response = None
while response == None:
    try:
        response = subprocess.check_output(
            ['ping', '-n', '1', '-w','2', 'google.fr'],
            stderr=subprocess.STDOUT,  # get all output
            universal_newlines=True  # return string not bytes
        )
        RES.printer("Ping Ok")
    except subprocess.CalledProcessError:
        RES.printer('Error ping')
        response = None
        time.sleep(1)

def isTimeOut(last_time = 0, timeOutMin = 0):
    deltatime = datetime.now(timezone.utc) - timedelta(hours=0, minutes=timeOutMin, seconds=0)
    deltatime = deltatime.strftime('%Y%m%d%H%M%S')
    if(int(last_time) <= int(deltatime)):
        return True

    return False

def getPlayerInfo(steam_id):
    url = "https://rpfrance.inov-agency.com/player.php?steam_id=" + steam_id
    r = requests.get(url)
    json_obj = json.loads(r.text)

    try:
        try:
            return json_obj['list'][0]
        except:
            return json_obj['list']
    except:
        return False


GB_CHK_STATUS = _gamebot_status.CheckStatus(RES, CON, 300)
GB_CHK = _gamebot.Check(RES, CON, 30)

GB_CHK.setBusy(True)
RES.start('START')
if(not RDY.doIt()):
    RES.addError('Unable to get ready (MAIN)')
RES.send()
GB_CHK.setBusy(False)

GB_CHK = _gamebot.Check(RES, CON, 30)
statut = 'start'

PAG.press('esc')
PAG.press('x')
PAG.press('t')

PRC_CHAT.teleportOrigin()
time.sleep(60)
PRC_CHAT.viewInfoPlayer()


'''
prop_user = {
    "userID": "76561198029980673",
    "userName": "El Diablo",
    "messages": {
        "starterPack" : ":[Bot]: ・ @{user} Tu vas recevoir un pack d'objet de départ. Prepares toi à être transporté!",
        },
    "command_chat": "!chat",
    "player_info": getPlayerInfo("76561198029980673"),
    "code_banque": "CBW",
    "code_shop_banque": "CBW",
    "value_item": 105000,
}
PRC_ACTION.banqueWithDrawal(prop_user)
time.sleep(40000)
#'''





listActions = {
    "shop": [-222000, -116916, 2000, 2000],
    "start_pack_point": [-222000, -116916, 2000, 2000],
    "messages": [],
    "list_user_command": [],
}



last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
last_check_new_player = 0
last_check_is_reboot = 0
last_check_alert_reboot = 0
last_check_bot_online = 0
RES.printer("Ready On Load command")
url = "https://rpfrance.inov-agency.com/check_bot.php?status=run"
r = requests.get(url)
loop = True
while loop:
    try:
        RES.printer('statut:' + str(statut))
        response = None
        while response == None:
            try:
                response = subprocess.check_output(
                    ['ping', '-n', '1', '-w','2', 'google.fr'],
                    stderr=subprocess.STDOUT,  # get all output
                    universal_newlines=True  # return string not bytes
                )
                RES.printer("Ping Ok")
            except subprocess.CalledProcessError:
                RES.printer('Error ping')
                response = None
                time.sleep(1)


        if(statut == 'sleep' or statut == 'start'):
            task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkLoginUser())
            loop = asyncio.get_event_loop()
            list_player = loop.run_until_complete(task)
            RES.printer(list_player)
            RES.printer("NbrPlayer sleep: "+str(len(list_player)))

            if(statut == 'sleep' and len(list_player) >= 1):
                GB_CHK.setBusy(False)
                statut = 'run'
                last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                RES.start('START')
                if(not RDY.doIt()):
                    RES.addError('Unable to get ready (MAIN)')
                RES.send()
                PAG.press('esc')
                PAG.press('x')
                PAG.press('t')
                PRC_CHAT.teleportOrigin()
            elif(statut == 'start' and len(list_player) > 1):
                last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                statut = 'run'
                GB_CHK.setBusy(False)
            elif(statut == 'start' and len(list_player) <= 1):
                RES.printer('Sleep No player')
                statut = 'sleep'
                GB_CHK.setBusy(True)
                RES.printer("Ca fait un petit bout de temps que personne n'as commandé! Je m'ennuis. Je rentre me recharger")
                CON.stopGame()
                time.sleep(60)

        elif(statut == 'run'):
            if(GB_CHK.getBusy() and statut != 'start'):
                RES.printer("Bot Busy" + str(GB_CHK.getBusy()))
                sleep(30)
            GB_CHK.setBusy(False)
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
            if(isTimeOut(last_command_user, 30)):
                task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkLoginUser())
                loop = asyncio.get_event_loop()
                list_player = loop.run_until_complete(task)
                #RES.printer(list_player)
                RES.printer("NbrPlayer run:" + str(len(list_player)))
                if(len(list_player) <= 1):
                    RES.printer('Sleep No player')
                    statut = 'sleep'
                    GB_CHK.setBusy(True)
                    RES.printer("Ca fait un petit bout de temps que personne n'as commandé! Je m'ennuis. Je rentre me recharger")
                    CON.stopGame()
                    time.sleep(60)
                    #PAG.keyDown('alt')
                    #PAG.press('F4')
                    #PAG.keyUp('alt')

            time_hour = datetime.now(timezone_paris).strftime('%H%M')
            if(isTimeOut(last_check_new_player, 10)):
                try:
                    GB_CHK.setBusy(True)
                    last_check_new_player = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                    RES.printer('Check new player')
                    #task_newbiland = asyncio.ensure_future(PRC_ACTION.checkIsPlayerNewbieLand())
                    #loop2 = asyncio.get_event_loop()
                    #loop2.run_until_complete(task_newbiland)
                except:
                    pass
                GB_CHK.setBusy(False)

            #HORDE Z
            m_time = os.path.getmtime(file_name_event_last)
            # convert timestamp into DateTime object
            last_time = datetime.fromtimestamp(m_time).strftime('%Y%m%d%H%M%S')
            deltatime = (datetime.now() - timedelta(hours=0, minutes=time_random_event, seconds=0)).strftime('%Y%m%d%H%M%S')
            if(int(last_time) <= int(deltatime)):
                #GB_CHK.setBusy(True)
                time_random_event = randint(180, 225)
                time.sleep(1)
                #PRC_ACTION.spawn_zombie_horde(file_name_event_last)
                #GB_CHK.setBusy(False)
            #HORDE Z

            if(
                (time_hour == '0550' or time_hour == '1150' or time_hour == '1750' or time_hour == '2350')
                and isTimeOut(last_check_alert_reboot,300)
            ):
                last_check_alert_reboot = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                PAG.click(115,500)
                GB_CHK.setBusy(True)
                PRC_CHAT.send("#Announce Tempête dans moins de 10min")
                GB_CHK.setBusy(False)
            elif(time_hour == '0559' or time_hour == '1159' or time_hour == '1759' or time_hour == '2359'):
                statut = 'sleep'
                GB_CHK.setBusy(True)
                CON.stopGame()
                time.sleep(360)
                GB_CHK.setBusy(False)
                statut == 'run'
                RES.start('START')
                if(not RDY.doIt()):
                    RES.addError('Unable to get ready (MAIN)')
                RES.send()
                last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                PAG.press('esc')
                PAG.press('x')
                PAG.press('t')
                PRC_CHAT.teleportOrigin()
                time.sleep(60)
                url = "https://rpfrance.inov-agency.com/check_bot.php?status="+statut
                r = requests.get(url)
                PRC_CHAT.viewInfoPlayer()

        if(GB_CHK.getBusy() == False):
            task = asyncio.ensure_future(Controller_Ftp_Log_Scum.checkCommandUser())
            loop = asyncio.get_event_loop()
            listActions['list_user_command'] = loop.run_until_complete(task)
            RES.printer(listActions)

            if(listActions['list_user_command'] != False and listActions['list_user_command'] != []):
                for user_command in listActions['list_user_command']:
                    last_command_user = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
                    RES.printer(last_command_user)

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
                        "player_info": getPlayerInfo(user_command['userID']),
                        "code_banque": code_banque,
                        "code_shop_banque": code_shop_banque,
                        "value_item": value_item,
                    }
                    RES.printer(prop_user)
                    if(statut == 'sleep'):
                        statut == 'run'
                        GB_CHK.setBusy(False)
                        PRC_ACTION.sendAlertDiscord(prop_user['player_info']['discord_id'],"Bonjour! J\'etais en train de me reposer, le temps d'arriver à mon poste et je suis à toi dans quelques instant pour traiter ta demande.")
                        RES.start('START')
                        if(not RDY.doIt()):
                            RES.addError('Unable to get ready (MAIN)')
                        RES.send()
                        GB_CHK.setBusy(True)
                        PAG.press('esc')
                        PAG.press('x')
                        PAG.press('t')
                        PRC_CHAT.teleportOrigin()
                        time.sleep(60)
                        PRC_CHAT.viewInfoPlayer()
                        GB_CHK.setBusy(False)


                    if(prop_user['player_info'] != False):
                        PAG.click(115,500)
                        GB_CHK.setBusy(True)
                        prop_user = PRC_CHAT.preMsg(prop_user)
                        if(user_command['command_chat'] == 'claim_starter_pack'):
                            RES.printer("Claim Starter Pack"+ user_command['command_chat'])
                            PRC_ACTION.getStarterPack(prop_user)
                        elif(user_command['command_chat'] == 'teleport_portal_in'):
                            PRC_ACTION.teleportPortal('in',prop_user)
                        elif(user_command['command_chat'] == 'teleport_portal_out'):
                            PRC_ACTION.teleportPortal('out',prop_user)
                        elif(user_command['command_chat'] == 'jump'):
                            PRC_ACTION.teleportToJump(prop_user)
                        elif(user_command['command_chat'] == 'horde'):
                            time_random_event = randint(180, 225)
                            PRC_ACTION.spawnZombieHorde(file_name_event_last)
                        elif(user_command['command_chat'] == 'restart'):
                            CON.restart()
                            time.sleep(120)
                        elif(user_command['command_chat'] == 'ping'):
                            PRC_CHAT.send("Pong")
                        elif(user_command['command_chat'] == 'go_shop'):
                            PRC_ACTION.teleportToShop(prop_user)
                        elif(user_command['command_chat'] == 'return_position_players'):
                            PRC_ACTION.teleportUserLastPos(prop_user)
                        elif(user_command['command_chat'] == 'teleport_event'):
                            PRC_ACTION.teleportUserToEvent(prop_user)
                        elif(user_command['command_chat'] == 'teleport_event_dead'):
                            PRC_ACTION.teleportUserToEvent(prop_user, False)
                        elif(user_command['command_chat'].lower().startswith('bug_teleport_to_zone')):
                            PRC_ACTION.teleportToZone(prop_user)
                        elif(user_command['command_chat'].lower().startswith('buy_car_market')):
                            PRC_ACTION.buyCarMarket(prop_user)
                        elif(user_command['command_chat'].lower().startswith('buy_aircraft_market_player')):
                            PRC_ACTION.buyAirCraftMarket(prop_user,'player')
                        elif(user_command['command_chat'].lower().startswith('buy_boat_market_player')):
                            PRC_ACTION.buyBoatMarket(prop_user,'player')
                        elif(user_command['command_chat'].lower().startswith('buy_aircraft_market')):
                            PRC_ACTION.buyAirCraftMarket(prop_user,'market')
                        elif(user_command['command_chat'].lower().startswith('banque_withdrawal_money')):
                            PRC_ACTION.banqueWithDrawal(prop_user)
                        GB_CHK.setBusy(False)

                            #PRC_ACTION.getStarterPack(prop_user)

                        '''
                        elif(user_command['command_chat'] == 'bank_chest'):
                            PRC_ACTION.teleportToBankChest(prop_user)
                        elif(user_command['command_chat'] == 'bank_entrance'):
                            PRC_ACTION.teleportToBank(prop_user, 'entrance')
                        elif(user_command['command_chat'] == 'bank_exit'):
                            PRC_ACTION.teleportToBank(prop_user, 'exit')
                        elif(user_command['command_chat'] == 'go_shop'):
                            PRC_ACTION.teleportToShop(prop_user)
                        elif(user_command['command_chat'] == 'back_shop'):
                            PRC_ACTION.teleportUserLastPos(prop_user)
                        '''
                        #elif(re.match(r"bug_teleport_to_zone", user_command['command_chat'])):
        else:
            RES.printer("Bot is busy")

    except Exception as e:
        RES.printer('Error in main loop'+ str(e))
        try:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            RES.addError(str(e), str(exception_type))
            RES.send()
            if(not RDY.doIt()):
                CON.restart()
                time.sleep(120)
        except:
            CON.restart()
            time.sleep(120)
            pass

    try:
        if(statut == 'run' or statut == 'start'):
            GB_CHK.setBusy(False)

        deltatime = datetime.now(timezone.utc) - timedelta(hours=0, minutes=30, seconds=0)
        deltatime = deltatime.strftime('%Y%m%d%H%M%S')

        if(last_check_bot_online >= 4):
            try:
                last_check_bot_online = 0
                url = "https://rpfrance.inov-agency.com/check_bot.php?status="+statut
                r = requests.get(url)
                RES.printer('last_check_bot_online status update')
            except:
                RES.printer('Error in check bot online')
                pass
        last_check_bot_online = last_check_bot_online + 1

        print('End Loops', last_command_user,last_check_bot_online)
        if(int(last_command_user) >= int(deltatime)):
            time.sleep(10)
        else:
            time.sleep(30)
    except Exception as e:
        print('Erorr in main loop Final: '+ str(e))


'''
RES.printer(FOC.doIt())
if(FOC.doIt()):
  RES.printer(FOC.getWindowProps())
else:
  RES.printer('Failed to focus game')
'''