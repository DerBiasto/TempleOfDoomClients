import requests
import time
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, HorizontalGroup, VerticalGroup, Grid
from textual.widgets import Button, Label, Digits, ListView, ListItem, Header, Footer, DataTable, Static, Input, Collapsible
from textual.validation import Function, Number, ValidationResult, Validator
from textual.screen import Screen
import sys
import threading
import random
platform = sys.platform

if platform == "win32":
    import winsound

def mus_loop():
    mus_start = int(random.random()*2)
    if platform == "win32":
        while True:
            if mus_start == 0:
                winsound.PlaySound("music/song1.wav", winsound.SND_FILENAME)
                mus_start = 1
            else:
                winsound.PlaySound("music/song2.wav", winsound.SND_FILENAME)
                mus_start = 0


music_thread = threading.Thread(target=mus_loop, daemon=True)
# music_thread.start()

def sfx_error():
    if platform == "win32": threading.Thread(target=winsound.PlaySound, args=('music/sfx_error.wav', winsound.SND_FILENAME)).start()

def sfx_click():
    if platform == "win32": threading.Thread(target=winsound.PlaySound, args=('music/sfx_click.wav', winsound.SND_FILENAME)).start()

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
    r = _postEndpoint("lobby/leave")
    del session.cookies["game"]
    return r

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
        self.playerRoles = {}
        self.playerCards = {}
        self.cards = getMyCards()
        self.role = getMyRole()
        self.keyPlayer = self.players[0]
        self.username = session.cookies.get("user")
        self.phase = 0
        self.playerCardCount = [5]*len(self.players)
        self.round = 1
        self.turn = 1
    def update(self, move: dict):
        self.cards = getMyCards()
        if "Announcement" in move.keys():
            self.turn += 1
            self.gameStateCount += 1
            self.announcementCount += 1
            oldKeyPlayer = self.keyPlayer
            if (self.players.index(self.keyPlayer) < len(self.players)-1):
                self.keyPlayer = self.players[self.players.index(self.keyPlayer)+1]
            else:
                self.keyPlayer = self.players[0]
            self.playerRoles[oldKeyPlayer] = move["Announcement"][0]
            self.playerCards[oldKeyPlayer] = (move["Announcement"][1], move["Announcement"][2])
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
            if move["Choice"][1] == "Treasure":
                self.playerCards[move["Choice"][0]][0]-=1
            elif move["Choice"][1] == "Trap":
                self.playerCards[move["Choice"][0]][1]-=1
            data = {"player": oldKeyPlayer,"type": "Choice", "choosenOne": move["Choice"][0], "card": move["Choice"][1]}
            
        data["backToAnnounce"] = False
        if self.phase == 0 and self.announcementCount % len(self.players) == 0:
            self.phase = 1
            self.turn = 1
        elif self.phase == 1 and self.choiceCount % len(self.players) == 0:
            self.phase = 0
            self.playerCards.clear()
            data["backToAnnounce"] = True
            self.turn = 1
        self.round = int(self.gameStateCount / len(self.players)) + 1
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
#lobbyLoop()

fakeLobbyTable = [("Lobby Name 1", 5, 2), ("Lobby Name 2", 4, 1), ("Lobby Name 3", 3, 1)]

def getLobbyTable():
    # return fakeLobbyTable
    lobbyTable = []
    lobbyDict = listLobbies()
    for lobbyName in lobbyDict.keys():
        lobbyTable.append((lobbyName, lobbyDict[lobbyName]["capacity"], len(lobbyDict[lobbyName]["players"])))
    lobbyTable.sort()
    return lobbyTable

def playerAmountInLobby(lobbyState = getLobbyState()):
    return f"{len(lobbyState["players"])}/{lobbyState["capacity"]}"

