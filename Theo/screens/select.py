import lib
from textual import on
from textual.widgets import Label, Button, Select, ListView, ListItem
from textual.screen import Screen
from textual.containers import VerticalScroll, Horizontal, Center
from screens.lobby import LobbyScreen

class LobbySelectScreen(Screen):
    def compose(self):
        with Center(): yield Label("Select Lobby")

        self.lobby_selector = ListView(
            *[ListItem(Label(f"{lobby} ({len(players["players"])}/{players["capacity"]})"), id=lobby) for lobby, players in lib.get_lobbies().items()]
        )

        with Center():
            yield VerticalScroll(self.lobby_selector)
        
        with Center():
            yield Horizontal(
                Button(
                    "Join",
                    id="join",
                    variant="success"
                ),
                Button(
                    "Refresh",
                    id="refresh",
                    variant="primary"
                ),
                Button(
                    "Back",
                    id="back", variant="error"
                ))

    @on(ListView.Highlighted)
    def update_join_button(self, event: ListView.Highlighted):
        if event.item and event.item.id:
            self.current_lobby = event.item.id

    @on(Button.Pressed, "#join")
    def join_current_lobby(self):
        lib.join_lobby(self.current_lobby)
        self.app.push_screen(LobbyScreen())

    @on(Button.Pressed, "#refresh")
    def handle_refresh(self):
        pass

    @on(Button.Pressed, "#back")
    def handle_back(self):
        self.app.pop_screen()
