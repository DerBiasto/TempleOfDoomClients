from textual import log, work  # noqa: F401
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import Button, DataTable, Header, Label, Select, Static

import libhttpx


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
        yield Button(label="Create a new lobby", variant="primary", id="new_lobby")
        yield Button(label="Create an example game", variant="primary", id="example_game")
        yield Button(label="Refresh", variant="primary", id="refresh")
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
        self.lobby_refresh_timer = self.set_interval(25, self.update_lobby_list)

    def set_interactibility(self, *, enable: bool):
        if enable:
            for button in self.query(Button):
                button.disabled = False
                self.query_one(DataTable).can_focus = True
        else:
            for button in self.query(Button):
                button.disabled = True
                self.query_one(DataTable).can_focus = False
        
    @work(exclusive=True)
    async def update_lobby_list(self):
        response = await libhttpx.list_lobbies()
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
                rows.append((lobby_name, player_str, f"{len(lobby_data['players'])}/{lobby_data['capacity']}"))
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
            self.set_interactibility(enable=True)

    @work(exclusive=True)
    async def lobby_creation(self, capacity):
        response = await libhttpx.create_lobby(capacity)
        log(f"This was the response from lobby_creation(): {response}")
        if response["ok"]:
            self.app.push_screen(Waiting())
        else:
            self.app.error_notifications(response["error"])
        self.set_interactibility(enable=True)

    @work(exclusive=True)
    async def example_game_creation(self, capacity):
        response = await libhttpx.create_example_game(capacity)
        if response["ok"]:
            self.app.push_screen(Game())
        else:
            self.app.error_notifications(response["error"])
        self.set_interactibility(enable=True)

    @work(exclusive=True)
    async def joining_lobby(self, lobby_name):
        response = await libhttpx.join_lobby(lobby_name)
        log("in function joining_lobby")
        if response["ok"]:
            self.app.push_screen(Waiting())
        else:
            if response["error"] == "HTTPError":
                self.notify("The selected lobby isn't available anymore. Please reload your lobby list.", severity="error")
            else:
                self.app.error_notifications(response["error"])
        self.set_interactibility(enable=True)
    
    def on_button_pressed(self, event: Button.Pressed):
        self.set_interactibility(enable=False)
        selected_capacity = self.query_one("#player_select").value
        if event.button.id == "new_lobby":
            self.lobby_creation(selected_capacity)
        elif event.button.id == "example_game":
            self.example_game_creation(selected_capacity)
        elif event.button.id == "refresh":
            self.update_lobby_list()
            self.set_interactibility(enable=True)
        else:
            self.set_interactibility(enable=True)

    def on_data_table_row_selected(self, event):
        self.set_interactibility(enable=False)
        selected_lobby = event.row_key.value
        self.joining_lobby(selected_lobby)

    def _on_screen_suspend(self):
        self.lobby_refresh_timer.pause()

    def _on_screen_resume(self):
        self.lobby_refresh_timer.resume()

class Waiting(Screen):
    def compose(self) -> ComposeResult:
        yield Label("", id="lobby_status")
        yield Label("", id="player_list")
        yield Button(label="Leave Lobby", variant="warning", id="leave_lobby")
    
    def on_mount(self):
        self.update_lobby_status()
        self.set_interval(10, self.update_lobby_status)

    def on_button_pressed(self, event: Button.Pressed):
        event.button.disabled = True
        if event.button.id == "leave_lobby":
            self.leave_lobby()
        else:
            event.button.disabled = False
    
    @work(group="lobby_updates", exclusive=True)
    async def update_lobby_status(self):
        response: dict = await libhttpx.lobby_state()
        if response["ok"] and response["response"]:
            state = response["response"]
            players_str = ""
            #for player in state["players"]:
            #    players_str += f"{player}\n"
            
            n_players: int = len(state["players"])
            capacity: int = state["capacity"]
            players_to_start = capacity - n_players
            self.query_one("#lobby_status").update(f"The following players are currently waiting in the Lobby:\n{players_str}\n{players_to_start} are still needed for the game to start")
        elif response["ok"] and not response["response"]:
            log("Response was ok and empty")
            self.app.switch_screen(Game())
        elif not response["ok"]:
            log("Response was not ok")
            self.app.error_notifications(response["error"])

    @work(exclusive=True)
    async def leave_lobby(self):
        self.workers.cancel_group(self, "lobby_updates")
        response = await libhttpx.leave_lobby()
        log(f"This was the response from leave_lobby(): {response}")
        if response["ok"]:
            self.app.pop_screen()
        else:
            log("Couldnt leave lobby")
            self.app.error_notifications(response["error"])
        self.query_one("#leave_lobby").disabled = False