class LobbyGrid(Grid):
    
    def __init__(self, *children, name = None, id = None, classes = "lobby-element", disabled = False, markup = True, lobbyName, lobbyCapacity, lobbyPlayerCount):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.lobbyName = lobbyName
        self.lobbyCapacity = lobbyCapacity
        self.lobbyPlayerCount = lobbyPlayerCount

    def compose(self):
        yield Label(self.lobbyName, classes="lobby-name")
        yield Label(f"{self.lobbyPlayerCount}/{self.lobbyCapacity}", classes="lobby-capacity")
        yield Button("Join", classes="join-button", variant="success")
    
    def on_button_pressed(self) -> None:
        joinLobby(self.lobbyName)
        APP.push_screen(WaitingScreen())

class LobbyCreationGroup(HorizontalGroup):

    def __init__(self, *children, name = None, id = None, classes = None, disabled = False, markup = True):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.playerCountInput = 0

    def compose(self):
        yield Input(placeholder="Enter Player Count (3-10)", type="integer", id="player-count-input", validators=[
                Number(minimum=3, maximum=10)], max_length=2)
        yield Button("Create Lobby", variant="warning", id="create-lobby-button")
        yield Button("Example Game", variant="primary", id="example-game-button")

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed):
        if event.value != "":
            self.playerCountInput = int(event.value)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create-lobby-button":
            if self.playerCountInput >= 3 and self.playerCountInput <= 10:
                sfx_click()
                createLobby(self.playerCountInput)
                APP.push_screen(WaitingScreen())
            else:
                sfx_error()
        if event.button.id == "example-game-button":
            if self.playerCountInput >= 3 and self.playerCountInput <= 10:
                sfx_click()
                startExampleGame(self.playerCountInput)
                APP.push_screen(GameScreen())
            else:
                sfx_error()

class Card(Static):
    def __init__(self, content = "", *, expand = False, shrink = False, markup = True, name = None, id = None, classes = "card", disabled = False):
        super().__init__(content, expand=expand, shrink=shrink, markup=markup, name=name, id=id, classes=classes, disabled=disabled)

class MyCards(HorizontalGroup):
    def __init__(self, *children, name = None, id = None, classes = None, disabled = False, markup = True, curState):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.curState = curState
    
    def refresh_cards(self):
        for card in self.curState.cards:
            self.mount(Static(card))

class RightGameSide(VerticalGroup):
    def __init__(self, *children, name = None, id = None, classes = None, disabled = False, markup = True, curState):
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled, markup=markup)
        self.curState = curState
    def compose(self):
        with HorizontalGroup():
            with VerticalGroup(classes="round-turn-counter"):
                with VerticalGroup(classes="border"):
                    yield Static("Round: ")
                    yield Digits(str(self.curState.round))
                with VerticalGroup(classes="border"):
                    yield Static("Turn: ")
                    yield Digits(str(self.curState.turn))
        
            
class PlayerAnnouncement(HorizontalGroup): 
    def __init__(self, *children, name = None, id = None, classes = None, disabled = False, markup = True, playerName, role, treasure, traps): 
        super().__init__(*children, name=name, id=playerName, classes=classes, disabled=disabled, markup=markup) 
        self.playerName = playerName 
        self.role = role 
        self.treasure = str(treasure) 
        self.traps = str(traps)

    def compose(self) -> ComposeResult:
        self.playerLabel = Label(self.playerName, classes="border")
        self.roleLabel = Label(self.role, classes="border")
        self.goldLabel = Label(self.treasure, classes="border")
        self.trapsLabel =  Label(self.traps, classes="border")
        yield HorizontalGroup(
            VerticalGroup(
                Static("Name: "),
                self.playerLabel,
                Static("Role: "),
                self.roleLabel, 
                classes="name-role-holder"
                ),
            VerticalGroup(
                Static("Treasure: "),
                self.goldLabel,
                Static("Traps: "),
                self.trapsLabel,
                classes="name-role-holder"
                )
            )
    def update(self, role, treasure, traps):
        self.roleLabel.update(role)
        self.goldLabel.update(str(treasure))
        self.trapsLabel.update(str(traps))


