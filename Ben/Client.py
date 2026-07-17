import requests
import pprint
import time
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, HorizontalGroup, VerticalGroup, Grid
from textual.widgets import Button, Label, Digits, Footer, Header
from textual.screen import Screen
IP = "10.255.22.192"
s = requests.Session()
state = 0
a = []

def __get(path):
    r = s.get(f"http://{IP}/" + path)
    if not r.text:
        return r.reason
    return r.json()

def __post(path):
    r = s.post(f"http://{IP}/" + path)
    if not r.text:
        return r.reason
    return r.text

def create_example_game(n: int= 5):
    if n < 3:
        print("You need more participants!")
    if n > 10:
        print("You have too much participants!")
    return __post(f"example_game/{n}")
    
def get_players():
    return __get("game/get/players")
    
def get_state():
    global a
    r = __get(f"game/get/state?starting={0}")
    if len(r) > len(a):  
        v = __get(f"game/get/state?starting={len(a)}")
        a = __get(f"game/get/state?starting={0}")
        return v
    
def get_staten(starting=0):
    return __get(f"game/get/state?starting={starting}")
A:str = "Adventurer"
G:str = "Guardian"
def announce(role: str = "Adventurer", treasures: int = 0, traps: int= 0):
    return __post(f"game/move/announce?role={role}&treasures={treasures}&traps={traps}")

def choose_player(name: str):
    return __post(f"game/move/choose/{name}")

def my_cards():
    return __get("game/my/cards")

def my_role():
    return __get("game/my/role")

def list_lobby():
    print("Open Lobbys:")
    return __get("lobby/get")

def join_lobby(lobbyname: str):
    return __post(f"lobby/join/{lobbyname}")

def leave_lobby():
    return __post("lobby/leave")

def new_lobby(capacity: int = 5):
    return __post(f"lobby/new/{capacity}")

def lobby_state():
    return __get("lobby/state")

def get_username():
    return s.cookies.get("user")

def treasures_found():
    treasure = 0
    r = __get(f"game/get/state?starting={0}")
    for index in range (len(r)):
        if list(r[index].keys())[0] == "Choice":
            s = r[index]["Choice"]
            if s[1] == "Treasure":
                treasure += 1
    return treasure     

def traps_found():
    trap = 0
    r = __get(f"game/get/state?starting={0}")
    for index in range (len(r)):
        if list(r[index].keys())[0] == "Choice":
            s = r[index]["Choice"]
            if s[1] == "Traps":
                trap += 1
    return trap

treasure_table = [0, 0, 0, 5, 6, 7, 8, 7, 8, 9, 10]
traps_table = [0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 3]
cardcounter_table = [0, 0, 0, 12, 16, 20, 24, 28, 32, 36, 40]

def gameover(state):
    if state.treasures_found == treasure_table[len(state.player_list)]:
        state.adventurers_win = True
        return True
    if state.traps_found == traps_table[len(state.player_list)]:
        state.guardians_win = True
        return True
    if state.cardcounter == cardcounter_table[len(state.player_list)]:
        state.guardians_win = True
        return True
    else:
        return False

class State:
    def __init__(self):
        self.my_role = my_role()
        self.my_cards = my_cards()
        self.treasures_found = 0
        self.traps_found = 0
        self.player_list = get_players()
        self.keyplayer = self.player_list[0]
        self.keyplayer_index = self.player_list.index(self.keyplayer)
        self.cardcounter = 0
        self.movecounter = 0
        self.gameover = False 
        self.username = get_username()
        self.guardians_win = False
        self.adventurers_win = False
        self.last_move = []
        self.current_announcements = {p: None for p in self.player_list}

    def update(self, move):
        self.movecounter += 1
        if self.movecounter%(2 * len(self.player_list)) == 0:
            self.my_cards = my_cards()
            for p in self.current_announcements:
                self.current_announcements[p] = None
        if "Choice" in move:
            if move["Choice"][1] == "Treasure":
                self.treasures_found += 1
            if move["Choice"][1] == "Trap":
                self.traps_found += 1
            self.keyplayer = move["Choice"][0]
            self.keyplayer_index = self.player_list.index(self.keyplayer)
            self.cardcounter += 1
            self.last_move = move
        if "Announcement" in move:
            self.last_move = move
            self.current_announcements[self.keyplayer] = move["Announcement"]
            if self.keyplayer_index + 1 < len(self.player_list):
                self.keyplayer = self.player_list[self.keyplayer_index + 1]
                self.keyplayer_index += 1
            else:
                self.keyplayer = self.player_list[0]
                self.keyplayer_index = 0

