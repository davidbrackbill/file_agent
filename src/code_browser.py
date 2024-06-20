import sys

from rich.syntax import Syntax
from rich.traceback import Traceback

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.reactive import var
from textual.events import Key
from textual.widgets import DirectoryTree, Footer, Header, Static


class CodeBrowser(App):
    """Textual code browser app."""

    CSS_PATH = "code_browser.tcss"
    BINDINGS = [
        ("f", "toggle_files", "Toggle Files"),
        (".", "toggle_hidden", "Toggle Hidden"),
        ("q", "quit", "Quit"),
    ]
    ALIASES = {"h": "left", "j": "down", "k": "up", "l": "right"}

    show_tree = var(True)
    show_hidden = var(True)

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when the `show_tree` var is modified."""
        self.set_class(show_tree, "-show-tree")

    def action_toggle_files(self) -> None:
        self.show_tree = not self.show_tree

    def action_toggle_hidden(self) -> None:
        self.show_hidden = not self.show_hidden

    async def on_key(self, event: Key) -> None:
        event.key = self.ALIASES.get(event.key, event.key)
        await super().dispatch_key(event)

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        path = "./" if len(sys.argv) < 2 else sys.argv[1]
        with Container():
            yield DirectoryTree(path, id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DirectoryTree).focus()

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#code", Static)
        try:
            syntax = Syntax.from_path(
                str(event.path),
                line_numbers=True,
                word_wrap=False,
                indent_guides=True,
                theme="github-dark",
            )
        except Exception:
            code_view.update(Traceback(theme="github-dark", width=None))
            self.sub_title = "ERROR"
        else:
            code_view.update(syntax)
            self.query_one("#code-view").scroll_home(animate=False)
            self.sub_title = str(event.path)


if __name__ == "__main__":
    CodeBrowser().run()
