import lib
from textual.screen import Screen
from textual.widgets import Label, Button, Static
from textual.containers import Center, Horizontal

class GameScreen(Screen):
    def compose(self):
        self.game = lib.GameState()
        with Center():
            yield Label("Your Cards")
        with Center():
            yield Horizontal(Label(card) for card in self.game.cards)

    def on_mount(self):
        self.set_interval(1, self.game.update())
