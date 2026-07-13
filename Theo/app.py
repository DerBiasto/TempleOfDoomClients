from textual.app import App
from screens.start import StartScreen

class TempleOfDoomApp(App):
    CSS_PATH = "temple_of_doom.tcss"
    def on_mount(self):
        self.push_screen(StartScreen())

if __name__ == "__main__":
    TempleOfDoom = TempleOfDoomApp()
    TempleOfDoom.run()
