import requests
import math

IP =   "10.255.22.215" #"10.255.22.156"

s= requests.session()

def __get(path):
    r=s.get(f"http://{IP}/"+path)
    if not r.text:
        return r.reason
    return r.json()


def __post(path):
    r=s.post(f"http://{IP}/"+path)
    if not r.text:
        return r.reason
    return r.json()


#game

def create_example_game(n: int=5):
    return __post(f"example_game/{n}")


def get_players():
    return __get("game/get/players")


def get_state(starting=0):
    return __get(f"game/get/state?starting={starting}")


def post_announcement(r,ts,tp):
    return __post(f"game/move/announce?role={r}&treasures={ts}&traps={tp}")


def choose_player(playername):
    return __post(f"game/move/choose/{playername}")


def get_cards():
    return __get("game/my/cards")


def get_role():
    return __get("game/my/role")


#lobby

def get_lobby():
    return __get("lobby/get")


def join_lobby(name):
    return __post(f"lobby/join/{name}")


def leave_lobby():
   return __post("lobby/leave")
   del s.cookies["game"]


def new_lobby(n: int=5):
    return __post(f"lobby/new/{n}")


def get_lobby_state():
    return __get("lobby/state")

#add ons

def treasures_found():
    moves = get_state()
    anzahl =0
    for move in moves:
        if "Choice" in move:
            if (move["Choice"][1] == "Treasure"):
                anzahl += 1
    return anzahl
   # return len(move for move in get_state() if "Choice" in move and move["Choice"][1] == "Treasure")

def traps_found():
    moves = get_state()
    anzahl =0
    for move in moves:
        if "Choice" in move:
            if (move["Choice"][1] == "Trap"):
                anzahl += 1
    return anzahl


def total_treasures():
    treasures:dict[int,int]={
        3:5,
        4:6,
        5:7,
        6:8,
        7:7,
        8:8,
        9:9,
        10:10
    }
    return treasures[len(get_players())]


def total_traps(n:int=5):
    if len(get_players())==10:
        return 3
    return 2


def game_over():
    if traps_found()==total_traps:
        return("Guardians win! Well done!")

    if treasures_found()==total_treasures:
        return("Adventurers win! Well done!")

    if len(get_state())== len(get_players())*2*4:
        return("Guardians win! Well done!")
    
    return ("The game is not over yet!")


def round_number():
    return math.ceil(len(get_state()) / len(get_players()) / 2)


def get_announcements(): 
    return [
        move ["Announcement"]
        for i, move in enumerate(get_state())
         if "Announcement" in move 
         and i >= len(get_players())*2*(round_number()-1)
         ]
    

def get_choices(n: int=0):
    return[
        move ["Choice"]
        for i, move in enumerate(get_state())
            if "Choice" in move
            and i >= len(get_players())*2*(round_number()-1+n)
    ]


"""def get_key_player():
    if round_number()==1 and not get_choices():
        return get_players()[0]
    if not get_choices:
        return get_choices(-1)[-1][0]
    return get_choices()[-1][0]"""


def get_key_player():
    if not get_choices(-1):
        return get_players()[0]
    return get_choices(-1)[-1][0]

if __name__ == "__main__":
    print(create_example_game())