def play():#wird nur ausgeführt bei einem TEXTBASIERTEN Spiel
    state = State()
    while not gameover(state):
        for move in get_staten(state.movecounter):
            print(move)
            state.update(move)
            print(state.keyplayer + ":")
        # if you are active make your move
        if state.username == state.keyplayer:
            if state.movecounter%(len(state.player_list) * 2) < len(state.player_list):
                
                if state.movecounter < len(state.player_list):
                    print(my_role())
                  
                print(my_cards())
                print("You have to announce:")
                r = announce(str(input("Your role:")), int(input("Treasures:")), int(input("Traps:")))
                print(r)
            if state.movecounter%(len(state.player_list) * 2) >= len(state.player_list):
                
                print("You have to choose:")
                choose_player(str(input("Which Player do you choose:")))
                
        time.sleep(1)
    if state.adventurers_win is True:
        print("Adventurers WIN!")
    else:
        print("Guardians WIN!")

class TextualApp(App):
    def compose(self) -> ComposeResult:
        start = Button("Start", id = "Start")
        start.styles.visibility = "hidden"
        yield start
        
    def on_mount(self):
        self.push_screen(Game_menu())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "Play":
            self.push_screen(Start_screen())
        if event.button.id == "Join_Lobby":
            self.push_screen(Lobbyscreen())
        if event.button.id == "Create_Lobby":
            self.push_screen(Start_screen_lobby())
        if event.button.id == "Back":
            self.pop_screen()

    def in_game(self):
        create_example_game(self.playercount)   

class Game_menu(Screen):
    def compose(self):
        yield Button("Play", id = "Play")
        yield Button("Join Lobby", id = "Join_Lobby")
        yield Button("Create Lobby", id = "Create_Lobby")
        yield Header("Temple of Terror")

class Lobbyscreen(Screen, VerticalGroup):
    def compose(self):
        for key in list_lobby().keys():
            yield Button(key, id = key)
        yield Button("Back", id = "Back")

    def on_button_pressed(self, event: Button.Pressed) -> None: # update_screen muss weg gepopt werden
        if event.button.id !="Back":
            join_lobby(event.button.id)   
            self.app.push_screen(In_Lobby())

class In_Lobby(Screen):
    def compose(self):
        yield Label(s.cookies.get("game"))
        if lobby_state() is not None:
            yield Label(f"{len(lobby_state()["players"])} / {lobby_state()["capacity"]} Players", id = "lobby_players")

    def on_mount(self):
        self.set_interval(1, self.update_lobby_status)

    def update_lobby_status(self):
        state = lobby_state()
        if state is None:
            self.app.pop_screen()
            self.app.push_screen(In_game())
            return
        self.query_one("#lobby_players").update(f"{len(state["players"])} / {state["capacity"]} Players")

class Start_screen(Screen):
    playercount = 3
    def compose(self):
        yield Button("Start", id = "Start")
        yield Button("+", id = "plus")
        yield Button("-", id = "minus")
        yield Digits(str(self.playercount), id = "playercount")
        yield Button("Back", id = "Back")

    def add_player(self): # fertig
        if self.playercount < 10:
            self.playercount += 1
            self.query_one("#playercount").update(str(self.playercount)) 
    
    def minus_player(self): # fertig
        if self.playercount >= 4:
            self.playercount -= 1
            self.query_one("#playercount").update(str(self.playercount))
    
    def on_button_pressed(self, event: Button.Pressed) -> None: # fertig
        if event.button.id == "plus":
            self.add_player()
        if event.button.id == "minus":
            self.minus_player()
        if event.button.id == "Start":
            create_example_game(self.playercount)
            self.app.push_screen(In_game())

