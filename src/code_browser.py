import sys
import json

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.events import Key
from textual.widgets import DirectoryTree, Footer, Static, Input

sys.path.append("")
import tools

CONFIG = './config.json'

class CodeBrowser(App):
    """Textual code browser app."""

    CSS =  """
    Screen {
    background: $surface-darken-1;
    &:inline {
        height: 50vh;
            }
    }

    #tree-view {
        display: block;
        max-width: 50%;
        scrollbar-gutter: stable;
        overflow: auto;
        width: auto;
        height: 100%;
        dock: left;
    }

    #code-view {
        overflow: auto scroll;
        min-width: 100%;
        hatch: right $primary;   
    }

    #code {
        width: auto;
    }

    #response {
            margin-top: 1;
    }

    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    ALIASES = {"h": "left", "j": "down", "k": "up", "l": "right"}

    def __init__(self):
        with open(CONFIG) as f:
            j = json.load(f)
        self.SYNTAX = j.get("syntax", dict(line_numbers=True,
                                            word_wrap=False,
                                            indent_guides=True,
                                            theme="github-dark")
                            )
        self.PREAMBLE = j.get("preamble", "")
        self.PROMPT = j.get("prompt", "")

        if "key" in j:
            self.CLIENT = tools.client(key=j["key"])
        else:
            raise ValueError("`config.json` does not have an LLM key provided under the top-level `key`.")

        super().__init__()

    async def on_key(self, event: Key) -> None:
        event.key = self.ALIASES.get(event.key, event.key)
        await super().dispatch_key(event)

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = "./" if len(sys.argv) < 2 else sys.argv[1]
        with Container():
            yield Input(placeholder="How can the LLM help analyze this file?", value=self.PROMPT)
            yield DirectoryTree(path, id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
            yield Static(id="response")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    async def on_input_changed(self, message: Input.Changed) -> None:
        self.PROMPT = message.value

    async def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        # Don't propogate the message up the widget tree to the container
        event.stop()

        # Apply syntax
        code: Static = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                **self.SYNTAX
            )
        except Exception:
            code.update(Traceback(theme="github-dark", width=None))
        else:
            code.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)

        # Send file path to the model
        file = event.path.absolute()
        response = await tools.query(self.CLIENT, self.PROMPT, self.PREAMBLE, args={"file": file})
        self.query_one('#response', Static).update(response)

if __name__ == "__main__":
    CodeBrowser().run()
