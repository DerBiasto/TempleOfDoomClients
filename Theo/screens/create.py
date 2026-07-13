import lib
from textual import on
from textual.screen import Screen
from textual.widgets import Button, Label, Input, Pretty
from textual.containers import Center, Horizontal
from textual.validation import Number, ValidationResult, Validator
from screens.role import RoleScreen
from screens.lobby import LobbyScreen

class LobbyCreateScreen(Screen):
    def compose(self):
        with Center():
            yield Label("Create Lobby")
        with Center():
            yield Label("How many Players?")
        with Center():
            yield Input(
                placeholder="Enter a number between 3 and 10...",
                validators=[
                    Number(minimum=3, maximum=10),
                ],
                id="capacity"
            )
        with Center():
            yield Pretty([])
        with Center():
            yield Horizontal(
                Button(
                    "Create",
                    id="create",
                    variant="success"
                ),
                Button(
                    "Back",
                    id="back",
                    variant="error"
                ),
                Button(
                    "Create Example Game",
                    id="example",
                    variant="primary"
                )
            )

    def on_mount(self):
        self.current_value = ""

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        if not event.validation_result.is_valid:
            self.query_one(Pretty).update(event.validation_result.failure_descriptions)
        else:
            self.query_one(Pretty).update([])
            self.current_value = event.input.value

    def on_input_submitted(self, event: Input.Submitted):
        lib.create_lobby(event.input.value)
        self.app.push_screen(LobbyScreen())

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create":
            lib.create_lobby(self.current_value)
            self.app.push_screen(LobbyScreen())
        elif event.button.id == "back":
            self.app.pop_screen()
        else:
            lib.create_example_game(self.current_value)
            self.app.push_screen(RoleScreen())
