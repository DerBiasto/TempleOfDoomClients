import requests
import time


# region LIBRARY

URL = "http://10.255.22.192"

session = requests.Session()
def _getEndpoint(endpoint: str):
    response = session.get(URL+"/"+endpoint)
    if not response.text:
        return response.reason
    return response.json()

def _postEndpoint(endpoint: str):
    response = session.post(URL+"/"+endpoint)
    if response.status_code > 299:
        print(response.reason) 
        return response.reason
    return response


def listLobbies():
    return _getEndpoint("lobby/get")

def createLobby(capacity: int):
    return _postEndpoint(f"lobby/new/{capacity}")

def joinLobby(lobbyName: str):
    return _postEndpoint(f"lobby/join/{lobbyName}")

def getLobbyState():
    #lobbies = json.loads(getEndpoint("lobby/state").text)
    lobbyState = _getEndpoint("lobby/state")
    #pprint.pprint(lobbyState)
    return lobbyState

def leaveLobby():
    return _postEndpoint("lobby/leave")

def startExampleGame(playerCount: int=5):
    return _postEndpoint(f"example_game/{playerCount}")

def getPlayers():
    return _getEndpoint("game/get/players")

def getState(startMove: int=0):
    return _getEndpoint(f"game/get/state?starting={startMove}")

def announce(role: str = "Adventurer", treasures: int = 0, traps: int = 0):
    return _postEndpoint(f"game/move/announce?role={role}&treasures={treasures}&traps={traps}")

def getMyCards():
    return _getEndpoint("game/my/cards")

def getMyRole():
    return _getEndpoint("game/my/role")

def choosePlayer(player: str):
    return _postEndpoint(f"game/move/choose/{player}")

def closeConnection():
    session.close()

def getUsername():
    return session.cookies.get("user")

def getLobbyName():
    return session.cookies.get("game")

def printLobbys(lobbies: dict):
    for roomname in lobbies.keys():
        print(bcolors.OKCYAN + roomname + bcolors.ENDC)
        print(lobbies[roomname])

state = 0

def setStateGetMyCards():
    global state
    state = 5

goldTable = [0, 0, 0, 5, 6, 7, 8, 7, 8, 9, 10]
trapTable = [0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 3]
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = "\033[1m"
    UNDERLINE = '\033[4m'

# endregion

def lobbyLoop():
    lobbyState = 0
    oldPlayerCount = 0
    while True:
        match lobbyState:
            case 0: # Refresh Lobby List
                lobbyDict = listLobbies()
                lobbyState = getLobbyState()
                printLobbys(lobbyDict)
                lobbyState = 1
            case 1: # let User choose
                print("Choose a Lobby, type \"test\" to start an example game or \"new\" to create new lobby. Press Enter to refresh lobby list:")
                userInput = input()
                match userInput:
                    case "":
                        lobbyState = 0
                    case "test":
                        lobbyState = 2
                    case "new":
                        lobbyState = 3
                    case _:
                        if userInput not in lobbyDict.keys():
                            print("Invalid Lobby Name! Try again.")
                        else:
                            if joinLobby(userInput).status_code < 300:
                                print("Successfully joined a lobby!")
                                lobbyState = 4
            case 2: # Start Example Game
                requestedPlayerCount = int(input("How many players do you want? (3-10) "))
                requestedPlayerCount = 3 if requestedPlayerCount < 3 else 10 if requestedPlayerCount > 10 else requestedPlayerCount
                print(f"Starting example game with {requestedPlayerCount} players...")
                startExampleGame(requestedPlayerCount)
                return newGameLoop()
            case 3: # Create new Lobby
                requestedPlayerCount = int(input("How many players do you want? (3-10) "))
                requestedPlayerCount = 3 if requestedPlayerCount < 3 else 10 if requestedPlayerCount > 10 else requestedPlayerCount
                print(f"Creating lobby with {requestedPlayerCount} players...")
                createLobby(requestedPlayerCount)
                print(f"Your lobby is called {getLobbyName()}.")
                lobbyState = 4
            case 4: # inside Lobby
                try:
                    gameLobbyState = getLobbyState()
                    if gameLobbyState is None:
                        if getMyCards() == "Unauthorized":
                            print("You lobby seems to have disappeared.")
                            lobbyState = 0
                        else:
                            print("The game has started!")
                            return newGameLoop()
                    else:
                        capacity = gameLobbyState["capacity"]
                        players = list(gameLobbyState["players"])
                        if oldPlayerCount != len(players):
                            print(f"{len(players)} out of {capacity} players. Press CTRL+C to leave")
                            oldPlayerCount = len(players)
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("Leaving lobby...")
                    leaveLobby()
                    del session.cookies["game"]
                    lobbyState = 0

