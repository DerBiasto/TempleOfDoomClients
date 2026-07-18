from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Label, Digits

class MyApp(App):
    x = 12
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(str(self.x))
            yield Button(label="Add 1", variant="success", id="first", disabled = False)
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
        
app = MyApp()
app.run()