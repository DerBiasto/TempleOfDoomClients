from textual import log, work  # noqa: F401
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label, Select

import lib


def diff_lobbies(old, new):
    added_lobbies = new.keys() - old.keys()
    removed_lobbies =  old.keys() - new.keys()

    players_changed = set()

    for lobby in old.keys() & new.keys():
        if old[lobby]["players"] != new[lobby]["players"]:
            players_changed.add(lobby)

    return {
        "added": added_lobbies,
        "removed": removed_lobbies,
        "changed": players_changed
    }


class LobbySelection(Screen):
    
    CSS_PATH = "lobby_selection.tcss"

    def compose(self) -> ComposeResult:
        yield Button(label="Create a new lobby", variant="success", id="new_lobby")
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
        allow_blank=False
        )
        yield DataTable()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns(("Name:", "name"), ("Players:", "players"), ("Capacity:", "capacity"))
        self.rendered_lobbies = {}
        self.update_lobby_list()
        self.set_interval(3, self.update_lobby_list)
        
    @work(thread=True, exclusive=True)
    def update_lobby_list(self):
        response = lib.list_lobbies()
        self.app.call_from_thread(self._apply_lobby_updates, response)

    @work(thread=True, exclusive=True)
    def initialize_lobby_creation(self, capacity):
        response = lib.create_lobby(capacity)
        self.app.call_from_thread(self._validate_lobby_creation, response)

    @work(thread=True, exclusive=True)
    def initialize_example_game_creation(self, capacity):
        response = lib.create_example_game(capacity)
        self.app.call_from_thread(self._validate_example_game_creation, response)

    @work(thread=True, exclusive=True)
    def initialize_joining_lobby(self, lobby_name):
        response = lib.join_lobby(lobby_name)
        self.app.call_from_thread(self._validate_joining_lobby, response)

    def on_select_changed(self, event: Select.Changed):
        yield event.value
    
    def on_button_pressed(self, event: Button.Pressed):
        selected_capacity = self.query_one("#player_select").value
        if event.button.id == "new_lobby":
            self.initialize_lobby_creation(selected_capacity)
        elif event.button.id == "example_game":
            self.initialize_example_game_creation(selected_capacity)

    def _apply_lobby_updates(self, response: dict):
        table = self.query_one(DataTable)
        if response["ok"]:
            new_lobbies = response["response"]
            rows = []
            difference = diff_lobbies(self.rendered_lobbies, new_lobbies)
            added_lobbies: set = difference["added"]
            removed_lobbies: set = difference["removed"]
            changed_player_lists: set = difference["changed"]

            for lobby_name in added_lobbies:
                lobby_data = new_lobbies[lobby_name]
                player_str = ", ".join(lobby_data["players"])
                rows.append((lobby_name, player_str, f"{len(lobby_data["players"])}/{lobby_data["capacity"]}"))
            for lobby_name, player_str, capacity in rows:
                table.add_row(lobby_name, player_str, capacity, key=lobby_name)

            for lobby_name in removed_lobbies:
                table.remove_row(lobby_name)

            for lobby_name in changed_player_lists:
                player_str = ", ".join(new_lobbies[lobby_name]["players"])
                capacity = f"{len(new_lobbies[lobby_name]['players'])}/{new_lobbies[lobby_name]['capacity']}"

                table.update_cell(
                    row_key=lobby_name, column_key="players", value=player_str, update_width=True
                )
                table.update_cell(
                    row_key=lobby_name, column_key="capacity", value=capacity, update_width=True
                )
            self.rendered_lobbies = new_lobbies
        else:
            self.app.error_notifications(response["error"])

    def _validate_lobby_creation(self, response):
        if response["ok"]:
            self.app.push_screen(Waiting())
        else:
            self.app.error_notifications(response["error"])

    def _validate_example_game_creation(self, response):
        if response["ok"]:
            self.app.push_screen(Game())
        else:
            self.app.error_notifications(response["error"])

    def _validate_joining_lobby(self, response):
        if response["ok"]:
            self.app.push_screen(Waiting())
        else:
            if response["error"] == "HTTPError":
                self.notify("The selected lobby isn't available anymore. Please reload your lobby list.", severity="error")
            else:
                self.app.error_notifications(response["error"])
        
    def on_data_table_row_selected(self, event):
        selected_lobby = event.row_key.value
        self.initialize_joining_lobby(selected_lobby)

class Waiting(Screen):
    def compose(self) -> ComposeResult:
        yield Label("", id="lobby_status")
        yield Label(content="", id="player_list")       
    
    def on_mount(self):
        self.set_interval(1, self.update_lobby_status)
    
    def update_lobby_status(self):
        #add check if game has started later
        response: dict = lib.lobby_state()
        if response["ok"] and response["response"]:
            state = response["response"]
            players_str = ""
            for player in state["players"]:
                players_str += f"{player}\n"
            n_players: int = len(state["players"])
            capacity: int = state["capacity"]
            players_to_start = capacity - n_players
            self.query_one("#lobby_status").update(f"The following players are currently waiting in the Lobby:\n{players_str}\n{players_to_start} are still needed for the game to start")
        elif response["ok"] and not response["response"]:
            self.app.push_screen(Game())
        elif not response["ok"]:
            self.app.errror_notifications(response["error"])

class Game(Screen):
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(str())
            yield Button(label="", variant="success", id="first", disabled = False)
            yield Button(label="Add 1", variant="success", id="second", disabled = False)
        with Horizontal():
            yield Label(str())
            yield Button(label="Add 1", variant="success", id="third", disabled = False)
            yield Button(label="Add 1", variant="success", id="forth", disabled = False)

    def on_button_pressed(self, event):
        self.query_one(Label).update(str())
        if event.button.id == "first":
            btn = event.button
            btn.label = "You clicked me"

class TempleOfDoom(App):
    def error_notifications(self, error: str):
        if error == "ConnectionError":
            self.notify("The server is currently unavailable. Please try again or adjust your Server-IP", severity="error")
        elif error == "Timeout":
            self.notify("The connection to the server has timed out.", severity="error")
        else:
            self.notify(error, severity="error")

    def on_mount(self):
        self.push_screen(LobbySelection())

if __name__ == "__main__":
    app = TempleOfDoom()
    app.run()