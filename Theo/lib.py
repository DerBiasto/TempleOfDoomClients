import requests
import time

#IP = "10.255.22.141:8000"
IP = "localhost"

s = requests.Session()

def __get(path: str):
    r = s.get(f"http://{IP}/" + path)
    if not r.text:
        return r.reason
    return r.json()

def __post(path: str):
    r = s.post(f"http://{IP}/" + path)
    if not r.text:
        return r.reason
    return r.json()

def create_example_game(n: int = 5):
    return __post(f"example_game/{n}")

def get_game_state(starting=0):
    return __get(f"game/get/state?starting={starting}")

def get_health_check():
    return __get("health_check")

def leave_lobby():
    answer = __post("lobby/leave")
    del s.cookies["game"]
    return answer

def get_lobby_state():
    return __get("lobby/state")

def create_lobby(capacity):
    return __post(f"lobby/new/{capacity}")

def join_lobby(lobby_name):
    return __post(f"lobby/join/{lobby_name}")

def get_lobbies():
    return __get("lobby/get")

def announce(role, treasures, traps):
    return __post(f"game/move/announce?role={role}&treasures={treasures}&traps={traps}")

def choose_player(player_name):
    return __post(f"game/move/choose/{player_name}")

def get_players():
    return __get("game/get/players")

def get_role():
    return __get("game/my/role")

def get_cards():
    return __get("game/my/cards")

def get_remote_player_role(player: str):
    return s.get(f"http://{IP}/game/my/role", cookies = {"user": player}).json()

def get_remote_cards(player):
    return s.get(f"http://{IP}/game/my/cards", cookies = {"user": player}).json()

def get_remote_player_role_from_game(player, game):
    return s.get(f"http://{IP}/game/my/role", cookies = {"user": player, "game": game}).json()

def get_game_state_from_game(game, player, starting=0):
    return s.get(f"http://{IP}/game/get/state?starting={starting}", cookies = {"game": game, "user": player}).json()


def lobby_announce():
    lobby = get_lobby_state()
#    print("You have joind the lobby \"{lobby["name"]}\".")
    print(f"Current Players in the Lobby:\n")
    for player in lobby["players"]:
        print(player)
    player_amount = len(lobby["players"])
    capacity = lobby["capacity"]
    print(f"\nyou need {capacity - player_amount} more players to start the game.")

def lobby_wait():
    lobby = get_lobby_state()
    capacity = lobby["capacity"]
    players = lobby["players"]
    while len(players) < capacity:
        lobby = get_lobby_state()
        if len(lobby["players"]) > players:
            players = lobby["players"]
            print(f"Player {players[-1]} has joined the lobby. ({len(players)}/{capacity})")
        elif lobby["players"] < players:
            print(f"Player {set(lobby["players"]) - set(players)} has left the Lobby. ({players}/{capacity})")
            players = lobby["players"]
        else:
            time.sleep(2)


class GameState:
    def __init__(self):
        self.players = get_players()
        self.n_players = len(self.players)
        self.moves = []
        self.n_moves = 0
        self.role = get_role()
        self.cards = get_cards()
        self.active_player_index = 0
        self.key_player_index = 0
        self.total_treasures = [5, 6, 7, 8, 7, 8, 9, 10][self.n_players - 1]
        self.treasures_found = 0
        self.total_traps = 3 if self.n_players == 10 else 2
        self.traps_found = 0
        self.announcements = {}
        self.n_cards = {p: 5 for p in self.players}
        self.round = 1
        self.n_turn = 0
        self.game_over = False

    @property
    def active_player(self):
        return self.players[self.active_player_index]

    def update(self):
        new_moves = get_game_state(len(self.moves))
        self.moves += new_moves
        self.n_moves += len(new_moves)
        self.turn = len(self.moves) % self.n_players
        for move in new_moves:
            if "Announcement" in move:
                self.announcements[self.active_player] = move["Announcement"]
                self.active_player_index = (self.active_player_index+1) % self.n_players
            elif "Choice" in move:
                self.n_cards[move["Choice"][0]] -= 1
                self.active_player_index = self.players.index(move["Choice"][0])
                self.key_player_index = self.players.index(move["Choice"][0])
                if move["Choice"][1] == "Treasure":
                    self.treasures_found += 1
                elif move["Choice"][1] == "Trap":
                    self.traps_found += 1

class LobbyState:
    def __init__(self):
        self.players = []
        self.capacity = 0
        self.cookies = s.cookies
        self.user = self.cookies["user"]
        self.game = self.cookies["game"]

    def update(self):
        state = get_lobby_state()
        self.players = state["players"]
        self.capacity = state["capacity"]