class Game(Screen):

    CSS_PATH = "game.tcss"

    #game_initializied = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("Your Role:", id="role"),
            Static("Round:", id="round"),
            Static("Game Phase:", id="game_phase"),
            Static("Treasures", id="treasures"),
            Static("Traps", id="traps"),
            id="game_stats"
            )
        yield Vertical(id="player_container")

    def on_mount(self):
        self.initialize_game_state()
        self.display_role()
        self.setup_player_display()
        #self.initialize_game_state_update()
        #self.set_interval(5, self.initialize_game_state_update())

    def on_button_pressed(self, event):
        pass

    @work
    async def initialize_game_state(self):
        response = await libhttpx.get_players()
        log("Reached initialize_game_state,")
        if response["ok"]:
            players = response["response"]
            self.game_state = libhttpx.GameState(players)
            log(f"The current round is {self.game_state.number_moves}")
            self.update_game_state()
            self.set_interval(3, self.update_game_state)
            #self.game_initializied = True
        else:
            self.app.error_notifications(response["error"])
            #add logic to try again later

    @work
    async def display_role(self):
        response = await libhttpx.get_role()
        if response["ok"]:
            role = response["response"]
            self.query_one("#role").update(f"Your Role: {role}")
        else:
            self.app.error_notifications(response["error"])
            #add logic to try again later
    
    @work
    async def update_game_state(self):
        log("Reached initialize update")
        response = await libhttpx.get_state(starting=self.game_state.number_moves)
        if response["ok"]:
            new_moves = response["response"]
            for move in new_moves:
                self.game_state.update(move)
            #self.app.sub_title = f"Round: {self.game_state.current_round}            {self.game_state.treasures}/{self.game_state.required_treasures} Treasures    {self.game_state.traps}/{self.game_state.required_traps} Traps"
            self.query_one("#round").update(f"Round: {self.game_state.current_round}")
            self.query_one("#game_phase").update(f"Game Phase: {self.game_state.game_phase}")
            self.query_one("#treasures").update(f"{self.game_state.treasures}/{self.game_state.required_treasures} Treasures")
            self.query_one("#traps").update(f"{self.game_state.traps}/{self.game_state.required_traps} Traps")
        else:
            self.app.error_notifications(response["error"])

    @work
    async def setup_player_display(self):
        response = await libhttpx.get_players()
        if response["ok"]:
            players = response["response"]
            player_container = self.query_one("#player_container")
            for player in players:
                player_container.mount(Horizontal(Static(f"{player}:", id="player"), id=player))
                if player == libhttpx.get_username():
                    player_container.query_one(f"#{player}").styles.border = ("solid", "blue")
        else:
            self.app.error_notifications()


turquoise_greenery= Theme(
	name="turquoise_greenery",
	primary="#CFD7D7FF",
	secondary="#00F5FFFF",
	accent="#FB2C00FF",
	background="#121212FF",
	foreground="#EDEDEDFF",
	surface="#1E1E1EFF",
	panel="#005F64FF",
	success="#00AF84FF",
	warning="#362321FF",
	error="#00FEFFFF",
	dark=True,
	variables={},
)

turquoise_ocean_theme = Theme(
    name="turquoise_ocean_theme",
    primary="#1BCFCFFF",       # bright turquoise
    secondary="#0AA7B8FF",     # deeper teal for contrast
    accent="#FF7A4BFF",        # warm coral accent for balance
    background="#0D1A1CFF",    # deep ocean blue-black
    foreground="#E8FDFEFF",    # soft near-white with a cool tint
    surface="#142628FF",       # slightly lighter than background
    panel="#0E4F55FF",         # muted teal panel
    success="#1ED8A0FF",       # minty success green
    warning="#4A3A1FFF",       # earthy warning brown
    error="#00C7D9FF",         # sharp cyan error (fits turquoise theme)
    dark=True,
    variables={}
)

pulse_inspired_theme = Theme(
    name="pulse_inspired_theme",
    primary="#00E0FFFF",       # bright electric cyan glow
    secondary="#0098AFFF",     # deeper teal for structure
    accent="#FF3D7FFF",        # neon magenta accent (Pulse uses neon contrast)
    background="#0A0F14FF",    # deep slate/ink background
    foreground="#E8F9FFFF",    # cool white with slight cyan tint
    surface="#111A22FF",       # elevated dark surface
    panel="#0F3C47FF",         # muted teal panel
    success="#00D9A0FF",       # glowing mint success
    warning="#4A3A20FF",       # warm amber warning
    error="#00B7CFFF",         # sharp cyan error (fits Pulse aesthetic)
    dark=True,
    variables={}
)


class TempleOfDoom(App):
    def error_notifications(self, error: str):
        if error == "ConnectionError":
            self.notify("The server is currently unavailable. Please try again or adjust your Server-IP", severity="error")
        elif error == "Timeout":
            self.notify("The connection to the server has timed out.", severity="error")
        else:
            self.notify(error, severity="error")

    def on_mount(self):
        self.register_theme(turquoise_greenery)
        self.register_theme(turquoise_ocean_theme)
        self.register_theme(pulse_inspired_theme)
        self.theme = "pulse_inspired_theme"
        self.push_screen(LobbySelection())

if __name__ == "__main__":
    app = TempleOfDoom()
    app.run()