import requests
import time

IP = "10.255.22.130"

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
        print("You are: "+getRole())
        return "Adventurers have won"
    if state.playerCount == 10 and state.trapCount == 3:
        print("You are: "+getRole())
        return "Guardians have won"
    elif state.playerCount < 10 and state.trapCount == 2:
        print("You are: "+getRole())
        return "Guardians have won"
    if state.moveCount >= state.playerCount * 8:
        print("You are: "+getRole())
        return "Guardians have won"

def updateState(state):
    moves = gameState(state.moveCount)
    for move in moves:
        state.update(move)
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
        
    def update(self, move):
        self.moveCount += 1
        if "Choice" in move and move["Choice"][1] == "Treasure":
            self.treasureCount += 1
        if "Choice" in move and move["Choice"][1] == "Trap":
            self.trapCount += 1
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
goldAmount = [5, 6, 7, 8, 7, 8, 9, 10]

state = State()
mc = state.moveCount
print(getRole())
print(getCards())

while True:
    updateState(state)
    if gameOver(state) != None:
        print(gameOver(state))
        break
    if state.moveCount == mc + 1:
        print(f"Last move: {gameState()[-1]}")
        mc += 1
    if state.moveCount%(2*state.playerCount) < state.playerCount and name == state.activePlayer:
        getInfo(state)
        print("It is your turn, what do you want to announce?")
        print("Role:")
        ro = input()
        print("Treasures:")
        tre = input()
        print("Traps:")
        tra = input()
        print(announce(ro, tre, tra))
    if state.moveCount%(2*state.playerCount) >= state.playerCount and name == state.activePlayer:
        getInfo(state)
        print("It is your turn, from whom do you want to uncover a card?")
        choosePlayer(input())