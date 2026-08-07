from math import ceil

import httpx

IP = "localhost"
#IP = "127.0.0.1:8000"
#IP = "10.255.22.215"
#IP = "10.255.22.153"

client = httpx.AsyncClient()

#Players

async def get(path: str):
    try:
        r = await client.get(f"http://{IP}/" + path, timeout=5)
        r.raise_for_status()
        if not r.text:
            return {"ok" : True, "response" : r.reason_phrase}
        return {"ok" : True, "response" : r.json()}
    except httpx.TimeoutException as e:
        return {"ok" : False, "error" : "Timeout", "details" : str(e)}
    except httpx.ConnectError as e:
        return {"ok" : False, "error" : "ConnectionError", "details" : str(e)}
    except httpx.HTTPStatusError as e:
        return {"ok" : False, "error" : "HTTPError", "details" : str(e)}

async def post(path: str):
    try:
        r = await client.post(f"http://{IP}/" + path, timeout=5)
        r.raise_for_status()
        if not r.text:
            return {"ok" : True, "response" : r.reason_phrase}
        return {"ok" : True, "response" : r.json()}
    except httpx.TimeoutException as e:
        return {"ok" : False, "error" : "Timeout", "details" : str(e)}
    except httpx.ConnectError as e:
        return {"ok" : False, "error" : "ConnectionError", "details" : str(e)}
    except httpx.HTTPStatusError as e:
        return {"ok" : False, "error" : "HTTPError", "details" : str(e)}

async def create_example_game(n: int = 5):
    return await post(f"example_game/{n}")

async def get_players():
    return await get("game/get/players")

async def get_state(starting: int =0):             # Returns moves that have been made since the n-th move
    return await get(f"game/get/state?starting={starting}")

#Lobbies

async def list_lobbies():
    return await get("lobby/get")

async def join_lobby(name : str):
    return await post(f"lobby/join/{name}")

async def create_lobby(n: int = 5):
    return await post(f"lobby/new/{n}")

async def leave_lobby():
    answer = await post("lobby/leave")
    del client.cookies["game"]
    return answer
    #return post("lobby/leave")

async def lobby_state():
    return await get("lobby/state")

# Moves

async def choose(player_name):
    return await post(f"game/move/choose/{player_name}")

async def announce(role, treasures, traps):
    return await post(f"game/move/announce?role={role}&treasures={treasures}&traps={traps}")

async def get_role():
    return await get("game/my/role")

async def get_cards():
    return await get("game/my/cards")

async def health_check():
    return await get("health_check")

#Cookies

def get_username():
    return client.cookies.get("user")

def get_lobby_name():
    return client.cookies["game"]

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

class GameState:
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
        self.required_treasures, self.required_traps = total_traps_treasures(self.size)

    def update(self, new_move: dict):
        self.number_moves += 1
        self.moves.append(new_move)
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