class GameScreen(Screen):
    CSS = """
    .round-turn-counter {
        width: 10%;
    }
    .border {
        border: white;
        margin: 0 0;
        box-sizing: border-box;
        text-style: bold;
        align: center top;
    }
    #playerList {
        border: heavy $accent;
        width: 40%
    }
    PlayerAnnouncement {
        margin: 0 0 1 0;
        border: white;
    }
    .name-role-holder {
        margin: 0;
        width: 50%;
    }
    """
    def __init__(self, name = None, id = None, classes = None):
        super().__init__(name, id, classes)
        self.curState = gameState()
    def compose(self):
        self.title = "Temple of Terror - Playing"
        yield Header()
        yield HorizontalGroup(VerticalScroll(id="playerList"), RightGameSide(curState=self.curState))
    
    def action_add_announcement(self, player) -> None:
        newAnnouncement = PlayerAnnouncement(playerName=player,role=self.curState.playerRoles[player],treasure=self.curState.playerCards[player][0],traps=self.curState.playerCards[player][1])
        self.query_one("#playerList").mount(newAnnouncement)

    def action_add_empty_announcement(self, player, role, gold, traps) -> None:
        newAnnouncement = PlayerAnnouncement(playerName=player,role=role,treasure=gold,traps=traps)
        self.query_one("#playerList").mount(newAnnouncement)

    def add_annoucements(self):
        for player in self.curState.players:
            self.action_add_empty_announcement(player=player, role="Unknown", gold="-", traps="-")

    def updateEverything(self):
        for player in self.curState.players:
            if player in self.curState.playerCards.keys():
                self.query_one(f"#{player}").update(role=self.curState.playerRoles[player],treasure=self.curState.playerCards[player][0],traps=self.curState.playerCards[player][1])
                #self.action_add_announcement(player)
            elif player in self.curState.playerRoles.keys():
                self.query_one(f"#{player}").update(role=self.curState.playerRoles[player], treasure="-", traps="-")
                #self.action_add_empty_announcement(player=player, role=self.curState.playerRoles[player], gold="-", traps="-")
            else: 
                self.query_one(f"#{player}").update(role="Unknown", treasure="-", traps="-")
                #self.action_add_empty_announcement(player=player, role="Unknown", gold="-", traps="-")
                
    def on_mount(self):
        self.add_annoucements()
        self.set_interval(1, self.queryNewMoves)

    def queryNewMoves(self):
        # if self.curState.keyPlayer == self.curState.username:
        #     if self.curState.phase == 0:
        #         askForAnnouncement(self.curState)
        #         processStateUpdate(self.curState, self.curState.update(getState(self.curState.gameStateCount)[0]))
        #     else:
        #         if askForChoice(self.curState):
        #             processStateUpdate(self.curState, self.curState.update(getState(self.curState.gameStateCount)[0]))
        # else:
        
        moves = getState(self.curState.gameStateCount)
        if len(moves) != 0:
            for move in moves:
                data = self.curState.update(move)
                #self.updateEverything(self.curState, data)
        self.updateEverything()

