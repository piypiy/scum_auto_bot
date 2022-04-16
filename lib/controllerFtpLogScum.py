import requests
import json

import os
import aioftp
import re
import hashlib
import time
from collections import OrderedDict
from datetime import timedelta, timezone
import datetime
from lib.read_config import Read_Config
from plugins import fileio


timestamp_pattern_date = re.compile(r"\d{4}\.\d\d\.\d\d-")
timestamp_pattern_time = re.compile(r"-\d\d\.\d\d\.\d\d")
user_steam_pattern = re.compile(r"\d{16,17}")
user_steam_name_pattern = re.compile(r"\d{16,17}:(.*)\(\d+\)")
login_pattern = re.compile(r"(\d{16,17}):(.*)\((\d+)\)'")
logout_pattern = re.compile(r"(\d+)' logging out")

bug_teleport_to_zone_pattern = re.compile(r"!bug ([A-Za-z0-9]{2})")
buy_car_market_pattern = re.compile(r"!buy_car_market (.*)")


victime_pattern = re.compile(
    r"Died: (.+) \((\d{17})\), Killer: (.+) \((\d{17})\) Weapon: (.+)? S(\[|:)")
victime_killer_pattern = re.compile(
    r"KillerLoc : (-\d+|\d+).(-\d+|\d+), (-\d+|\d+).(-\d+|\d+), (-\d+|\d+).(-\d+|\d+)")
victime_victime_pattern = re.compile(
    r"VictimLoc: (-\d+|\d+).(-\d+|\d+), (-\d+|\d+).(-\d+|\d+), (-\d+|\d+).(-\d+|\d+)")


timestamp_pattern       = re.compile(r"\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d")

file_tmp = 'C:\\Windows\\Temp\\scum_tool_admin_tmp\\'
if(os.path.isdir(file_tmp) == False):
    os.mkdir(file_tmp)

fname = file_tmp+'chat_log.log'
fileio.create_if_not_created(fname)

