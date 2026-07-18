#Start the Server by typing: "python -m uvicorn main:app --reload" into the terminal
from fastapi import FastAPI, Request, Response, Path
from random_username.generate import generate_username
import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class ServerState(object):
    def __init__(self):
        self.all_lobbies = {}
        self.n_of_lobbies = 0
    def add_lobby(self, new_lobby):  # type: ignore # noqa: F821
        self.all_lobbies[new_lobby.name] = new_lobby
        self.n_of_lobbies += 1

server_state = ServerState()

class Lobby(object):
    def __init__(self, cap, starting_player):
        self.players = [starting_player]
        self.capacity = cap
        self.name = generate_username(1)[0]
        self.is_full = False
    def join(self, new_player):
        if self.is_full:
            pass #add game logic later
        self.players.append(new_player)
        if self.players == self.capacity:
            self.is_full

@app.get("/health_check")
def health_check():
    return "OK"

@app.post("/lobby/new/{capacity}", status_code=201)
def new_lobby(request: Request, response: Response, capacity: int = Path(..., ge=3, le=10)):
    user: str | None = request.cookies.get("username")
    if not user:
        user = generate_username(1)[0]
        response.set_cookie(key="user", value = user)
    new_lobby = Lobby(capacity, user)
    response.set_cookie(key="game", value = new_lobby.name)
    server_state.add_lobby(new_lobby)
    logging.info(f"New Lobby created - state is now {server_state.all_lobbies[new_lobby.name]}, {server_state.all_lobbies}")
    #return "Created"

@app.post("/lobby/join/{lobby_name}")
def join_lobby(request: Request, response: Response, lobby_name: str):
    username: str | None = request.cookies.get("username")
    if not username:
        username = generate_username(1)[0]
        response.set_cookie(key = "user", value = username)
    lobby = server_state.all_lobbies.get(lobby_name)
    if lobby:
        lobby.join(username)
        response.set_cookie(key="game", value = lobby.name)
        logging.info(f"Lobby joined - state is now {server_state.all_lobbies[lobby.name].players}, {server_state.all_lobbies}")
        return "Lobby joined successfully"
    else:
        return "Forbidden"

@app.get("/lobby/get")
def get_lobbies():
    # return list(server_state.all_lobbies.values()) # {lobby_name: [liste von players, cap]}
    return {
        lobby.name: {"players" : lobby.players, "capacity" : lobby.capacity}
        for lobby in server_state.all_lobbies.values()
    }

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}