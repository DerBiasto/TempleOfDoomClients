import requests
import time
import random

IP = "10.255.22.215"

s = requests.session()

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
    
def exampleGame(players):
    return __post(f"example_game/{players}")
    
def healthCheck():
    return __get(f"health_check")

def gameState(starting = 0):
    return __get(f"game/get/state?starting={starting}")

def getPlayers():
    return __get(f"game/get/players")

def getRole():
    return __get(f"game/my/role")

def getCards():
    return __get(f"game/my/cards")

def announce(role, treasures, traps):
    return __post(f"game/move/announce?role={role}&treasures={treasures}&traps={traps}")
    
def choosePlayer(player):
    return __post(f"game/move/choose/{player}")

def lobbyState():
    return __get(f"lobby/state")

def leaveLobby():
    return __post(f"lobby/leave")

def createLobby(capacity):
    return __post(f"lobby/new/{capacity}")

def joinLobby(name):
    return __post(f"lobby/join/{name}")
    
def getLobbies():
    return __get(f"lobby/get")

def gameOver(state):
    if state.treasureCount == goldAmount[state.playerCount]:
        return "You (Adventurers) have won"
    if state.playerCount == 10 and state.trapCount == 3:
        return "You (Guardians) have won"
    elif state.playerCount < 10 and state.trapCount == 2:
        return "You (Guardians) have won"
    if state.moveCount == 8 * state.playerCount:
        return "You (Guardians) have won"

def updateState(state, name):
    moves = gameState(state.moveCount)
    for move in moves:
        state.update(move, name)
    time.sleep(1)
    
def getInfo(state):
    print(f"Last {state.playerCount} moves: {gameState(max(state.moveCount-state.playerCount, 0))}")
    print(f"Players: {state.players}")
    print(f"Treasures uncover: {state.treasureCount}")
    print(f"Traps uncover: {state.trapCount}")
    print(f"Own Cards: {getCards()}")

class State:
    def __init__(self):
        self.players = getPlayers()
        self.activePlayer = self.players[0]
        self.moveCount = 0
        self.treasureCount = 0
        self.trapCount = 0
        self.playerCount = len(self.players)
        self.announcements = {}
        self.playerCardCount = {}
        self.round = 0
        
    def update(self, move, name):
        self.moveCount += 1
        if "Announcement" in move:
            self.announcements[self.activePlayer] = move["Announcement"]
        if "Choice" in move and move["Choice"][1] == "Treasure":
            self.treasureCount += 1
        if "Choice" in move and move["Choice"][1] == "Trap":
            self.trapCount += 1
        if "Announcement" in move and self.activePlayer == name:
            self.round += 1
            for player in self.players:
                state.playerCardCount[player] = 6 - self.round
        for player in self.players:
            if "Choice" in move and move["Choice"][0] == player:
                state.playerCardCount[player] -= 1
        if list(move.keys()) == ["Choice"]:
            self.activePlayer = move["Choice"][0]
        else:
            self.activePlayer = self.players[(self.players.index(self.activePlayer)+1)%len(self.players)]
    
print("1 to create Lobby, 2 to join Lobby, 3 to start an example game")
x = input()

if(x=='1'):
    print("How many players?")
    n = input()
    print(createLobby(n))
if(x=='2'):
    for lobby in getLobbies():
        print(lobby)
    print("Lobby name:")
    name = input()
    print(joinLobby(name))
if(x=='3'):
    print("Wie viele Spieler?")
    sp = input()
    print(exampleGame(sp))
    
name = s.cookies["user"]
lobby = s.cookies["game"]

print("Lobby name: " + lobby)
print("Username: " +name)

ls = lobbyState()
while getPlayers() == 'Not Found':
    if lobbyState() != ls:
        print(lobbyState())
        ls = lobbyState()
goldAmount = [0 ,0 ,0 ,5, 6, 7, 8, 7, 8, 9, 10]

state = State()

trustList = []
for i in range(state.playerCount):
    trustList.append(True)

mc = state.moveCount
print(getRole())

print(getCards())

while True:
    updateState(state, name)
    if gameOver(state) != None:
        print(gameOver(state))
        break
    if state.moveCount == mc + 1:
        print(f"Last move: {gameState()[-1]}")
        mc += 1
    if state.moveCount%(2*state.playerCount) < state.playerCount and name == state.activePlayer:
        getInfo(state)
        print("It is your turn, what do you want to announce?")
        if random.random() < 0.5:
            ro = "Adventurer"
        else:
            ro = "Guardian"
        tre = int((goldAmount[state.playerCount] - state.treasureCount + 1) * random.random())
        if state.playerCount == 10:
            tra = int((4 - state.trapCount) * random.random())
        else:
            tra = int((3 - state.trapCount) * random.random())
        print(announce(ro, tre, tra))
    elif state.moveCount%(2*state.playerCount) >= state.playerCount and name == state.activePlayer:
        getInfo(state)
        print("It is your turn, from whom do you want to uncover a card?")
        ranPlayer = state.players[int((state.playerCount) * random.random())]
        if ranPlayer == name:
            ranPlayer = state.players[(state.players.index(ranPlayer)+1)%len(state.players)]
        choosePlayer(ranPlayer)