import requests
import time

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

IP = "10.255.22.215"

s = requests.Session()

turn = 0
foundTreasure = 0
foundTraps = 0
players = {}
playersT = []
newTurns = None
playerTotal = 0
name = "j"
cTurn = 0
role = "h"
announceAmmount = 0
chooseAmmount = 0
lastPlayer = "g"
gameEnded = False

def reset():
    global turn
    global foundTreasure
    global foundTraps
    global players
    global playersT
    global newTurns
    global playerTotal
    global name
    global cTurn
    global role
    global announceAmmount
    global chooseAmmount
    global lastPlayer
    global gameEnded
    turn = 0
    foundTreasure = 0
    foundTraps = 0
    players = {}
    playersT = []
    newTurns = None
    playerTotal = 0
    name = "j"
    cTurn = 0
    role = "h"
    announceAmmount = 0
    chooseAmmount = 0
    lastPlayer = "g"
    gameEnded = False

cardTotals = {
3:[5,2],
4:[6,2],
5:[7,2],
6:[8,2],
7:[7,2],
8:[8,2],
9:[9,2],
10:[10,3]}

def __get(path):
    r = s.get(f"http://{IP}/" + path)
    if not r.text:
        return r.reason
    return r.json()

def __post(path):
    r = s.post(f"http://{IP}/" + path)
    if not r.text:
        return r.reason
    return r.json()

########## game commands ##########

def getPlayers():
    global players
    global playerTotal
    global playersT
    global lastPlayer
    playersT = __get("game/get/players")
    playerTotal = len(playersT)
    for t in range(playerTotal):
        players[playersT[t]] = ["",0,0]
    lastPlayer = playersT[0]
    return playersT

def getName():
    global name
    name = s.cookies.get("user")

def getState():
    global turn
    global foundTreasure
    global foundTraps
    global players
    global newTurns
    global cTurn
    global announceAmmount
    global chooseAmmount
    global lastPlayer
    global gameEnded
    newTurns =__get(f"game/get/state?starting={turn}")
    elapsedTurns = len(newTurns)
    turn+=elapsedTurns
    for i in range(elapsedTurns):
        if "Announcement" in newTurns[i]:
            players[playersT[cTurn]] = [newTurns[i]["Announcement"][0],newTurns[i]["Announcement"][1],newTurns[i]["Announcement"][2]]
            print(f"{playersT[cTurn]} announced as {bcolors.OKBLUE}{players[playersT[cTurn]][0]}{bcolors.ENDC} with {bcolors.OKBLUE}{players[playersT[cTurn]][1]} Treasures{bcolors.ENDC} and {bcolors.OKBLUE}{players[playersT[cTurn]][2]} Traps{bcolors.ENDC}")
            announceAmmount+=1
            chooseAmmount = 0
            cTurn = cTurn+1 if cTurn < playerTotal-1 else 0
        elif "Choice" in newTurns[i]:
            foundTreasure+=1 if newTurns[i]["Choice"][1] == "Treasure" else 0
            foundTraps+=1 if newTurns[i]["Choice"][1] == "Trap" else 0
            print(f"{lastPlayer} selected {bcolors.OKGREEN}{newTurns[i]["Choice"][0]}{bcolors.ENDC} and found {bcolors.OKGREEN}{newTurns[i]["Choice"][1]}{bcolors.ENDC}")
            chooseAmmount+=1
            announceAmmount = 0
            cTurn = 0
            while playersT[cTurn] != newTurns[i]["Choice"][0]:
                cTurn+=1
            lastPlayer = newTurns[i]["Choice"][0]
    if foundTreasure == cardTotals[playerTotal][0]:
        if role == "Guardian": print(f"{bcolors.FAIL}Adventurers won!{bcolors.ENDC}")
        else: print(f"{bcolors.WARNING}Adventurers won!{bcolors.ENDC}")
        gameEnded = True
    elif foundTraps == cardTotals[playerTotal][1] or turn == (playerTotal*8):
        if role == "Adventurer": print(f"{bcolors.FAIL}Guardians won!{bcolors.ENDC}")
        else: print(f"{bcolors.WARNING}Guardians won!{bcolors.ENDC}")
        gameEnded = True
    elif len(newTurns) > 0: print(f"\nIt's {playersT[cTurn]}'s move. Wait for them to finish")

def getCards():
    return __get("game/my/cards")

def getRole():
    return __get("game/my/role")

def announce(role, treasures: int, traps: int):
    return __post(f"game/move/announce?role={role}&treasures={treasures}&traps={traps}")

def choosePlayer(player):
    return __post(f"game/move/choose/{player}")

########## lobby commands ##########

def getLobbies():
    return __get("lobby/get")

def joinLobby(name):
    __post(f"lobby/join/{name}")
    joinLoop()

def leaveLobby():
    reset()
    __post("lobby/leave")

def createLobby(capacity):
    __post(f"lobby/new/{capacity}")
    print(f"Lobby name: {s.cookies.get("game")}")
    joinLoop()

def lobbyState():
    return __get("lobby/state")

########## loop commands ##########

def loopAnnounce():
    cards = getCards()
    treasures = 0
    traps = 0
    for t in range(len(cards)):
        if cards[t] == "Treasure": treasures+=1
        elif cards[t] == "Trap": traps+=1
    print(f"{bcolors.HEADER}It's your turn to make an announcement{bcolors.ENDC}\nYou role is {bcolors.OKCYAN}'{role}'{bcolors.ENDC}\nYou have:\n{bcolors.OKCYAN}{treasures} treasures\n{traps} traps{bcolors.ENDC}")
    aRole = input("Which role would you like to announce ('Adventurer' or 'Guardian') ")
    aTreasures = int(input("How many treasures would you like to announce (Positive whole number) "))
    aTraps = int(input("How many traps would you like to announce (Positive whole number) "))
    announce(aRole,aTreasures,aTraps)

def loopChoice():
    print(f"{bcolors.HEADER}It's your turn to choose a player{bcolors.ENDC}\nCurrently found rooms:\n{bcolors.OKCYAN}{foundTreasure} treasures\n{foundTraps} traps{bcolors.ENDC}")
    choosePlayer(input("Type another player's name to select them "))

def mainLoop():
    global role
    print(f"\nPlayers: {getPlayers()}")
    getName()
    print(f"You are {bcolors.WARNING}{name}{bcolors.ENDC}\n")
    role = getRole()
    print(f"It's {playersT[cTurn]}'s move. Wait for them to finish")
    while not gameEnded:
        getState()
        if len(newTurns) > 0 and not gameEnded:
            if name == playersT[cTurn]:
                if "Announcement" in newTurns[-1] and announceAmmount != playerTotal or chooseAmmount == playerTotal and lastPlayer == name:
                    loopAnnounce()
                elif "Choice" in newTurns[-1] and chooseAmmount != playerTotal or announceAmmount == playerTotal and lastPlayer == name:
                    loopChoice()
        elif turn == 0 and name == playersT[0]:
            loopAnnounce()
        time.sleep(1)
    del s.cookies["game"]

def joinLoop():
    global gameEnded
    gameEnded = False
    coolVariable = {}
    while coolVariable != None:
        coolerVariable  = lobbyState()
        if coolerVariable != coolVariable and coolerVariable != None: print(f"Players: {coolerVariable["players"]} ({len(coolerVariable["players"])}/{coolerVariable["capacity"]})")
        coolVariable = coolerVariable
        time.sleep(1)
    mainLoop()

def createExampleGame(n: int = 5):
    __post(f"example_game/{n}")
    mainLoop()