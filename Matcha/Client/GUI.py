from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Select, ListItem, ListView
from textual.screen import Screen
import lib
#from textual import log

class LobbySelection(Screen):
    
    CSS_PATH = "lobby_selection.tcss"

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Button(label="Create a new lobby", variant="success", id="new_lobby")
            yield Button(label="Join an existing lobby", variant="success", id="join_lobby")
            yield Button(label="Create an example game", variant="success", id="example_game")
            yield  Select(
            options=[
                ("3 Players", 3),
                ("4 Players", 4),
                ("5 Players", 5),
                ("6 Players", 6),
                ("7 Players", 7),
                ("8 Players", 8),
                ("9 Players", 9),
                ("10 Players", 10),
                ],
            id="player_select",
            prompt="Choose how many players should be in your game"
            )
            lobbies = lib.list_lobbies()["response"]

            yield  Select(
            options=[ (lbname + " " + repr(lbcont), lbname) for lbname, lbcont in lobbies.items()],
            id="lobby_select",
            prompt="Choose the Lobby you want to join"
            )
            
            lobbies = lib.list_lobbies()["response"]
            items = []
            for lobby_name, lobby_data in lobbies.items():
                player_str = " ".join(lobby_data["players"])
                items.append(ListItem(Horizontal(Label(lobby_name, classes="lobby_names"), Label(player_str, classes="players"), Label(f"{len(lobby_data["players"])}/{lobby_data["capacity"]}", classes="capacity")),classes="rows"))
            yield ListView(
                ListItem(Label("One")),
                ListItem(Label("Two")),
                ListItem(Label("Three")),
                *items
            )

    #def on_mount(self):
    #    self.set_interval(1, self.update_lobby_selection)

    #def update_lobby_selection(self):
    #    lobbies = lib.list_lobbies()["response"]
    #    new_options=[ (lbname + " " + repr(lbcont), lbname) for lbname, lbcont in lobbies.items()]
    #    self.query_one("#lobby_select").options = new_options
    
    def on_select_changed(self, event: Select.Changed):
        yield event.value
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "new_lobby":
            lib.create_lobby(self.query_one("#player_select").value)  # ty:ignore[unresolved-attribute]
            self.app.push_screen(Waiting())
        elif event.button.id == "join_lobby":
            selected_lobby = self.query_one("#lobby_select").value
            self.app.log("Value of selected_lobby:", selected_lobby)
            if selected_lobby is not Select.NULL:
                self.app.log("if-statement executed")
                lib.join_lobby(selected_lobby)  # ty:ignore[unresolved-attribute]
                self.app.push_screen(Waiting())
        elif event.button.id == "example_game":
            lib.create_example_game(self.query_one("#player_select").value)  # ty:ignore[unresolved-attribute]
            self.app.push_screen(Game())

class Waiting(Screen):
    def compose(self) -> ComposeResult:
        self.status = Label("", id="lobby_status")
        yield self.status
        self.player_list = Label(content="", id="player_list")
        yield self.player_list        
    
    def on_mount(self):
        self.set_interval(1, self.update_lobby_status)
    
    def update_lobby_status(self):
        state: dict = lib.lobby_state()["response"]
        players = ""
        for player in state["players"]:
            players += f"{player}\n"
        n_players: int = len(players)
        capacity: int = state["capacity"]
        players_to_start = capacity - n_players
        #self.status.update(f"{players} {n_players}/{capacity} Players")
        self.query_one("#lobby_status").update(f"The following players are currently waiting in the Lobby:\n{players}\n{players_to_start} are still needed for the game to start")
        #with Vertical():
        #    yield Label(str(self.x))
        #    yield Button(label="", variant="success", id="first", disabled = False)
        #    yield Button(label="Add 1", variant="success", id="second", disabled = False)

    def on_button_pressed(self, event):
        self.query_one(Label).update(str(""))
        if event.button.id == "first":
            btn = event.button
            btn.label = "You clicked me"


class Game(Screen):
    x = 12
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(str(self.x))
            yield Button(label="", variant="success", id="first", disabled = False)
            yield Button(label="Add 1", variant="success", id="second", disabled = False)
        with Horizontal():
            yield Label(str(self.x))
            yield Button(label="Add 1", variant="success", id="third", disabled = False)
            yield Button(label="Add 1", variant="success", id="forth", disabled = False)

    def on_button_pressed(self, event):
        self.x += 1
        self.query_one(Label).update(str(self.x))
        if event.button.id == "first":
            btn = event.button
            btn.label = "You clicked me"

class TempleOfDoom(App):
    def on_mount(self):
        self.push_screen(LobbySelection())

if __name__ == "__main__":
    app = TempleOfDoom()
    app.run()