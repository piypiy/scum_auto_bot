import time
import requests

class Ready:

    RES = None
    FOC = None
    CON = None
    PRC_CHAT = None

    def __init__(self, respond, focus, control, PRC_CHAT):
        self.PRC_CHAT = PRC_CHAT
        self.RES = respond
        self.CON = control
        self.FOC = focus

    def getGameState(self):
        self.CON.setWindow(self.FOC.getWindowProps())
        chat = self.CON.onScreen('img/chat_mute.png', region='chatStumm')
        mapi = self.CON.onScreen('img/mapi.png', region='mapi')
        if(chat and mapi):
            return 'ready'
        else:
            return 'game'


    def getState(self):
        try:
            if(self.FOC.doIt()):
                return self.getGameState()
            if(self.FOC.check('steam')):
                if(self.FOC.check('scum.exe')):
                    self.FOC.doIt()
                    return self.getGameState()
                else:
                    return False
            else:
                self.RES.printer('Steam getState????'+str(self.getGameState()))
                return 'steam'
        except Exception as e:
            return False


    def doIt(self, repeat=True):
        self.FOC.doIt()
        time.sleep(0.1)
        state = self.getState()
        self.RES.printer('State: ' + str(state))
        if(state == 'ready'):
            self.PRC_CHAT.doClean()
            return True
        elif(state == 'game'):
            url = "https://rpfrance.inov-agency.com/check_bot.php?status=restart"
            r = requests.get(url)
            if(self.CON.getReady()):
                self.PRC_CHAT.doClean()
                return True
        elif(state == 'steam'):
            url = "https://rpfrance.inov-agency.com/check_bot.php?status=restart"
            r = requests.get(url)
            self.RES.printer('Steam RESTART')
            self.CON.restart()
            return False
        else:
            url = "https://rpfrance.inov-agency.com/check_bot.php?status=restart"
            r = requests.get(url)
            if(self.CON.startGame()):
                self.PRC_CHAT.doClean()
                return True
        return False
