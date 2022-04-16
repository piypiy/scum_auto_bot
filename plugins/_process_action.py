from datetime import datetime
from pathlib import Path
from random import *
import random
from lib.controllerFtpLogScum import Controller_Ftp_Log_Scum
import subprocess
import time
import sys
import os
import requests
import json


class Action:

    PRC_CHAT = None
    RES = None
    CON = None
    SCB = None
    PAG = None

    currentScope = None
    clean = False


    def __init__(self, RES, CON, SCB, PRC_CHAT, PAG):
        self.RES = RES
        self.CON = CON
        self.SCB = SCB
        self.PAG = PAG
        self.PRC_CHAT = PRC_CHAT


    def getPlayerList(self):
        playerList = {}
        pList = self.PRC_CHAT.send("#ListPlayers", read=True)
        pList = pList.split('\n')
        pList.pop(0)
        for el in pList:
            elProps = el.split('    ')
            pProps = []
            for prop in elProps:
                prop.strip()
                if(len(prop) >= 1):
                    pProps.append(prop)
            uid = pProps[0][3:].strip()
            playerList[uid] = {
                'steamID': uid,
                'steamName': pProps[1].strip(),
                'charName': pProps[2].strip(),
                'fame': pProps[3].strip()
            }
        return playerList


    def mapShot(self, props):
        now = datetime.now()
        folderName = now.strftime('%Y_%m_%d')
        fileName = now.strftime('%Y_%m_%d.%H_%M_%S')+'.png'
        fullPath = props['path']+folderName+'/'+fileName
        Path(props['path']+folderName).mkdir(parents=True, exist_ok=True)
        self.PAG.press('esc')
        self.PAG.screenshot(fullPath, region=self.CON.getRegion('map'))
        time.sleep(0.05)
        self.PAG.press('t')
        self.CON.openAll()
        self.RES.add({'fileName': fileName, 'fullPath': fullPath})


    def playerReport(self, props):
        withLocation = False
        if("dict" in type(props).__name__ and props['location']):
            withLocation = True
        playerList = self.getPlayerList()

        if(withLocation):
            for player in playerList:
                p = self.PRC_CHAT.send('#Location '+playerList[player]['steamID'], read=True)
                playerLoc = (p[(p.find(':')+1):]).strip().split()
                playerList[player]['location'] = {
                    'x': playerLoc[0][2:],
                    'y': playerLoc[1][2:],
                    'z': playerLoc[2][2:]
                }

        self.RES.add({'playerInfo': playerList})


    def transfer(self, props):
        try:
            self.PRC_CHAT.goScope('global')
            self.PRC_CHAT.send(props['messages']['started'])
            playerList = self.getPlayerList()

            recipient = False
            sender = playerList[props['from']]

            for el in playerList:
                if(props['to'].lower() in playerList[el]['charName'].lower()):
                    recipient = playerList[el]
                    break


            if(not recipient):
                self.PRC_CHAT.send(props['messages']['notFound'])
                self.RES.add({'playerInfo': playerList})
                return False

            if(props['from'] == recipient['steamID']):
                self.PRC_CHAT.send(props['messages']['somethingWrong'])
                return False

            if(int(sender['fame']) < int(props['amount'])):
                self.PRC_CHAT.send(props['messages']['notEnough'])
                return False


            withdraw = '#SetFamePoints ' + str(int(sender['fame']) - int(props['amount'])) + ' ' + props['from']
            deposit = '#SetFamePoints ' + str(int(recipient['fame']) + int(props['amount'])) + ' ' + recipient['steamID']

            self.RES.add({
                "transactionInfo": {
                    "senderBefore": str(int(sender['fame'])),
                    "recipientBefore": str(int(recipient['fame'])),
                    "withdraw": withdraw,
                    "deposit": deposit
                }
            })

            self.PRC_CHAT.send(withdraw)
            self.PRC_CHAT.send(deposit)
            self.PRC_CHAT.send(props['messages']['success'])

        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            self.PRC_CHAT.send(props['messages']['somethingWrong'])
            self.RES.addError(str(e), str(exception_type))
            self.RES.send()


    def travel(self, props):
        try:
            self.PRC_CHAT.goScope('global')
            self.PRC_CHAT.send(props['messages']['start'])
            playerList = self.getPlayerList()
            user = playerList[props['steamID']]
            self.RES.add({'userInfo': user})

            if(not user):
                self.PRC_CHAT.send(props['messages']['somethingWrong'])
                return False

            if(int(user['fame']) < int(props['costs'])):
                self.PRC_CHAT.send(props['messages']['notEnough'])
                return False

            p = self.PRC_CHAT.send('#Location '+props['steamID'], read=True)
            playerLoc = (p[(p.find(':')+1):]).strip().split()
            nearStation = False
            for station in props['stations']:
                if(float(playerLoc[0][2:]) > (station[0] - station[2]) and float(playerLoc[0][2:]) < (station[0] + station[2])):
                    if(float(playerLoc[1][2:]) > (station[1] - station[3]) and float(playerLoc[1][2:]) < (station[1] + station[3])):
                        nearStation = True

            if(nearStation):
                self.PRC_CHAT.send('#SetFamePoints ' + str(int(user['fame']) - int(props['costs'])) + ' ' + props['steamID'])
                self.PRC_CHAT.send(props['target'])
            else:
                self.PRC_CHAT.send(props['messages']['noStation'])
                return False
            return True

        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            self.PRC_CHAT.send(props['messages']['somethingWrong'])
            self.RES.addError(str(e), str(exception_type))
            self.RES.send()


    def spawn(self, command):
        i = 0
        resp = self.PRC_CHAT.send(command, read=True)
        while(not resp.lower().startswith('spawned') and i < 20):
            i = i + 1
            time.sleep(0.05)
            resp = self.PRC_CHAT.read()
        if(resp.lower().startswith('spawned')):
            return True
        return False


    def sale(self, props):
        try:
            self.PRC_CHAT.goScope('local')
            self.PRC_CHAT.send(props['messages']['startSale'])
            p = self.PRC_CHAT.send('#Location ' + props['userID'], read=True)
            playerLoc = (p[(p.find(': ')+1):]).strip().split()
            nearShop = False
            if(float(playerLoc[0][2:]) > (props['shop'][0] - props['shop'][2]) and float(playerLoc[0][2:]) < (props['shop'][0] + props['shop'][2])):
                if(float(playerLoc[1][2:]) > (props['shop'][1] - props['shop'][3]) and float(playerLoc[1][2:]) < (props['shop'][1] + props['shop'][3])):
                    nearShop = True

            if(not nearShop):
                self.PRC_CHAT.goScope('global')
                self.PRC_CHAT.send(props['messages']['notNearShop'])
                return

            playerList = self.getPlayerList()
            player = playerList[props['userID']]

            if(int(player['fame']) < int(props['item']['price_fame'])):
                self.PRC_CHAT.goScope('local')
                self.PRC_CHAT.send(props['messages']['notEnoughMoney'])
                return

            famePointSetter = '#SetFamePoints '+ str(int(player['fame']) - int(props['item']['price_fame'])) + ' ' + props['userID']
            itemSpawner = props['item']['spawn_command']

            self.PRC_CHAT.goScope('local')
            self.PRC_CHAT.send(props['teleport'])
            #self.PRC_CHAT.send(props['teleportUser'])
            self.PRC_CHAT.send(famePointSetter)
            self.PRC_CHAT.send(itemSpawner)
            self.PRC_CHAT.send(props['messages']['endSale'])

        except Exception as e:
            exception_type, exception_object, exception_traceback = sys.exc_info()
            self.PRC_CHAT.send(props['messages']['somethingWrong'])
            self.RES.addError(str(e), str(exception_type))
            self.RES.send()

    def getStarterPack(self,prop_user):
        self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Ta demande du Pack de bienvenue est prise en compte, merci de patienter quelques instants le temps que je prépare ta  commande. Prépare-toi à être transporté dans moins de 2 minutes.')
        self.PRC_CHAT.doClean()
        #self.PRC_CHAT.send(prop_user['messages']['starterPack'])
        self.PRC_CHAT.send(f"#teleport 574605.938 -229922.313 356.130")
        time.sleep(15)
        self.PRC_CHAT.send(f"#spawnitem BP_Weapon_BlackHawk_Crossbow 1")
        self.PRC_CHAT.send(f"#spawnItem Improvised_Quiver_01 1")
        self.PRC_CHAT.send(f"#spawnitem BP_Ammo_Crossbow_Bolt_Carbon 10")
        self.PRC_CHAT.send(f"#spawnitem BP_Ammo_Crossbow_Bolt_Carbon 10")
        self.PRC_CHAT.send(f"#spawnitem BP_Ammo_Crossbow_Bolt_Carbon 4")
        self.PRC_CHAT.send(f"#spawnitem 2H_Baseball_Bat_With_Spikes 1")
        self.PRC_CHAT.send(f"#spawnItem Hiking_Backpack_04 1")
        self.PRC_CHAT.send(f"#spawnitem Water_05l 1")
        self.PRC_CHAT.send(f"#spawnitem Lock_Item_Advanced 1")
        self.PRC_CHAT.send(f"#spawnitem BP_WeaponFlashlight_DesertEagle 1")
        self.PRC_CHAT.send(f"#spawnitem MRE_Cheeseburger 1")
        self.PRC_CHAT.send(f"#spawnvehicle BP_Quad_01_A 1")
        self.PRC_CHAT.send(f"#teleport 574605.938 -229922.313 356.130 \"{prop_user['userID']}\"")
        self.PRC_CHAT.teleportOrigin()

    def teleportToJump(self,prop_user, jump = 3):
        player_x,player_y,player_z = self.getLocationPlayer(prop_user['userID'])
        player_z = float(player_z)+float(jump * 120)
        self.PRC_CHAT.send(f"#teleport {player_x} {player_y} {player_z}  \"{prop_user['userID']}\"")

    def teleportToZone(self,prop_user):
        regions = {
            'D4': (571874.688, 351582.156, 611.17),
            'D3': (263938.75, 503086.563, 22195.16),
            'D2': (-118371.227, 347189.188, 74983.5),
            'D1': (-320756.188, 561343.5, 76789.891),
            'D0': (-876307.625, 500313.938, 61112.555),

            'C4': (577472.125, 254866.641, 2025.04),
            'C3': (156377.938, 39713.859, 29901.979),
            'C2': (-182912.359, 75683.18, 67510.242),
            'C1': (-499467.469, 191493.203, 37808.898),
            'C0': (-829674.938, 155191.781, 43017.75),

            'B4': (494012.938, -192795.219, 333.09),
            'B3': (291911.813, -180368.109, 14302.739),
            'B2': (-57383.367, -88131.977, 36523.188),
            'B1': (-461547.188, -104336.156, 30867.16),
            'B0': (-740222.125, -270054.563, 17075.182),

            'A4': (337797.344, -371151.156, 12877.5),
            'A3': (192390.063, -516058.281, 397.23),
            'A2': (-32816.77, -489083.063, 328.61),
            'A1': (-339919.125, -351018.031, 185.467),
            'A0': (-740222.125, -270054.563, 17075.182),

            'Z4': (535952.75, -698165.063, 256.193),
            'Z3': (101257.773, -757887.875, 1132.321),
            'Z2': (-159760.078, -688480.938, 727.619),
            'Z1': (-278276.5, -675996.125, 7803.06),
            'Z0': (-641969.75, -676555.813, 204.49),
        }

        zone = prop_user['command_chat'].replace('bug_teleport_to_zone','')
        region_select = regions[zone.upper()]
        x = region_select[0]
        y = region_select[1]
        z = region_select[2]

        self.PRC_CHAT.send(f"#teleport {x} {y} {z} \"{prop_user['userID']}\"")
        #self.PRC_CHAT.waitEndTeleport()

    def dropToStorage(self):



        #self.PRC_CHAT.send(f"#teleport 368734.844 -522173.656 7658.357")
        #time.sleep(3)

        list_drop = {
                0: {
                    'BP_Magazine_M82A1': (1,4),
                    '1H_KitchenKnife_03': (1,2),
                },
                1: {
                    'BPC_Weapon_AKM': (1,3),
                    'BP_M70_Bayonet': (1,2),
                    'BP_Magazine_RPK': (1,3),
                    'BP_ImprovisedFlashlight': (1,2),
                    'WeaponScope_ACOG_01': (1,2),
                    'Cal_7_62x39mm_Ammobox': (1,2),
                    'BP_ScopeRail_AK47': (1,2),
                    'BP_WeaponSuppressor_AK15': (1,2),
                    'BP_WeaponSights_RedDot_CA401B': (1,2),
                }

            }


        self.PRC_CHAT.send(f"#spawnitem Improvised_Wooden_Chest 1")
        self.PAG.press('esc')
        time.sleep(0.2)
        self.PAG.press('f')
        time.sleep(0.2)
        for i in range(10):
            self.PAG.scroll(10000)

        self.PAG.press('tab')
        self.PAG.keyDown('c')
        time.sleep(1)
        self.PAG.keyUp('c')
        time.sleep(1.5)

        pos_y = 20
        select_drop = 1
        for item in list_drop[select_drop]:
            nbr_move = 0
            item_name = item
            item_nbr = list_drop[select_drop][item][0]
            item_size = list_drop[select_drop][item][1]
            self.PAG.press('t')
            time.sleep(0.18)
            self.PRC_CHAT.send(f"#spawnitem {item_name} {item_nbr}")
            time.sleep(0.18)
            self.PAG.press('esc')
            self.PAG.moveTo(1920/2, 1080/2, duration=0.4)
            time.sleep(0.18)
            nbr = 0
            while nbr < item_nbr:
                try:
                    self.PAG.press('tab')
                    time.sleep(0.5)
                    self.PAG.press('tab')
                    print("mouseDown")
                    self.PAG.mouseDown(960,530, button='left')
                    time.sleep(1)
                    print("mouse moveTo")
                    self.PAG.moveTo(960,530-10, duration=0.4)
                    time.sleep(1)
                    while(not self.CON.onScreen('img/id.png', region='stock_drop_id')):
                        self.PAG.mouseUp(button='left')
                        time.sleep(0.2)
                        self.PAG.press('tab')
                        time.sleep(1)
                        self.PAG.press('tab')

                        self.PAG.mouseDown(960,530, button='left')
                        time.sleep(1)
                        self.PAG.moveTo(960,530-10, duration=0.4)
                        time.sleep(1)
                        nbr_move = nbr_move + 1
                        if(nbr_move == 5):
                            self.PAG.press('tab')
                            time.sleep(0.5)
                            self.PAG.press('tab')
                            self.PAG.keyDown('c')
                            time.sleep(0.8)
                            self.PAG.keyUp('c')
                            time.sleep(1)
                            self.PAG.press('t')
                            time.sleep(0.18)
                            self.PRC_CHAT.send(f"#spawnitem {item_name} {item_nbr}")
                            time.sleep(0.18)
                            self.PAG.press('esc')
                        if(nbr_move > 10):
                            break

                    #self.PAG.dragTo(15, pos_y, 0.5, button='left')
                    self.PAG.moveTo(15,pos_y, duration=0.4)
                    print("mouse mouseUp")
                    self.PAG.mouseUp(15, pos_y, button='left')
                    time.sleep(1)
                    pos_y += 33*item_size
                    nbr += 1


                except:
                    nbr_move = nbr_move + 1
                    pass

        self.PAG.press('esc')
        self.PAG.press('tab')
        self.PAG.press('t')


    def teleportToBankChest(self,prop_user):
        url = "https://rpfrance.inov-agency.com/banque_coffre.php?steam_id=" + prop_user['userID']
        r = requests.get(url)
        json_obj = json.loads(r.text)

        if(json_obj.__contains__('error')):
            print('error : ' + json_obj['error'])
        else:
            pos_teleport = json_obj['chest']['position']

            if(self.isUserNear(prop_user, 575454.688, -222331.672, 30)):
                self.PRC_CHAT.send(f"#teleport {pos_teleport} \"{prop_user['userID']}\"")
            else:
                print('user not near Bank')

    def teleportToBank(self,prop_user, bank_name_pos):
        try:
            pos_teleport = ''
            near = False

            if(bank_name_pos == 'entrance'):
                if(self.isUserNear(prop_user['userID'], 575454.688, -222331.672, 30) and self.IsCredentialAdmin(prop_user)):
                    near = True
                    pos_teleport = '575454.688 -222331.672 600.880'
            elif(bank_name_pos == 'exit'):
                if(self.isUserNear(prop_user['userID'], 575454.688, -222331.672, 400)):
                    near = True
                    pos_teleport = '573764.750 -227568.359 364.590'
            if(pos_teleport != '' and near == True):
                self.PRC_CHAT.send(f"#teleport {pos_teleport} \"{prop_user['userID']}\"")

            if(near == False):
                print('user not near Bank')

        except:
            pass

    def getLocationPlayer(self,steam_id):
        self.PRC_CHAT.send(f"#ListVehicles")
        time.sleep(0.2)
        p = self.PRC_CHAT.send('#Location '+steam_id, read=True)
        playerLoc = (p[(p.find(':')+1):]).strip().split()
        print(playerLoc, playerLoc[0][2:],playerLoc[1][2:])

        return playerLoc[0][2:],playerLoc[1][2:],playerLoc[2][2:]



    def isUserNear(self,steam_id,x,y,l,h = 0):
        #ajust h and l
        x = float(x)
        y = float(y)
        l = float(l) * 120
        if(h > 0):
            h = float(h) * 120
        else:
            h = l

        player_x,player_y,player_z = self.getLocationPlayer(steam_id)
        print(player_x,player_y,player_z)
        print('pos:',(x - l),(x + l),(y - h),(y + h))

        if(float(player_x) > (x - l) and float(player_x) < (x + l)):
            if(float(player_y) > (y - h) and float(player_y) < (y + h)):
                return True

        return False

    def getUserLocation(self,steam_id):
        p = self.PRC_CHAT.send('#Location '+steam_id, read=True)
        playerLoc = (p[(p.find(':')+1):]).strip().split()
        return playerLoc[0][2:], playerLoc[1][2:], playerLoc[2][2:]


    def IsCredentialAdmin(self, prop_user):
        if(prop_user['userID'] == '76561198029980673'
           or prop_user['userID'] == '76561198026254419'
           or prop_user['userID'] == '76561198800598751'
           ):
            return True
        else:
            return False



    async def checkIsPlayerNewbieLand(self):
        pos_teleport_newbieland = '559347.938 -445105.125 554.030'
        list_player = {}
        list_player_newbie_land = {}
        url = "https://rpfrance.inov-agency.com/newbie.php"
        r = requests.get(url)
        json_obj = json.loads(r.text)
        list_player_newbie = json_obj['list']
        if(list_player_newbie != None):
            if(len(list_player_newbie) > 0):
                for player in list_player_newbie:
                    list_player_newbie_land.update({player['steam_id']: player['name']})

            list_player = await Controller_Ftp_Log_Scum.checkLoginUser('left')
            if(list_player != None):
                for player_id in list_player:
                    if(list_player[player_id]['steam_id'] in list_player_newbie_land):
                        print(list_player[player_id])
                        user_steam_id = list_player[player_id]['steam_id']
                        if(self.isUserNear(user_steam_id, 543546, -444946, 200) == False):
                            self.PRC_CHAT.send(f"#teleport {pos_teleport_newbieland} \"{user_steam_id}\"")

    def savePosUser(self,steam_id):
        x, y, z = self.getUserLocation(steam_id)
        print("savePosUser",x,y,z,steam_id)
        posUser = {}
        posUser = {'steam_id': steam_id,
                   'name': 'X',
                   'position': x + " " + y + " " + z
                }
        requests.post(
            'https://rpfrance.inov-agency.com/position.php', data=posUser)

    def teleportToShop(self,prop_user):
        user_steam_id = prop_user['userID']
        self.savePosUser(user_steam_id)
        self.PRC_CHAT.send(f"#teleport 571430 -218820 426 \"{user_steam_id}\"")


    def teleportUserLastPos(self, prop_user):
        try:
            user_steam_id = prop_user['userID']
            url = "https://rpfrance.inov-agency.com/position.php?steam_id=" + user_steam_id
            r = requests.get(url)
            json_obj = json.loads(r.text)

            if(json_obj.__contains__('error')):
                print('No position for this user')
            else:
                position = json_obj['list'][0]['position']
                self.PRC_CHAT.send(f"#teleport {position} \"{user_steam_id}\"")
        except Exception as e:
            print("returnPositionUser", e)

    def teleportUserToEvent(self, prop_user, save_last_post = True):
        try:
            user_steam_id = prop_user['userID']
            url = "https://rpfrance.inov-agency.com/portal.php?event=true"
            r = requests.get(url)
            json_obj = json.loads(r.text)

            if(json_obj.__contains__('error')):
                print('No position for this user')
            else:
                if(save_last_post == True):
                    self.savePosUser(user_steam_id)

                x = json_obj['list'][0]['in']['x']
                y = json_obj['list'][0]['in']['y']
                z = json_obj['list'][0]['in']['z']
                self.PRC_CHAT.send(f"#teleport {x} {y} {z} \"{user_steam_id}\"")
        except Exception as e:
            print("returnPositionUser", e)

    def teleportPortal(self,type_portal = 'in', prop_user = None):
        if(type_portal == 'in'):
            type_portal_destination = 'out'
        else:
            type_portal_destination = 'in'

        url = "https://rpfrance.inov-agency.com/portal.php"
        r = requests.get(url)
        json_obj = json.loads(r.text)

        player_x,player_y,player_z = self.getLocationPlayer(prop_user['userID'])

        print('Player Location: ',player_x,player_y,player_z)


        try:
            for portal in json_obj['list']:
                have_credential = True
                if(portal['restricted'] == True and prop_user['userID'] not in portal['steam_id']):
                    have_credential = False

                x = float(portal[type_portal]['x'])
                y = float(portal[type_portal]['y'])
                z = float(portal[type_portal]['z'])
                delta_x = float(portal[type_portal]['delta_x']) * 120
                delta_y = float(portal[type_portal]['delta_y']) * 120
                delta_z = float(portal[type_portal]['delta_z']) * 120

                print(x,y,z,delta_x,delta_y,delta_z)

                if(float(player_x) > (x - delta_x) and float(player_x) < (x + delta_x)):
                    if(float(player_y) > (y - delta_y) and float(player_y) < (y + delta_y)):
                        if(float(player_z) > (z - delta_z) and float(player_z) < (z + delta_z)):
                            if(have_credential):
                                print("Teleport to "+portal['name'])
                                self.PRC_CHAT.send(f"#teleport {portal[type_portal_destination]['x']} {portal[type_portal_destination]['y']} {portal[type_portal_destination]['z']} \"{prop_user['userID']}\"")
                            else:
                                print('No credential for this portal')
                                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Tu n\'as pas les autorisations nécessaires pour utiliser ce portail')
                            break

        except Exception as e:
            print("[Error] teleportPortal : "+str(e))
            print(portal)

    def randomZ(self,nbr_z):
        list_z = {
            'BP_Zombie_Civilian_Fat_Female',
            'BP_Zombie_Civilian_Fat_Male',
            'BP_Zombie_Civilian_Muscular_Female',
            'BP_Zombie_Civilian_Muscular_Male',
            'BP_Zombie_Civilian_Normal_Male',
            'BP_Zombie_Civilian_Skinny_Female',
            'BP_Zombie_Civilian_Skinny_Male',
            'BP_Zombie_Hospital_Fat',
            'BP_Zombie_Hospital_Normal',
            'BP_Zombie_Hospital_Muscle',
            'BP_Zombie_Hospital_Female',
            'BP_Zombie_Military_Armored',
            'BP_Zombie_Military_Female',
            'BP_Zombie_Military_Muscle',
            'BP_Zombie_Police_Armored',
            'BP_Zombie_Police_Fat',
            'BP_Zombie_Police_Muscle',
            'BP_Zombie_Police_Female'
        }
        for i in range(nbr_z):
            selected_z = random.choice(list(list_z))
            self.PRC_CHAT.send(f"#spawnzombie {selected_z} 1")

    def buyAirCraftMarket(self,prop_user, type_banque = 'market'):
        #self.sendAlertDiscord(prop_user['player_info']['discord_id'],'La commande pour le véhicule est en cours de traitement. Merci de patienter.')
        if(self.isUserNear(prop_user['userID'], 378237, -513476, 40)):
            if(prop_user['code_banque'] != ''):
                self.PRC_CHAT.doClean()
                self.PAG.click(110,500)
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Votre commande est en cours de préparation. Merci de patienter.')
                self.PRC_CHAT.send(f"#teleport 378237.625 -513476.281 7590.670")
                time.sleep(10)
                aircraft = prop_user['command_chat'].replace('buy_aircraft_market_player_','').replace('buy_aircraft_market_','')
                self.PRC_CHAT.send(f"#SpawnVehicle {aircraft} 1")
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'La commande pour l\'avions est prête')

                try:
                    url = "https://rpfrance.inov-agency.com/banque.php"
                    if(type_banque == 'market'):
                        user_command = prop_user['code_shop_banque']+" "+str(int(0-prop_user['value_item']))
                    else:
                        user_command = prop_user['code_banque']+" "+str(int(0-prop_user['value_item']))

                    r = requests.post(url, data={
                        'user_id': 'CyberWise3552',
                        'from': 'scum_tool',
                        'command_chat': user_command
                        })
                    self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Votre commande est prête.')
                except Exception as e:
                    print("[Error] buyCarMarket : "+str(e))
                    pass

                self.PRC_CHAT.teleportOrigin()
                time.sleep(60)
            else:
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Vous n\'avez aucun compte enregistré à la banque! Merci de vous rapprocher du personnel de la banque.')
        else:
            self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Rapprochez-vous du magasin d\'avions en A4 pour pouvoir acheter un avions')


    def buyBoatMarket(self,prop_user, type_banque = 'market'):
        if(self.isUserNear(prop_user['userID'], 570608, -229554, 20)):
            if(prop_user['code_banque'] != ''):
                self.PRC_CHAT.doClean()
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Votre commande est en cours de préparation. Merci de patienter.')
                self.PRC_CHAT.send(f"#teleport 567687.563 -227440.031 7.590")
                time.sleep(10)
                boat = prop_user['command_chat'].replace('buy_boat_market_player_','').replace('buy_boat_market_','')
                self.PRC_CHAT.send(f"#SpawnVehicle {boat} 1")
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'La commande pour l\'achat de votre bateau est prête. Rapprochez-vous du hangar à bateaux pour récupérer votre nouveau joujou.')

                try:
                    url = "https://rpfrance.inov-agency.com/banque.php"
                    if(type_banque == 'market'):
                        user_command = prop_user['code_shop_banque']+" "+str(int(0-prop_user['value_item']))
                    else:
                        user_command = prop_user['code_banque']+" "+str(int(0-prop_user['value_item']))

                    r = requests.post(url, data={
                        'user_id': 'CyberWise3552',
                        'from': 'scum_tool',
                        'command_chat': user_command
                        })
                    self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Votre commande est prête.')
                except Exception as e:
                    print("[Error] buyBoatMarket : "+str(e))
                    pass

                self.PRC_CHAT.teleportOrigin()
                time.sleep(10)
            else:
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Vous n\'avez aucun compte enregistré à la banque! Merci de vous rapprocher du personnel de la banque.')
        else:
            self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Rapprochez-vous du magasin de bateaux en B4 pour pouvoir acheter un bateau.')


    def buyCarMarket(self,prop_user):
        #self.sendAlertDiscord(prop_user['player_info']['discord_id'],'La commande pour le véhicule est en cours de traitement. Merci de patienter.')
        if(prop_user['code_shop_banque'] != ''):
            self.PRC_CHAT.doClean()
            self.PRC_CHAT.send(f"#teleport 572245.625 -224606.516 362.250")
            time.sleep(10)
            car = prop_user['command_chat'].replace('buy_car_market_','')
            self.PRC_CHAT.send(f"#SpawnVehicle {car} 1")
            self.sendAlertDiscord(prop_user['player_info']['discord_id'],'La commande pour le véhicule est prête')

            try:
                url = "https://rpfrance.inov-agency.com/banque.php"
                user_command = prop_user['code_shop_banque']+" "+str(int(0-prop_user['value_item']))
                print(url)
                print(user_command)
                r = requests.post(url, data={
                    'user_id': 'CyberWise3552',
                    'from': 'scum_tool',
                    'command_chat': user_command
                    })
            except Exception as e:
                print("[Error] buyCarMarket : "+str(e))
                pass
            self.PRC_CHAT.teleportOrigin()
            time.sleep(10)
        else:
            self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Vous n\'etes pas autorisé à utiliser cette commande !')


    def spawCash(self, money, use = False):
        nb_ticket = money // 5000
        modulo = nb_ticket // 10
        reste = nb_ticket - (modulo * 10)

        if(use):
            use = [45,50,55,60,65]
            use_random = random.choice(use)
            heal = f'Health {use_random}'
        else:
            heal = ''

        if(modulo > 0):
            for i in range(modulo):
                self.PRC_CHAT.send(f"#spawnitem BP_Cash 10 {heal}")
        if(reste > 0):
            self.PRC_CHAT.send(f"#spawnitem BP_Cash {reste} {heal}")

    def banqueWithDrawal(self,prop_user):
        if(prop_user['code_banque'] != ''):
            if(self.isUserNear(prop_user['userID'], 566881, -224684, 2)):
                self.PRC_CHAT.doClean()
                self.PRC_CHAT.send(f"#teleport 566755.125 -224770.859 381.237")
                time.sleep(10)
                self.spawCash(prop_user['value_item'],False)
                time.sleep(1)
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Merci de votre confiance à notre banque!')
                try:
                    url = "https://rpfrance.inov-agency.com/banque.php"
                    #'''
                    if(prop_user['code_banque'] != ''):
                        user_command = prop_user['code_banque']+" "+str(int(0-prop_user['value_item']))
                    else:
                        user_command = prop_user['code_shop_banque']+" "+str(int(0-prop_user['value_item']))
                    r = requests.post(url, data={
                        'user_id': 'CyberWise3552',
                        'from': 'scum_tool',
                        'command_chat': user_command
                        })
                    #'''
                except Exception as e:
                    print("[Error] buyCarMarket : "+str(e))
                    pass
                self.PRC_CHAT.teleportOrigin()
                time.sleep(10)
            else:
                print('User not near ATM')
                self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Rapprochez-vous du distributeur de billet en B4 (chez l\'épicier) pour faire un retrait')
        else:
            self.sendAlertDiscord(prop_user['player_info']['discord_id'],'Vous n\'avez aucun compte enregistré à la banque! Merci de vous rapprocher du personnel de la banque.')


    def spawnZombieHorde(self,file_name_event_last):
        f = open(file_name_event_last, "a+")
        f.write("Last Event!")
        f.close()

        list_item = [

        ]
        list_spawn = [
            {
                'name': 'spawn_1',
                'description': '\u200b',
                'localisation': 'A3',
                'nbr_item': 4,
                'item_spawn': {"x": 257997.594, "y": -504805.344, "z": 7627.810},
                'item': [
                        'Christmas_Present_AK15 1',
                        'Christmas_Present_AKS_74U_01 1',
                        'Christmas_Present_Ghillie 1',
                        'Christmas_Present_SVD_01 1',
                ],
                'spawn_z': [
                        {"loc": "X=259075 Y=-506074 Z=7591", "nbr": randint(5, 8)},
                        {"loc": "X=257363 Y=-504037 Z=7658", "nbr": randint(5, 8)},
                        {"loc": "X=260285.719 Y=-503926.563 Z=7643.470", "nbr": randint(5, 8)},
                        {"loc": "X=255249.922 Y=-506104.781 Z=7302.580", "nbr": randint(5, 8)},
                        {"loc": "X=253889.672 Y=-504305.656 Z=7658.610", "nbr": randint(5, 8)},
                        {"loc": "X=262590.813 Y=-506906.750 Z=7210.620", "nbr": randint(5, 8)},
                        {"loc": "X=259557.813 Y=-498977.469 Z=8408.080", "nbr": randint(2, 5)},
                        {"loc": "X=266424.813 Y=-504394.781 Z=7909.850", "nbr": randint(2, 5)},
                ],
            },
            {
                'name': 'spawn_2',
                'description': 'N\'y allez pas seul...',
                'localisation': 'A2-Bunker',
                'nbr_item': 4,
                'item_spawn': {"x": 257997.594, "y": -504805.344, "z": 7627.810},
                'item': [
                        'Christmas_Present_AK15 1',
                        'Christmas_Present_AKS_74U_01 1',
                        'Christmas_Present_Ghillie 1',
                        'Christmas_Present_SVD_01 1',
                ],
                'spawn_z': [
                        {"loc": "X=-41144.141 Y=-324788.031 Z=16218.939", "nbr": randint(5, 8)},
                        {"loc": "X=-42533.527 Y=-324728.156 Z=16010.470", "nbr": randint(5, 8)},
                        {"loc": "X=-50030.570 Y=-323652.719 Z=16281.140", "nbr": randint(5, 8)},
                        {"loc": "X=-45426.168 Y=-321055.125 Z=16001.260", "nbr": randint(5, 8)},
                        {"loc": "X=-46367.520 Y=-322164.219 Z=16011.890", "nbr": randint(2, 5)},
                        {"loc": "X=-46972.867 Y=-318982.313 Z=16025.890", "nbr": randint(2, 5)},
                        {"loc": "X=-46675.789 Y=-321875.500 Z=16452.980", "nbr": randint(5, 8)},
                        {"loc": "X=-43302.879 Y=-322860.906 Z=16046.699", "nbr": randint(5, 8)},
                        {"loc": "X=-45556.578 Y=-323688.750 Z=16010.630", "nbr": randint(5, 8)},
                        {"loc": "X=-45834.438 Y=-323281.438 Z=16075.989", "nbr": randint(2, 5)},
                        {"loc": "X=-44753.711 Y=-320514.219 Z=16498.139", "nbr": randint(2, 5)},
                        {"loc": "X=-49713.199 Y=-320892.094 Z=16458.129", "nbr": randint(2, 5)},
                ],
            },
        ]
        #'''
        point_spawn = list_spawn[0]
        time.sleep(1)
        self.PRC_CHAT.send("#Teleport {x} {y} {z}".format(x=point_spawn['item_spawn']['x'], y=point_spawn['item_spawn']['y'], z=point_spawn['item_spawn']['z']))
        time.sleep(60)
        for item in point_spawn['item']:
            self.PRC_CHAT.send("#SpawnItem {item}".format(item=item))

        for point_spawn_z in point_spawn['spawn_z']:
            self.PRC_CHAT.send("#Teleport {loc}".format(loc=point_spawn_z['loc'].replace('X=', '').replace(' Y=', ' ').replace(' Z=', ' ')))
            time.sleep(10)
            self.randomZ(point_spawn_z['nbr'])


        loginDict = {
                        'command': json.dumps({
                            'messages':
                                [{
                                    'channel': 956629028830331010,
                                    'embed': {
                                            'fields':
                                                [
                                                    {'name': 'Event:', 'value': 'Hordes', 'inline': True},
                                                    {'name': 'Localisation:', 'value': point_spawn['localisation'], 'inline': True},
                                                    {'name': '\u200b', 'value': '\u200b', 'inline': True},
                                                    {'name': 'Description', 'value': point_spawn['description'], 'inline': False},
                                                ]
                                        },
                                    'image': {'image_folder': "pictures/spawn_horde", 'image_name': f"{point_spawn['name']}.png"},
                                }]
                        }),
                    }
        r = requests.post('https://rpfrance.inov-agency.com/messenger.php?bot_type=Bot_Discord_Event', data=loginDict)
        self.PRC_CHAT.teleportOrigin()
        time.sleep(60)

    def sendAlertDiscord(self,discord_id,message):

        MessageDict = {
                        'message': json.dumps(
                            [{
                                'message': message,
                                'message_admin': '',
                                'list_alert': [discord_id],
                            }]),
                    }
        r = requests.post('https://rpfrance.inov-agency.com/messenger.php', data=MessageDict)