class Controller_Ftp_Log_Scum(object):

    def __init__(self):
        print("Controller_Ftp_Log_Scum")

    # return all the necessary info to download the logfile

    def get_ftp_config(click_button="left"):
        print("click_button = ", click_button)
        if(click_button == "right"):
            token = Read_Config().getConfig()['storage']['token2']
        else:
            token = Read_Config().getConfig()['storage']['token']

        url = "https://rpfrance.inov-agency.com/info.php?token=" + token

        r = requests.get(url)
        json_obj = json.loads(r.text)

        return (json_obj['ftp']['host'],
                int(json_obj['ftp']['port']),
                json_obj['ftp']['username'],
                json_obj['ftp']['password'],
                json_obj['ftp']['logpath'])

    async def checkLoginUser(click_button="left"):
        last_file_modif = 0
        last_file_chat = ''
        list_user_command = []
        d = datetime.date.today() - timedelta(hours=24, minutes=0, seconds=0)
        time_d = int(d.strftime('%Y%m%d%H%M%S'))
        d = datetime.datetime.now() - timedelta(hours=0, minutes=10, seconds=0)

        host, port, username, password, logpath = Controller_Ftp_Log_Scum.get_ftp_config(
            click_button)

        client = aioftp.Client()
        await client.connect(host, port)
        await client.login(username,  password)

        for filepath, info in await client.list(logpath):
            if "login" not in str(filepath):
                continue
            if(int(info['modify']) > time_d and last_file_modif < int(info['modify'])):
                last_file_modif = int(info['modify'])
                last_file_chat = filepath
                # print(filepath,info['modify'])

        filepath = last_file_chat
        global user_steam_pattern
        if(filepath == ''):
            return False

        data = bytearray()
        pc = 0
        stat = await client.stat(filepath)

        async with client.download_stream(filepath) as stream:
            async for block in stream.iter_by_block():
                data += block
                percent = len(data)/int(stat["size"])
                if pc + percent > .05:
                    pc -= .05

        new_data = data.decode('utf-16')
        with open(file_tmp+'login_new_log.log', 'wb+') as f:
            f.write(str.encode(new_data).decode().encode('utf-8'))
        shakes = open(file_tmp+"login_new_log.log", "r")
        # c_channel = self.get_channel(self.channel_chat_in_game)
        list_login = {}
        for line_chat in shakes:
            line_chat = str(line_chat.strip().lstrip().rstrip())
            timestamp_id_pattern_date = timestamp_pattern_date.findall(
                line_chat)
            timestamp_id_pattern_time = timestamp_pattern_time.findall(
                line_chat)
            user_name_steam = user_steam_name_pattern.findall(line_chat)
            user_steam = user_steam_pattern.findall(line_chat)
            login = login_pattern.findall(line_chat)
            logout = logout_pattern.findall(line_chat)
            if(user_name_steam != []):
                date = timestamp_id_pattern_date[0].replace('-', '').replace(
                    '.', '-') + ' ' + timestamp_id_pattern_time[0].replace('-', '').replace('.', ':')

                utc = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                date_fr = utc.strftime('%H:%M:%S')
                hash_user = hashlib.md5(
                    user_name_steam[0].encode('utf-8')).hexdigest()
                loginDict = {}
                username = str(user_name_steam[0]).lower(
                ).capitalize().strip().rstrip().lstrip()
                if(user_steam[0] == '76561198029980673'
                   or user_steam[0] == '76561199104880775'
                   or user_steam[0] == '76561198335382367'
                   or user_steam[0] == '76561198026254419'):
                    username = '$_'+username
                loginDict = {
                    'hash': hash_user, 'steam_id': user_steam[0], 'name': username, 'date_login': str(date_fr)}
                if(login[0][2] != ''):
                    list_login[login[0][2]] = loginDict
            elif(logout and logout[0] in list_login):
                del list_login[logout[0]]

        list_login = OrderedDict(
            sorted(list_login.items(), key=lambda kv: kv[1]['name']))
        # print(list_login)
        return list_login
        # os.environ['SDL_LOGIN'] = json.dumps(list_login)

    async def checkVictimeUser(click_button="left"):
        try:
            # print('checkVictimeUser')
            last_file_modif = 0
            last_file_chat = ''
            list_user_command = []
            d = datetime.date.today() - timedelta(hours=24, minutes=0, seconds=0)
            time_d = int(d.strftime('%Y%m%d%H%M%S'))

            d = datetime.datetime.now(timezone.utc) - \
                timedelta(hours=0, minutes=10, seconds=0)
            time_gtm = d.strftime('%Y%m%d%H%M%S')

            host, port, username, password, logpath = Controller_Ftp_Log_Scum.get_ftp_config(
                click_button)

            client = aioftp.Client()
            await client.connect(host, port)
            await client.login(username,  password)

            for filepath, info in await client.list(logpath):
                if "kill" not in str(filepath):
                    continue
                if(int(info['modify']) > time_d and last_file_modif < int(info['modify'])):
                    last_file_modif = int(info['modify'])
                    last_file_chat = filepath
                    # print(filepath,info['modify'])

            filepath = last_file_chat
            '''
        for filepath, info in await client.list(logpath):
            if "chat" not in str(filepath):
                continue
            if(int(info['modify']) >  time_d):
        '''
            global user_steam_pattern
            if(filepath == ''):
                return False

            data = bytearray()
            pc = 0
            stat = await client.stat(filepath)

            async with client.download_stream(filepath) as stream:
                async for block in stream.iter_by_block():
                    data += block
                    percent = len(data)/int(stat["size"])
                    if pc + percent > .05:
                        pc -= .05

            new_data = data.decode('utf-16')
            with open(file_tmp+'victime_log4.log', 'wb+') as f:
                f.write(str.encode(new_data).decode().encode('utf-8'))
            shakes = open(file_tmp+"victime_log4.log", "r")
            # c_channel = self.get_channel(self.channel_chat_in_game)
            list_victime = {}

            for line_chat in shakes:
                victime = victime_pattern.findall(line_chat)
                try:
                    if(victime[0][0]):
                        timestamp_id_pattern_date = timestamp_pattern_date.findall(
                            line_chat)
                        timestamp_id_pattern_time = timestamp_pattern_time.findall(
                            line_chat)
                        date = timestamp_id_pattern_date[0].replace('-', '').replace(
                            '.', '/') + ' ' + timestamp_id_pattern_time[0].replace('-', '').replace('.', ':')
                        '''
                    date_string = timestamp_id_pattern_date[0].replace(
                        '-','').replace('.','/')
                    date = datetime.datetime.strptime(date_string, "%Y/%m/%d")
                    timestamp = datetime.datetime.timestamp(date)
                    print(timestamp)
                    '''
                        timestamp = time.mktime(datetime.datetime.strptime(
                            date, "%Y/%m/%d %H:%M:%S").timetuple())+3600
                        timestamp_now = time.time()
                        timestamp_diff = int(timestamp_now) - int(timestamp)
                        # date = timestamp_id_pattern_date[0].replace('-','').replace('.','/')+ '' + timestamp_id_pattern_time[0].replace('-','').replace('.','')
                        victimeDict = {
                            'steam_id_victime': str(victime[0][1]),
                            'name_victime': victime[0][0],
                            'steam_id_killer': str(victime[0][3]),
                            'name_killer': victime[0][2],
                            'timestamp': int(timestamp),
                            'timestamp_diff': timestamp_diff,
                        }
                        if(victime[0][1] != ''):
                            list_victime[victime[0][1]] = victimeDict

                except Exception as e:
                    print(e)
                    pass
            return list_victime
        except Exception as e:
            print(e)

    async def checkCommandUser():
        list_user_command = []
        try:
            url = "https://rpfrance.inov-agency.com/messenger.php?get_message_waiting=true"
            r = requests.get(url)
            json_obj = json.loads(r.text)
            for item in json_obj['item']:
                #message = json.loads(item['message'])
                try:
                    list_user_command.append({'timestamp': item['message']['timestamp'], 'userID': item['message']['userID'],'userName': item['message']['userName'], 'command_chat': item['message']['command_chat'], 'code_banque': item['message']['code_banque'], 'code_shop_banque': item['message']['code_shop_banque'], 'value_item': item['message']['value_item']})
                except:
                    list_user_command.append({'timestamp': item['message']['timestamp'], 'userID': item['message']['userID'],'userName': item['message']['userName'], 'command_chat': item['message']['command_chat']})

        except Exception as e:
            print("Error checkCommandUser:",e)
            pass

        return list_user_command

    async def checkCommandUser2():

        list_user_command = []

        try:

            last_file_modif = 0
            last_file_chat = ''
            d = datetime.date.today() - timedelta(hours=24, minutes=0, seconds=0)
            time_d = int(d.strftime('%Y%m%d%H%M%S'))

            d = datetime.datetime.now(timezone.utc) - timedelta(hours=0, minutes=2, seconds=0)
            time_gtm = d.strftime('%Y%m%d%H%M%S')

            host, port, username, password, logpath = Controller_Ftp_Log_Scum.get_ftp_config()
            print(host, port, username, password, logpath)
            client = aioftp.Client(socket_timeout=10)
            await client.connect(host, port)
            await client.login(username,  password)

            for filepath, info in await client.list(logpath):
                if "chat" not in str(filepath):
                    continue
                if(int(info['modify']) >  time_d and last_file_modif < int(info['modify'])):
                    last_file_modif = int(info['modify'])
                    last_file_chat = filepath
                    print(filepath,info['modify'])

            filepath = last_file_chat
            '''
            for filepath, info in await client.list(logpath):
                if "chat" not in str(filepath):
                    continue
                if(int(info['modify']) >  time_d):
            '''
            global user_steam_pattern
            print(filepath)
            if(filepath == ''):
                return False

            data = bytearray()
            pc = 0
            stat = await client.stat(filepath)

            async with client.download_stream(filepath) as stream:
                async for block in stream.iter_by_block():
                    data += block
                    percent = len(data)/int(stat["size"])
                    if pc + percent > .05:
                        pc -= .05

            # update local copy and return its previous contents
            old_data = fileio.update_binary(fname, data)


            new_data = Controller_Ftp_Log_Scum.log_diff(old_data.decode('utf-16'), data.decode('utf-16'))
            with open(file_tmp+'chat_log4.log', 'wb+') as f:
                f.write(str.encode(new_data).decode().encode('utf-8'))


            shakes = open(file_tmp+"chat_log4.log", "r")

            for line_chat in shakes:
                command = ''
                line_chat = str(line_chat.strip().lstrip().rstrip())
                #user_id_steam_name = user_steam_name_pattern.findall(line_chat)

                if re.match(r"(.+)!entrer", line_chat):
                    command = 'teleport_portal_in'
                elif re.match(r"(.+)!sortir", line_chat):
                    command = 'teleport_portal_out'
                elif re.match(r"(.+)!bug", line_chat):
                    bug_teleport_to_zone = bug_teleport_to_zone_pattern.findall(line_chat)
                    command = 'bug_teleport_to_zone'+str(bug_teleport_to_zone[0])
                elif re.match(r"(.+)!shop_go", line_chat):
                    command = 'go_shop'
                elif re.match(r"(.+)!shop_back", line_chat):
                    command = 'return_position_player'
                elif re.match(r"(.+)!sauter", line_chat):
                    command = 'jump'
                elif re.match(r"(.+)!ping", line_chat):
                    command = 'ping'
                elif re.match(r"(.+)!horde", line_chat):
                    user_id_steam = user_steam_pattern.findall(line_chat)
                    if(user_id_steam[0] == '76561198029980673' or user_id_steam[0] == '76561198026254419'):
                        command = 'horde'
                elif re.match(r"(.+)!restart", line_chat):
                    user_id_steam = user_steam_pattern.findall(line_chat)
                    if(user_id_steam[0] == '76561198029980673' or user_id_steam[0] == '76561198026254419'):
                        command = 'restart'
                '''
                elif re.match(r"(.+)!bot_pack_debutant", line_chat):
                    command = 'claim_starter_pack'
                elif re.match(r"(.+)!buy_car_market", line_chat):
                    buy_car_market = buy_car_market_pattern.findall(line_chat)
                    command = 'buy_car_market_'+str(buy_car_market[0])
                '''

                if(command != ''):
                    timestamp_id_pattern = timestamp_pattern.findall(line_chat)
                    user_id_steam = user_steam_pattern.findall(line_chat)
                    user_name_steam = user_steam_name_pattern.findall(line_chat)

                    if(user_id_steam[0]):
                        timestamp_id = timestamp_id_pattern[0]
                        timestamp_msg = timestamp_id.replace('-','').replace('.','')
                        user_id_steam = user_id_steam[0]
                        user_name_steam = user_name_steam[0]

                        print(timestamp_id,user_id_steam,user_name_steam,command)
                        if(timestamp_msg > time_gtm):
                            list_user_command.append({'timestamp': timestamp_msg, 'userID': user_id_steam,'userName': user_name_steam, 'command_chat': command})



            url = "https://rpfrance.inov-agency.com/messenger.php?get_message_waiting=true"

            r = requests.get(url)
            json_obj = json.loads(r.text)
            try:
                for item in json_obj['item']:
                    #message = json.loads(item['message'])
                    try:
                        list_user_command.append({'timestamp': item['message']['timestamp'], 'userID': item['message']['userID'],'userName': item['message']['userName'], 'command_chat': item['message']['command_chat'], 'code_banque': item['message']['code_banque'], 'code_shop_banque': item['message']['code_shop_banque'], 'value_item': item['message']['value_item']})
                    except:
                        list_user_command.append({'timestamp': item['message']['timestamp'], 'userID': item['message']['userID'],'userName': item['message']['userName'], 'command_chat': item['message']['command_chat']})

            except Exception as e:
                print("Error:",e)
                pass

        except:
            pass

        return list_user_command



    def log_diff(old_data, data):
        #passthrough if no old_data
        if not old_data:
            print("No old data found. All data is new.")
            return data
        data_list = data.strip().split("\n")
        old_data_list = old_data.strip().split("\n")

        global timestamp_pattern
        new_data = ""
        if old_data_list[0] == data_list[0]:
            print("Head match detected; calculating new data.")
            old_size = len(old_data)
            new_data = data[old_size:]
        else:
            print("Head mismatch detected; all data is new.")
            new_data = data
        return new_data