class WaitingScreen(Screen):
    BINDINGS = [      
        ("d", "toggle_dark", "Toggle Dark Mode")
    ]
    CSS = """
    * {
        align: center top;
    }
    .title {
        text-style: bold;
        width: auto;
        text-overflow: fold;
    }
    .title-container {
        align: center top;
    }
    #players {
        border: heavy $accent;
        width: 100%;
        align: center top;
        text-align: center;
    }
    #player-list-holder {
        width: 30%;
        align: center top;
    }
    .player-in-list {
        width: auto;
        text-align: center;
        margin: 1;
    }
    WaitingScreen {
        align: center top;
    }
    .marked {
        color: $accent;
        text-overflow: fold;
    }
    #leave-lobby-button {
        width: 100%
    }
    """
    def compose(self):
        lobbyState = getLobbyState()
        if lobbyState is None:
            APP.push_screen(GameScreen())
            return
        yield Header()
        self.title = "Temple of Terror - Waiting for Players"
        lobbyNameLabelContainer = HorizontalGroup(Static("Lobby Name: ", classes="title"), Static(getLobbyName(), classes="marked"), classes="title-container")
        playerCountStatic = Static(playerAmountInLobby(lobbyState), id="playerCountStatic", classes="title")
        playerLabelContainer = HorizontalGroup(Static("Players: ", classes="title"), playerCountStatic, classes="title-container")
        lobbySelectionHolder = VerticalGroup(lobbyNameLabelContainer, playerLabelContainer, VerticalScroll(id="players"), Button("Leave", "error", id="leave-lobby-button"), id="player-list-holder")
        
        yield lobbySelectionHolder
        
    def refreshPlayerList(self) -> None:
        lobbyState = getLobbyState()
        if lobbyState is None:
            APP.push_screen(GameScreen())
            return
        self.query_one("#playerCountStatic").update(playerAmountInLobby(lobbyState))
        for aPlayer in self.query(".player-in-list"):
            aPlayer.remove()
        for player in lobbyState["players"]:
            player = Static(player +(" (you)" if player == getUsername() else ""), classes="player-in-list")
            self.query_one("#players").mount(player)
            player.scroll_visible()
    
    def on_mount(self):
        self.refreshPlayerList()
        self.set_interval(1, self.refreshPlayerList)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "leave-lobby-button":
            leaveLobby()
            self.dismiss()


class LobbyApp(App):
    BINDINGS = [      
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("r", "refresh", "Refresh Lobbies")
    ]
    CSS = """
    * {
        align: left top;
    }
    .title {
        text-style: bold;
        width: auto;
    }
    .title-container {
        align: center top;
    }
    #lobbies {
        border: heavy $accent;
        width: 100%;
    }
    #create-lobby-button {
        margin: 0 1;
    }
    #example-game-button {
        margin: 0 1;
    }
    #lobby-selection-holder {
        width: 50%;
    }
    #lobby-creation-holder {
        width: 50%;
    }
    #player-count-input {
        width: 50%;
    }
    .lobby-element {
        margin: 0;
        width: 100%;
        border: solid $accent;
        align: center middle;
        grid-size: 3;
        grid-columns: 70% 15% 15%;
        height: auto;
    }
    .lobby-name {
        height: 100%;
        margin: 1;
    }
    .lobby-capacity {
        margin: 1;
    }
    .join-button {
        display: block;
        width: auto;
        align: center middle;
        text-align: center;
    }
    LobbyCreationScreen {
        margin: 1;
    }
    """
    def compose(self) -> ComposeResult:
        self.title = "Temple of Terror - Main Menu"
        yield Header()
        
        yield Footer()

        lobbyLabelContainer = HorizontalGroup(Static("Lobby Selection", classes="title"), classes="title-container")
        lobbySelectionHolder = VerticalGroup(lobbyLabelContainer, VerticalScroll(id="lobbies"), id="lobby-selection-holder")
        
        createLabelContainer = HorizontalGroup(Static("Lobby Creation", classes="title"), classes="title-container")
        lobbyCreationHolder = VerticalGroup(createLabelContainer, LobbyCreationGroup(), id="lobby-creation-holder")
        
        yield HorizontalGroup(lobbySelectionHolder, lobbyCreationHolder)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_refresh(self) -> None:
        """An action to add a lobby"""
        for aLobby in self.query(".lobby-element"):
            aLobby.remove()
        for lobby in getLobbyTable():
            newLobby = LobbyGrid(lobbyName=lobby[0], lobbyCapacity=lobby[1], lobbyPlayerCount=lobby[2])
            self.query_one("#lobbies").mount(newLobby)
            #newLobby.scroll_visible()
    
    def on_mount(self):
        self.action_refresh()
        self.set_interval(5, self.action_refresh)

APP = LobbyApp()
APP.run()

