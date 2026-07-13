from textual.widgets import Button, Label
from textual.containers import Vertical, Center
from textual.screen import Screen
from screens.select import LobbySelectScreen
from screens.create import LobbyCreateScreen

class StartScreen(Screen):
    def compose(self):
        with Center():
            yield Label(r"""
___________                   .__           ________   _____  ________                         
\__    ___/___   _____ ______ |  |   ____   \_____  \_/ ____\ \______ \   ____   ____   _____  
  |    |_/ __ \ /     \\____ \|  | _/ __ \   /   |   \   __\   |    |  \ /  _ \ /  _ \ /     \ 
  |    |\  ___/|  Y Y  \  |_> >  |_\  ___/  /    |    \  |     |    `   (  <_> |  <_> )  Y Y  \
  |____| \___  >__|_|  /   __/|____/\___  > \_______  /__|    /_______  /\____/ \____/|__|_|  /
             \/      \/|__|             \/          \/                \/                    \/ 
""")
        with Center():
            yield Vertical(
                Button("Join Lobby", id="join", variant="success"),
                Button("Create Lobby", id="create", variant="primary"),
                Button("Quit", id="quit", variant="error")
            )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "join":
            self.app.push_screen(LobbySelectScreen())
        elif event.button.id == "create":
            self.app.push_screen(LobbyCreateScreen())
        else:
            self.app.exit()


if __name__ == "__main__":
    game = GameApp()
    game.run()
