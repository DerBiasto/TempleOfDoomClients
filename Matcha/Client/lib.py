from math import ceil
import requests
IP = "localhost"
#IP = "127.0.0.1:8000"
#IP = "10.255.22.215"
#IP = "10.255.22.153"

s = requests.Session()

#Players

def get(path: str):
    try:
        r = s.get(f"http://{IP}/" + path, timeout=5)
        r.raise_for_status()
        if not r.text:
            return {"ok" : True, "response" : r.reason}
        return {"ok" : True, "response" : r.json()}
    except requests.exceptions.Timeout as e:
        return {"ok" : False, "error" : "Timeout", "details" : str(e)}
    except requests.exceptions.ConnectionError as e:
        return {"ok" : False, "error" : "ConnectionError", "details" : str(e)}
    except requests.exceptions.HTTPError as e:
        return {"ok" : False, "error" : "HTTPError", "details" : str(e)}

def post(path: str):
    try:
        r = s.post(f"http://{IP}/" + path, timeout=5)
        r.raise_for_status()
        if not r.text:
            return {"ok" : True, "response" : r.reason}
        return {"ok" : True, "response" : r.json()}
    except requests.exceptions.Timeout as e:
        return {"ok" : False, "error" : "Timeout", "details" : str(e)}
    except requests.exceptions.ConnectionError as e:
        return {"ok" : False, "error" : "ConnectionError", "details" : str(e)}
    except requests.exceptions.HTTPError as e:
        return {"ok" : False, "error" : "HTTPError", "details" : str(e)}

def create_example_game(n: int = 5):
    return post(f"example_game/{n}")

def get_players():
    return get("game/get/players")

def get_state(starting: int =0):             # Returns moves that have been made since the n-th move
    return get(f"game/get/state?starting={starting}")



#Lobbies

def list_lobbies():
    return get("lobby/get")

def join_lobby(name : str):
    return post(f"lobby/join/{name}")

def create_lobby(n: int = 5):
    return post(f"lobby/new/{n}")

def leave_lobby():
    answer = post("lobby/leave")
    del s.cookies["game"]
    return answer
    #return post("lobby/leave")

def lobby_state():
    return get("lobby/state")



# Moves

def choose(player_name):
    return post(f"game/move/choose/{player_name}")

def announce(role, treasures, traps):
    return post(f"game/move/announce?role={role}&treasures={treasures}&traps={traps}")

def get_role():
    return get("game/my/role")

def get_cards():
    return get("game/my/cards")

def health_check():
    return get("health_check")

#Cookies

def get_username():
    return s.cookies["user"]

def get_lobby_name():
    return s.cookies["game"]

def start_player():
    return get_players()[0]

def treasures_found(starting=0):
    moves = get_state(starting)
    treasures = 0
    for move in moves:
        if list(move.keys()) == ["Choice"]:
            if move['Choice'][1] == "Treasure":
                treasures += 1
    return treasures

def count_moves(starting=0):
    return len(get_state(starting))

def total_traps_treasures(size):
    distribution = {
                    3 : (5, 2),
                    4 : (6, 2),
                    5 : (7, 2),
                    6 : (8, 2),
                    7 : (7, 2),
                    8 : (8, 2),
                    9 : (9, 2),
                    10 : (10, 3)
    }   # Spieleranzahl : (Schätze, Fallen)
    return distribution[size]

class gameState(object):
    def __init__(self, players : list):
        self.size = len(players)
        self.number_moves = 0
        self.current_announcements = []
        self.key_holder = players[0]
        self.current_round = 0
        self.active_player = players[0]
        self.treasures = 0
        self.traps= 0
        self.winner = None
        self.players = players
        self.n_cards_left: list = []
        self.moves: list = []
        self.game_phase = "announcing"

    def update(self, new_move: dict):
        self.number_moves += 1
        self.moves += new_move
        if self.current_round != ceil(self.number_moves / (2 * self.size)):
            self.current_round = ceil(self.number_moves / (2 * self.size))
            self.current_announcements.clear()
            self.n_cards_left = [(6 - self.current_round) for i in range(self.size)]
        if list(new_move.keys()) == ["Choice"]:
            self.key_holder = new_move["Choice"][0]
            self.active_player  = new_move["Choice"][0]
            for player in self.players:
                if player == self.active_player:
                    self.n_cards_left[self.players.index(player)] -= 1
            if new_move["Choice"][1] == "Treasure":
                self.treasures += 1
                if self.treasures == total_traps_treasures(self.size)[0]:
                    self.winner = 'Adventurer'
            if new_move["Choice"][1] == "Trap":
                self.traps += 1
                if self.traps == total_traps_treasures(self.size)[1]:
                    self.winner = 'Guardian'
        if list(new_move.keys()) == ["Announcement"]:
            self.current_announcements.append((self.active_player, new_move['Announcement']))
            active_player_index = self.players.index(self.active_player)
            active_player_index += 1
            active_player_index = active_player_index % self.size
            #print(active_player_index) # Debugging
            self.active_player = self.players[active_player_index]
        if self.number_moves == 8 * self.size:
            self.winner = 'Guardian'
        if self.number_moves % (2*self.size) < self.size:
            self.game_phase = "announcing"
        else:
            self.game_phase = "choosing"