class gameState:
    def __init__(self): 
        self.announcementCount = 0
        self.choiceCount = 0
        self.gameStateCount = 0
        self.treasureCount = 0
        self.trapCount = 0
        self.players = getPlayers()
        self.cards = getMyCards()
        self.role = getMyRole()
        self.keyPlayer = self.players[0]
        self.username = session.cookies.get("user")
        self.phase = 0
        self.playerCardCount = [5]*len(self.players)
    def update(self, move: dict):
        self.cards = getMyCards()
        if "Announcement" in move.keys():
            self.gameStateCount += 1
            self.announcementCount += 1
            oldKeyPlayer = self.keyPlayer
            if (self.players.index(self.keyPlayer) < len(self.players)-1):
                self.keyPlayer = self.players[self.players.index(self.keyPlayer)+1]
            else:
                self.keyPlayer = self.players[0]
            data = {"player": oldKeyPlayer, "type": "Announcement", "role": move["Announcement"][0], "gold": move["Announcement"][1], "traps": move["Announcement"][2]}
        elif "Choice" in move.keys():
            self.gameStateCount += 1
            self.choiceCount += 1
            oldKeyPlayer = self.keyPlayer
            self.keyPlayer = move["Choice"][0]
            match move["Choice"][1]:
                case "Treasure":
                    self.treasureCount += 1
                case "Trap":
                    self.trapCount += 1   
            data = {"player": oldKeyPlayer,"type": "Choice", "choosenOne": move["Choice"][0], "card": move["Choice"][1]}
            
        data["backToAnnounce"] = False
        if self.phase == 0 and self.announcementCount % len(self.players) == 0:
            self.phase = 1
        elif self.phase == 1 and self.choiceCount % len(self.players) == 0:
            self.phase = 0
            data["backToAnnounce"] = True
        data["gameOver"] = "no"
        if self.treasureCount >= goldTable[len(self.players)]:
            data["gameOver"] = "gold"
        elif self.trapCount >= trapTable[len(self.players)]:
            data["gameOver"] = "traps"
        elif self.gameStateCount >= (len(self.players)*8):
            data["gameOver"] = "time"
        return data

def printMyInfo(curGameState):
    print(f"Your name is {bcolors.OKGREEN}{curGameState.username}{bcolors.ENDC} and you are playing as {bcolors.OKGREEN}{curGameState.role}{bcolors.ENDC}. Your cards are:")
    print(f"{bcolors.OKBLUE}{curGameState.cards}{bcolors.ENDC}")
    print(f"{bcolors.OKGREEN}{curGameState.treasureCount}/{goldTable[len(curGameState.players)]} gold{bcolors.ENDC} and {bcolors.OKGREEN}{curGameState.trapCount}/{trapTable[len(curGameState.players)]} traps{bcolors.ENDC} have been revealed.")

def askForAnnouncement(curGameState):
    print("It's your turn to announce!")
    roleInput = input(f"What role do you claim to be? You are a {curGameState.role}. (A or G) ")
    role = "Guardian" if roleInput == "G" else "Adventurer"
    treasure = int(input(f"How much gold do you claim to have? (You have {curGameState.cards.count("Treasure")} gold) "))
    traps = int(input(f"How many traps do you claim to have? (You have {curGameState.cards.count("Trap")} traps) "))
    announce(role, treasure, traps)

def askForChoice(curGameState):
    print("It's your turn to choose a player!")
    playerInput = input("Which player do you choose? ")
    if playerInput not in curGameState.players or playerInput.removesuffix("\n") == curGameState.username:
        print("Invalid player name!")
        return False
    else:
        choosePlayer(playerInput)
        return True

def processStateUpdate(curGameState, data):
    if data["type"] == "Announcement":
        print(f"{bcolors.OKCYAN}{data["player"]}{bcolors.ENDC} says he plays as {bcolors.OKGREEN}{data["role"]}{bcolors.ENDC}, has {bcolors.OKGREEN}{data["gold"]} gold{bcolors.ENDC} and {bcolors.OKGREEN}{data["traps"]} traps{bcolors.ENDC}.")
    elif data["type"] == "Choice":
        print(f"{bcolors.OKCYAN}{data["player"]}{bcolors.ENDC} has chosen {bcolors.OKGREEN}{"you" if data["choosenOne"] == curGameState.username else data["choosenOne"]}{bcolors.ENDC} and revealed a {bcolors.OKGREEN}{data["card"]}{bcolors.ENDC}.")
    match data["gameOver"]:
        case "gold":
            print(f"All gold has been found. The {bcolors.OKGREEN}Adventurers{bcolors.ENDC} won!")
            input("Press Enter to go back to Lobby selection... ")
            return lobbyLoop()
        case "traps":
            print(f"All traps have been revealed. The {bcolors.OKGREEN}Guardians{bcolors.ENDC} won!")
            input("Press Enter to go back to Lobby selection... ")
            return lobbyLoop()
        case "time":
            print(f"You are out of time. The {bcolors.OKGREEN}Guardians{bcolors.ENDC} won!")
            input("Press Enter to go back to Lobby selection... ")
            return lobbyLoop()
    if curGameState.keyPlayer != curGameState.username:
        print(f"It's {curGameState.keyPlayer} turn to {'announce' if curGameState.phase == 0 else 'choose'}.")
    if data["backToAnnounce"]:
        printMyInfo(curGameState)

def newGameLoop():
    curGameState = gameState()
    print("The players in your game are: ")
    print(curGameState.players)
    printMyInfo(curGameState)
    if curGameState.keyPlayer != curGameState.username:
        print(f"It's {curGameState.keyPlayer} turn to {'announce' if curGameState.phase == 0 else 'choose'}.")
    while True:
        if curGameState.keyPlayer == curGameState.username:
            if curGameState.phase == 0:
                askForAnnouncement(curGameState)
                processStateUpdate(curGameState, curGameState.update(getState(curGameState.gameStateCount)[0]))
            else:
                if askForChoice(curGameState):
                    processStateUpdate(curGameState, curGameState.update(getState(curGameState.gameStateCount)[0]))
        else:
            moves = getState(curGameState.gameStateCount)
            if len(moves) != 0:
                for move in moves:
                    data = curGameState.update(move)
                    processStateUpdate(curGameState, data)
            time.sleep(0.5)
lobbyLoop()
