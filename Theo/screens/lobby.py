import lib
from textual.screen import Screen
from textual.widgets import Label, Button
from textual.containers import Center
from screens.role import RoleScreen


class LobbyScreen(Screen):
    lobby = None

    def compose(self):
        self.status = Label("", id="lobby_status")
        with Center():
            yield Label("LobbyScreen")
        with Center():
            yield self.status
        with Center():
            yield Button("Leave", id="leave", variant="error")

    def on_mount(self):
        self.set_interval(1, self.update_lobby_status)

    def on_button_pressed(self, event: Button.Pressed):
        lib.leave_lobby()
        self.app.pop_screen()

    def update_lobby_status(self):
        try:
            lobby = lib.LobbyState()
            lobby.update()
            self.status.update(f"{lobby.game}: {lobby.players}, ({len(lobby.players)}/{lobby.capacity})")
        except:
            self.app.push_screen(RoleScreen())