class Announcements(Screen, Grid):
    def __init__(self):
        super().__init__()
        self.announce_treasures = 0
        self.announce_traps = 0

    def compose(self):
        with Horizontal():
            yield Label(f"Cards: {my_cards()}")
            yield Label(f"Role: {my_role()}")
            yield Digits(str(" "), id = "place_holder1")
        with Horizontal():
            yield Button("-", id = "minus_treasures")
            yield Digits(str(f"(Treasures) {self.announce_treasures}"), id = "announce_treasures")
            yield Button("+", id = "plus_treasures")
        with Horizontal():
            yield Button("-", id = "minus_traps")
            yield Digits(str(f"(Traps) {self.announce_traps}"), id = "announce_traps")
            yield Button("+", id = "plus_traps")
        with Horizontal():
            yield Button("Adventurer", id = "Adventurer")
            yield Digits(str(" "), id = "place_holder")
            yield Button("Guardian", id = "Guardian")

    def on_button_pressed(self, event: Button.Pressed) -> None: # fertig
        if event.button.id == "Adventurer":
            announce("Adventurer", self.announce_treasures, self.announce_traps)
            self.app.pop_screen()
        if event.button.id == "Guardian":
            announce("Guardian", self.announce_treasures, self.announce_traps)
            self.app.pop_screen()
        if event.button.id == "plus_treasures":
            self.announce_treasures += 1
            self.query_one("#announce_treasures").update(str(self.announce_treasures))
        if event.button.id == "minus_treasures":
            self.announce_treasures -= 1
            self.query_one("#announce_treasures").update(str(self.announce_treasures))
        if event.button.id == "plus_traps":
            self.announce_traps += 1
            self.query_one("#announce_traps").update(str(self.announce_traps))
        if event.button.id == "minus_traps":
            self.announce_traps -= 1
            self.query_one("#announce_traps").update(str(self.announce_traps))

class Choosen(Screen):
    def __init__(self, state):
        super().__init__()
        self.state = state

    def compose(self):
        for player in self.state.player_list:
            announcement = self.state.current_announcements[player]
            with Horizontal():
                yield Button(player, id = player)
                yield Label(repr(announcement))

    def on_button_pressed(self, event: Button.Pressed) -> None: # fertig
        choose_player(event.button.id)
        self.app.pop_screen()

    CSS = """
    Announcements {
        border: heavy $accent;
        grid-size: 3;
        grid-columns: 20% 20% 20%;
    }      
    """

class Start_screen_lobby(Screen):
    playercount_lobby = 3
    def compose(self):
        yield Button("Start", id = "Start")
        yield Button("+", id = "plus")
        yield Button("-", id = "minus")
        yield Digits(str(self.playercount_lobby), id = "playercount")
        yield Button("Back", id = "Back")

    def add_player(self): # fertig
        if self.playercount_lobby < 10:
            self.playercount_lobby += 1
            self.query_one("#playercount").update(str(self.playercount_lobby))
        
    def minus_player(self): # fertig
        if self.playercount_lobby >= 4:
            self.playercount_lobby -= 1
            self.query_one("#playercount").update(str(self.playercount_lobby))
    
    def on_button_pressed(self, event: Button.Pressed) -> None: # fertig
        if event.button.id == "plus":
            self.add_player()
        if event.button.id == "minus":
            self.minus_player()
        if event.button.id == "Start":
            new_lobby(self.playercount_lobby)
            self.app.push_screen(In_Lobby())
    
class AdventurersWIN(Screen):
    def compose(self):
        yield Label("ADVENTURERS WIN!!!")

