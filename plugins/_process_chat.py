import win32clipboard
import win32con
import time


class Chat:

    RES = None
    CON = None
    SCB = None
    PAG = None


    safeCommands = [
        '#location',
        '#listplayers',
        '#listspawnedvehicles',
        '#findsquadmember',
        '#listsquads'
    ]

    currentScope = None
    clean = False

    def __init__(self, RES, CON, SCB, PAG):
        self.RES = RES
        self.CON = CON
        self.SCB = SCB
        self.PAG = PAG


    def goScope(self, scope = 'local', force = False):
        if(not force and self.currentScope == scope):
            return True
        scopeImg = 'chat_local.png'
        if(scope == 'global'):
            scopeImg = 'chat_global.png'
        self.RES.printer(scope)
        i = 0
        onMapi = self.CON.onScreen('img/mapi.png', region='mapi')
        while(not onMapi):
            self.PAG.press('m')
            time.sleep(0.2)
            onMapi = self.CON.onScreen('img/mapi.png', region='mapi')
            i = i + 1
            if(i > 10):
                return False


        if(scope == 'global'):
            while(not self.CON.onScreen('img/' + scopeImg, region='chatScope')):
                self.PAG.press('t')
                time.sleep(0.5)
                self.PAG.press('tab')
                time.sleep(0.5)
                i = i + 1
                if(i > 10):
                    raise Exception('Could not change scope')
                    return False
        elif(scope == 'local'):
            while(self.CON.onScreen('img/' + scopeImg, region='chatScope')):
                self.PAG.press('t')
                time.sleep(0.5)
                self.PAG.press('tab')
                time.sleep(0.5)
                i = i + 1
                if(i > 10):
                    raise Exception('Could not change scope')
                    return False
        self.currentScope = scope

        #self.PAG.press('m')


        return True


    def copyToClip(self, txt):
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(txt, win32con.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()


    def readFromClip(self):
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return data


    def doClean(self):
        self.CON.isItReady()
        self.PAG.hotkey('ctrl','a')
        self.PAG.press('backspace')
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()
        self.clean = True


    def read(self, message):
        command = message.split()[0].strip().lower()
        if(command in self.safeCommands):
            self.copyToClip(message + ' true')
            self.PAG.hotkey('ctrl','v')
            self.PAG.press('enter')
        else:
            self.copyToClip(message)
            chat = self.CON.onScreen('img/chat_mute.png', region='chatStumm')
            self.PAG.moveTo(chat[0], chat[1]-30, 0.2, self.PAG.easeOutQuad)
            self.PAG.hotkey('ctrl','v')
            self.PAG.press('enter')
            self.PAG.click(chat[0], chat[1]-30)
            self.PAG.hotkey('ctrl','a')
            self.PAG.hotkey('ctrl', 'c')
            self.PAG.press('esc')
            self.PAG.press('t')
        return self.readFromClip().strip()


    def formLocation(self, telep):
        loc = telep.lower().replace('#teleport ', '')
        loc = loc.split(' ')
        return str(round(float(loc[0]))) + ' ' + str(round(float(loc[1]))) + ' ' + str(round(float(loc[2])))


    def getLocation(self):
        i = 0
        loc = self.send('#Location 76561198029980673', read = True)
        while(not loc.startswith('CyberWise') and i < 10):
            loc = self.send('#Location 76561198029980673', read = True)
            i = i + 1
        if(not loc.startswith('CyberWise')):
            self.RES.addError('Unable to catch location', '_process_chat: getLocation()')
            self.RES.send()
            return False
        loc = loc.split(': X=')[1]
        loc = loc.split(' ')
        return str(round(float(loc[0]))) + ' ' + str(round(float(loc[1][2:]))) + ' ' + str(round(float(loc[2][2:])))


    def send(self, message, read = False):
        self.PAG.click(110,500)
        message = message.strip()
        data = True
        teleport = False
        current = False

        self.PAG.hotkey('ctrl','a')
        self.PAG.press('backspace')
        '''
        if(message.lower().startswith('#teleport ') and 'CyberWise' in message.lower()):
            current = self.getLocation()
            teleport = self.formLocation(message.lower().replace('CyberWise', '').strip())
            if(current == teleport):
                return data
        '''
        self.RES.printer('SENDING MSG -> ' + message)
        if(read):
            data = self.read(message)
        else:
            self.copyToClip(message)
            self.PAG.hotkey('ctrl','v')
            self.PAG.press('enter')
            '''
            if(teleport):
                while(current == self.getLocation()):
                    time.sleep(0.15)
            '''
        time.sleep(0.15)
        return data
        self.RES.printer('SENDING MSG DONE')


    def sendMulti(self, messages):
        for message in messages:
            self.goScope(str(message['scope']))
            self.send(str(message['content']))

    def preMsg(self, prop_user):
        for i, message_key in enumerate(prop_user['messages']):
            prop_user['messages'][message_key] = prop_user['messages'][message_key] \
            .replace("{user}", prop_user['userName'])

        return prop_user


    def waitEndTeleport(self):

        return True

        while(not self.CON.onScreen('img/menu_continue.png', region='menu')):
            self.PAG.press('esc')
            time.sleep(0.5)

        '''
        while(self.loadingTeleport()):
            print('On est en train de teleporter')
            time.sleep(0.5)
        '''

    def teleportOrigin(self):
        self.send(f"#teleport  572240 -224600 -3840")

    def viewInfoPlayer(self):
        self.send(f"#ShowNameplates true")
        self.send(f"#ShowOtherPlayerInfo true")

    def loadingTeleport(self):
        have_micro = self.CON.onScreen('img/have_micro.png', region='micro')
        #print(img_rgb_screenshot_quality)
        if(have_micro):
            return False
        else:
            return True
