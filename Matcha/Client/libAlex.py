import requests         # Funktion kann man nicht als pprint printen
import math


IP = "10.255.22.215"

s = requests.Session()

def __get(path: str):                                  # __ -man darf nicht im terminal das nutzen (nur in Funktion) -braucht man nicht unbedingt weil ty installiert ist
    r = s.get(f"http://{IP}/" + path)    # //-du darfst nicht  # path: str -nur strings werden akzeptiert -Fehlermeldung sag, error weil keine String
    if not r.text:
        return r.reason
    return r.json()

def __post(path: str):
    r = s.post(f"http://{IP}/" + path)      # +path weil dann der Befehl eingesetzt wird
    if not r.text:
        return r.reason
    return r.json()



def create_example_game(n: int = 5):                       # wenn keine Zahl gegeben, nimmt einfach 5
    return __post(f"example_game/{n}")                # f weil eine Variable drinnen ist

def health_check():
    return __get("health_check")




def get_state(starting_point: int = 0):                                    # ()leere Klammer -Funktion
    return __get(f"game/get/state?starting={starting_point}")    # starting...ab dem n-ten move (!zählen ab 0)

def get_announcements():
    return [
        move["Announcement"]                                   # nur Wert von Adventurer
        for i, move in enumerate(iterable=get_state())         # for i: schleife, iterable: durchgehen, enumerate: durchzählen (mit Zahl benennen)
        if "Announcement" in move 
        and i >= len(get_players())*2*(round_number()-1)       # *2: Announcement wird erst danach drauf angewendet; Choice sind noch dabei
    ]

def get_choices(n: int =0):
    return [
        move["Choice"]
        for i, move in enumerate(iterable=get_state())
        if "Choice" in move 
        and i >= len(get_players())*2*(round_number()-1+n)
    ]



def get_players():
    return __get("game/get/players")

def announce(r,ts,tp):                  # variabeln werden vom Spieler eingegeben
    return __post(f"game/move/announce?role={r}&treasures={ts}&traps={tp}")

def choose_player(playername):
    return __post(f"game/move/choose/{playername}")

def get_my_cards():
    return __get("game/my/cards")

def get_my_role():
    return __get("game/my/role")



def get_current_lobbies():
    return __get("lobby/get")

def join_lobby(lobby_name):
    return __post(f"lobby/join/{lobby_name}")

def leave_lobby():
    del s.cookies ["game"]
    return __post("lobby/leave")

def create_lobby(capacity: int = 5):
    return __post(f"lobby/new/{capacity}")

def get_lobby_state():
    return __get("lobby/state")



def found_treasures():
    amount = 0
    moves = get_state()
    for move in moves:
        if "Choice" in move:
            if (move["Choice"][1] == "Treasure"):
                amount += 1
    return amount

def found_traps():
    amount = 0
    moves = get_state()
    for move in moves:
        if "Choice" in move:
            if (move["Choice"][1] == "Trap"):
                amount += 1
    return amount


def total_traps():
    if len(get_players()) == 10:
        return 3
    return 2

def total_treasures():
    treasures = {
        3: 5,
        4: 6,
        5: 7,
        6: 8,
        7: 7,
        8: 8,
        9: 9,
        10: 10
    }
    return treasures[len(get_players())]

def result():
    if found_traps() == total_traps():
        return("-Guardians win-")
    if found_treasures() == total_treasures():
        return("-Adveturers win-")
    if len(get_state()) == len(get_players())*4*2:       # 4 wegen insg. 4 Runden, 2 wegen announcement + choice
        return("-Guardians win-")
    return("the game is not over yet...")


def round_number():
    return math.ceil(len(get_state()) / len(get_players()) / 2)    # math.ceil heißt immer aufrunden (auch bei 0,1)


def get_key_player():
    if round_number() == 1 and not get_choices():
        return get_players()[0]
    if not get_choices():
        return get_choices(-1)[-1][0]
    return get_choices() [-1][0]

class gameState(object):
    def __init__(self, starting_player):
        self.key_holder = starting_player
        self.