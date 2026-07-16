import requests
import json
import pprint
import math
import time
URL = "http://10.255.22.215"

session = requests.Session()
def _getEndpoint(endpoint: str):
    response = session.get(URL+"/"+endpoint)
    if not response.text:
        return response.reason
    # print(response.status_code)
    # print(response.reason)
    # print(response.text)
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
        print(bcolors.BOLD + roomname + bcolors.ENDC)
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

class gameState:
    def __init__(self): 
        self.isFirstRound = True
        self.keyPlayer = ""
        self.announcementCount = 0
        self.choiceCount = 0
        self.gameStateCount = 0
        self.treasureCount = 0
        self.trapCount = 0
        self.oldPlayerCount = 0

def mainLoop():
    curGameState = gameState()
    global state
    while True:
        match state:
            case 0: # Refresh Lobby List
                lobbyDict = listLobbies()
                lobbyState = getLobbyState()
                printLobbys(lobbyDict)
                state = 1
            case 1: # let User choose
                print("Choose a Lobby, type \"test\" to start an example game or \"new\" to create new lobby. Press Enter to refresh lobby list:")
                userInput = input()
                match userInput:
                    case "":
                        state = 0
                    case "test":
                        state = 2
                    case "new":
                        state = 3
                    case _:
                        if userInput not in lobbyDict.keys():
                            print("Invalid Lobby Name! Try again.")
                        else:
                            if joinLobby(userInput).status_code < 300:
                                print("Successfully joined a lobby!")
                                state = 4
            case 2: # Start Example Game
                requestedPlayerCount = int(input("How many players do you want? (3-10) "))
                requestedPlayerCount = 3 if requestedPlayerCount < 3 else 10 if requestedPlayerCount > 10 else requestedPlayerCount
                print(f"Starting example game with {requestedPlayerCount} players...")
                startExampleGame(requestedPlayerCount)
                state = 5
            case 3: # Create new Lobby
                requestedPlayerCount = int(input("How many players do you want? (3-10) "))
                requestedPlayerCount = 3 if requestedPlayerCount < 3 else 10 if requestedPlayerCount > 10 else requestedPlayerCount
                print(f"Creating lobby with {requestedPlayerCount} players...")
                createLobby(requestedPlayerCount)
                print(f"Your lobby is called {getLobbyName()}.")
                state = 4
            case 4: # inside Lobby
                try:
                    lobbyState = getLobbyState()
                    if lobbyState is None:
                        if getMyCards() == "Unauthorized":
                            print("You lobby seems to have disappeared.")
                            state = 0
                        else:
                            print("The game has started!")
                            state = 5
                    else:
                        capacity = lobbyState["capacity"]
                        players = list(lobbyState["players"])
                        if curGameState.oldPlayerCount != len(players):
                            print(f"{len(players)} out of {capacity} players. Press CTRL+C to leave")
                            curGameState.oldPlayerCount = len(players)
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("Leaving lobby...")
                    leaveLobby()
                    del session.cookies["game"]
                    state = 0
            case 5: # get Cards
                cards = getMyCards()
                role = getMyRole()
                if cards == "Unauthorized":
                    "Game Over!"
                    state = 10
                    break
                username = getUsername()
                players = list(getPlayers())
                print(f"Your name is {bcolors.OKGREEN}{username}{bcolors.ENDC} and you are playing as {bcolors.OKGREEN}{role}{bcolors.ENDC}. Your cards are:")
                print(f"{bcolors.OKBLUE}{cards}{bcolors.ENDC}")
                print(f"{bcolors.OKGREEN}{curGameState.treasureCount}/{goldTable[len(players)]} gold{bcolors.ENDC} and {bcolors.OKGREEN}{curGameState.trapCount}/{trapTable[len(players)]} traps{bcolors.ENDC} have been revealed.")
                if curGameState.isFirstRound:
                    print("The players in your game are: ")
                    print(players)
                    curGameState.isFirstRound = False
                    curGameState.keyPlayer = players[0]
                state = 6
            case 6: # Announcement Stage
                if curGameState.announcementCount >= len(players):
                    print("All cards have been anounced!")
                    curGameState.announcementCount = 0
                    state = 8
                elif curGameState.keyPlayer == username:
                    print("It's your turn to announce!")
                    roleInput = input(f"What role do you claim to be? You are a {role}. (A or G) ")
                    role = "Guardian" if roleInput == "G" else "Adventurer"
                    treasure = int(input(f"How much gold do you claim to have? (You have {cards.count("Treasure")} gold) "))
                    traps = int(input(f"How many traps do you claim to have? (You have {cards.count("Trap")} traps) "))
                    announce(role, treasure, traps)
                    state = 7
                else:
                    print(f"It's {curGameState.keyPlayer} turn to announce.")
                    state = 7
            case 7: # Wait for announcement
                moveList = list(getState(curGameState.gameStateCount))
                for move in moveList:
                    if list(move.keys())[0] == "Announcement":
                        curGameState.gameStateCount += 1
                        curGameState.announcementCount += 1
                        print(f"{bcolors.OKCYAN}{curGameState.keyPlayer}{bcolors.ENDC} says he plays as {bcolors.OKGREEN}{move["Announcement"][0]}{bcolors.ENDC}, has {bcolors.OKGREEN}{move["Announcement"][1]} gold{bcolors.ENDC} and {bcolors.OKGREEN}{move["Announcement"][2]} traps{bcolors.ENDC}.")
                        if (players.index(curGameState.keyPlayer) < len(players)-1):
                            curGameState.keyPlayer = players[players.index(curGameState.keyPlayer)+1]
                        else:
                            curGameState.keyPlayer = players[0]
                        state = 6
                    else:
                        print("All cards have been announced!")
                        curGameState.announcementCount = 0
                        state = 8
                time.sleep(0.5)
            case 8: # Choosing Stage
                if curGameState.choiceCount >= len(players):
                    print("All choices have been made.")
                    curGameState.choiceCount = 0
                    state = 5
                elif curGameState.keyPlayer == username:
                    print("It's your turn to choose a player!")
                    playerInput = input("Which player do you choose? ")
                    if playerInput not in players or playerInput.removesuffix("\n") == username:
                        print("Invalid player name!")
                    else:
                        choosePlayer(playerInput)
                        state = 9
                else:
                    print(f"It's {curGameState.keyPlayer} turn to choose.")
                    state = 9

            case 9: # Wait for choice
                moveList = list(getState(curGameState.gameStateCount))
                for move in moveList:
                    if list(move.keys())[0] == "Choice":
                        curGameState.gameStateCount += 1
                        curGameState.choiceCount += 1
                        print(f"{bcolors.OKCYAN}{curGameState.keyPlayer}{bcolors.ENDC} has chosen {bcolors.OKGREEN}{"you" if move["Choice"][0] == username else move["Choice"][0]}{bcolors.ENDC} and revealed a {bcolors.OKGREEN}{move["Choice"][1]}{bcolors.ENDC}.")
                        curGameState.keyPlayer = move["Choice"][0]
                        match move["Choice"][1]:
                            case "Treasure":
                                curGameState.treasureCount += 1
                            case "Trap":
                                curGameState.trapCount += 1   
                        state = 8
                    else:
                        curGameState.choiceCount = 0
                        state = 5
                if curGameState.treasureCount >= goldTable[len(players)]:
                    print(f"All gold has been found. The {bcolors.OKGREEN}Adventurers{bcolors.ENDC} won!")
                    state = 10
                elif curGameState.trapCount >= trapTable[len(players)]:
                    print(f"All traps have been revealed. The {bcolors.OKGREEN}Guardians{bcolors.ENDC} won!")
                    state = 10
                elif curGameState.gameStateCount >= (len(players)*8)-1:
                    print(f"You are out of time. The {bcolors.OKGREEN}Guardians{bcolors.ENDC} won!")
                    state = 10
            case 10: # Game Ended
                curGameState.isFirstRound = True
                curGameState.keyPlayer = ""
                curGameState.announcementCount = 0
                curGameState.choiceCount = 0
                curGameState.gameStateCount = 0
                curGameState.treasureCount = 0
                curGameState.trapCount = 0
                state = 0
                input("Press Enter to go back to Lobby selection... ")
            case _:
                return
mainLoop()