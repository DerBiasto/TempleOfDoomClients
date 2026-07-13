import lib
from textual.widgets import Label, Button
from textual.containers import Center, Horizontal
from textual.screen import Screen
from textual.widgets import Label, Button, Static
from screens.game import GameScreen

class RoleScreen(Screen):

    def compose(self):
        self.game = lib.GameState()
        with Center():
            yield Label("Your role is:")
        with Center():
            yield Label(self.game.role + ("🤠" if self.game.role == "Adventurer" else "🛡️"))
        if self.game.role == "Adventurer":
            with Center():
                yield Static("Your goal is to find all the treasures by communicating with your fellow adventurers. But beware: there are guardians trying to lead you into firey traps by using fake announcements, so trust nobody.", id="role_description")
        else:
            with Center():
                yield Static("Your goal is to lure the adventurers into traps by announcing false information", id="role-description")

        with Center():
            yield Label("These are your cards:")

        with Center():
            yield Cards()

        with Center():
            yield Button("OK")

    def update_game(self):
        self.game.update()

    def on_mount(self):
        self.set_interval(1, self.update_game())

    def on_button_pressed(self, event: Button.Pressed):
        self.app.pop_screen()
        self.app.push_screen(GameScreen())

class Cards(Horizontal):
    def compose(self):
        self.game = lib.GameState()
        for card in self.game.cards:
            yield Static(card, classes=f"card {card}")