class GuardiansWIN(Screen):
    def compose(self):
        yield Label("GUARDIANS WIN!!!")

class In_game(Screen):# Fehler bei Lobbys es werden wohl keine spielzüge gespeichert, bzw.übertragen. oder gleich wieder überschrieben/gelöscht.
    def __init__(self):
        super().__init__()
        self.state: State = State()
        #self.my_role = my_role()
        #self.treasures_found = 0
        #self.traps_found = 0
        #self.player_list = get_players()
        #assert self.player_list != "Forbidden"
        #self.keyplayer = self.player_list[0]
        #assert len(self.keyplayer) > 1
        #self.keyplayer_index = self.player_list.index(self.keyplayer)
        #self.cardcounter = 0
        #self.movecounter = 0
        #self.gameover = False 
        self.username = get_username()
        #self.guardians_win = False
        #self.adventurers_win = False
        #self.last_move = []

    def compose(self):
        with Horizontal():
            with Vertical():
                yield Digits(str(self.state.treasures_found), id = "treasures")
                yield Digits(str(self.state.traps_found), id = "traps")
                yield Digits(str(self.state.cardcounter), id = "cards")
                yield Label(f" Your name: {str(self.username)}", id = "username")
                yield Label(f" Participants: {str(self.state.player_list)}", id = "player_list")
                yield Button("Announcement", id = "Announcement", disabled = True)#disabled
                yield Button("Choose", id = "Choose", disabled = True)#disabled
                yield Label(str(self.state.last_move), id = "last_move")# hier sagt er State hat kein move ich muss einen last move variable einführen!
                yield Label(f" Keyplayer: {str(self.state.keyplayer)}", id = "keyplayer")
                yield Label(f" Your role: {str(self.state.my_role)}", id = "my_role")
                yield Label(f" Your cards: {str(self.state.my_cards)}", id = "my_cards")
            with Vertical():
                yield Vertical(id = "vertical")

    def on_mount(self):
        self.set_interval(5, self.update_game_status)
        self.notify("mounted")

    

    def update_game_status(self):
        self.notify(f"updating {self.state.movecounter}")
        for move in get_staten(self.state.movecounter): 
            self.notify(repr(move))           
            self.state.update(move)
            self.query_one("#cards").update(str(self.state.cardcounter))
            self.query_one("#traps").update(str(self.state.traps_found))
            self.query_one("#treasures").update(str(self.state.treasures_found))
            self.query_one("#last_move").update(str(self.state.last_move))
            self.query_one("#my_cards").update(str(self.state.my_cards))
            self.query_one("#my_role").update(str(self.state.my_role))
            self.query_one("#keyplayer").update(str(self.state.keyplayer))
            self.query_one("#vertical").mount(Label(str(f"{self.state.player_list[self.state.keyplayer_index - 1]}: {self.state.last_move}")))
        # if you are active make your move
        if self.state.username == self.state.keyplayer:
            if self.state.movecounter%(len(self.state.player_list) * 2) < len(self.state.player_list):
                self.query_one("#Choose").disabled = True
                self.query_one("#Announcement").disabled = False # Muss ich gucken ob es klappt, oder ob ich einen anderen befehl
            if self.state.movecounter%(len(self.state.player_list) * 2) >= len(self.state.player_list):
                self.query_one("#Announcement").disabled = True
                self.query_one("#Choose").disabled = False
        if gameover(self.state) is True:
            if self.state.adventurers_win is True:
                self.app.push_screen(AdventurersWIN())
            if self.state.guardians_win is True:
                self.app.push_screen(GuardiansWIN())
            
    def on_button_pressed(self, event: Button.Pressed) -> None: # fertig
        if event.button.id == "Announcement":
            self.app.push_screen(Announcements())
        if event.button.id == "Choose":
            self.app.push_screen(Choosen(self.state))
            
if __name__=="__main__":
    TextualApp().run()

def move_counter():
    moves = len(get_staten(0))
    print(moves)
    return moves





        

     


            








