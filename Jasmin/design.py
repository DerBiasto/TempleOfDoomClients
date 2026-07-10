from textual.screen import Screen
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Digits, Static
from textual.containers import HorizontalGroup, Center, CenterMiddle
from library import create_example_game, get_lobby, new_lobby, get_cards, get_role


        
class StartScreen(App):
    def compose(self):

        with CenterMiddle():
            yield Button("Create example game", id="Example")
            yield Button("Show Lobbys", id="Show")
            yield Button("Create Lobby", id="Create")

    @on(Button.Pressed)
    def on_button_pressed(self, event):
        if event.button.id == "Example":
            create_example_game()
        if event.button.id == "Show":
            get_lobby()
        if event.button.id == "Create":
            new_lobby()


class GameScreen(Screen):
    get_cards()
    get_role()
    




if __name__ == "__main__":
    StartScreen().run()