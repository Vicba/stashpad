"""Textual split-pane browser for vault entries."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import App
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key, Resize
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, ListItem, ListView, Static

from stashpad.clipboard import copy_to_clipboard
from stashpad.constants import DEFAULT_PICK_LIMIT
from stashpad.entry_actions import (
    execute_entry_command,
    get_clipboard_text,
    get_entry_body_text,
    open_entry_in_browser,
    resolve_entry_kind,
)
from stashpad.entry_query import format_entry_label
from stashpad.exceptions import EntryNotFoundError, ValidationError
from stashpad.models import Entry, EntryKind
from stashpad.output import entry_preview_renderable
from stashpad.tui.browse_tags import (
    ALL_TAGS,
    UNTAGGED_FILTER,
    TagFilterOption,
    build_tag_filter_options,
    entries_for_tag_filters,
    initial_selected_tags,
    load_entries_for_browse_context,
)

if TYPE_CHECKING:
    from uuid import UUID

    from textual.widget import Widget

    from stashpad.storage import VaultStorage

BROWSE_CSS = """
BrowseApp {
    background: $surface;
}

#main_layout {
    layout: horizontal;
    height: 1fr;
}

#browse_column {
    width: 1fr;
    min-width: 32;
    height: 1fr;
    border: solid $primary;
    padding: 0 1;
}

#tag_section {
    height: auto;
    max-height: 12;
    margin-bottom: 1;
}

#tag_heading {
    color: $text-muted;
}

#tag_hint {
    color: $text-muted;
    margin-bottom: 1;
}

#tag_list {
    height: auto;
    min-height: 3;
    max-height: 8;
    border: solid $primary-darken-1;
}

#search_input {
    margin-bottom: 1;
}

#entry_list {
    height: 1fr;
}

#preview_pane {
    width: 1fr;
    min-width: 28;
    height: 1fr;
    border: solid $primary;
    padding: 0 1;
}

#preview {
    height: 1fr;
    overflow-y: auto;
}

.empty_preview {
    color: $text-muted;
    padding: 1 0;
}

BrowseApp.-narrow #main_layout {
    layout: vertical;
}

BrowseApp.-narrow #preview_pane {
    height: 40%;
    min-height: 8;
}
"""


@dataclass(frozen=True)
class BrowseOptions:
    """Filter and action options shared by the browse TUI."""

    query: str = ""
    tags: list[str] | None = None
    pinned: bool = False
    kind: EntryKind | None = None
    limit: int = DEFAULT_PICK_LIMIT
    exact: bool = False
    force: bool = False
    first_line_only: bool = False


class TagFilterItem(ListItem):
    """Sidebar row for a toggleable tag filter."""

    def __init__(self, option: TagFilterOption, *, selected: bool) -> None:
        self.option = option
        self.selected = selected
        super().__init__(Label(self._label_text()))

    def _label_text(self) -> str:
        from stashpad.tui.browse_tags import format_tag_filter_label

        return format_tag_filter_label(
            self.option.label,
            self.option.entry_count,
            selected=self.selected,
        )

    def set_selected(self, selected: bool) -> None:
        """Update the checkbox marker on this row."""
        self.selected = selected
        self.query_one(Label).update(self._label_text())


class EntryListItem(ListItem):
    """List row that carries the backing vault entry."""

    def __init__(self, entry: Entry) -> None:
        super().__init__(Label(format_entry_label(entry)))
        self.entry = entry


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Ask the user to confirm deleting a vault entry."""

    DEFAULT_CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }

    #confirm_dialog {
        width: 80%;
        max-width: 80;
        height: auto;
        border: thick $error;
        background: $panel;
        padding: 1 2;
    }

    #confirm_target {
        margin: 1 0;
    }
    """

    def __init__(self, entry_title: str) -> None:
        super().__init__()
        self.entry_title = entry_title

    def compose(self) -> Iterator[Widget]:
        yield Vertical(
            Static("Delete this entry?", id="confirm_title"),
            Static(self.entry_title, id="confirm_target"),
            Static("[bold]y[/bold] confirm  [bold]n[/bold] cancel", id="confirm_help"),
            id="confirm_dialog",
        )

    def on_key(self, event: Key) -> None:
        if event.key in {"y", "enter"}:
            self.dismiss(True)
        elif event.key in {"n", "escape"}:
            self.dismiss(False)


class ConfirmRunScreen(ModalScreen[bool]):
    """Ask the user to confirm running a shell command."""

    DEFAULT_CSS = """
    ConfirmRunScreen {
        align: center middle;
    }

    #confirm_dialog {
        width: 80%;
        max-width: 80;
        height: auto;
        border: thick $error;
        background: $panel;
        padding: 1 2;
    }

    #confirm_command {
        margin: 1 0;
    }
    """

    def __init__(self, command: str) -> None:
        super().__init__()
        self.command = command

    def compose(self) -> Iterator[Widget]:
        yield Vertical(
            Static("Run this command?", id="confirm_title"),
            Static(self.command, id="confirm_command"),
            Static("[bold]y[/bold] confirm  [bold]n[/bold] cancel", id="confirm_help"),
            id="confirm_dialog",
        )

    def on_key(self, event: Key) -> None:
        if event.key in {"y", "enter"}:
            self.dismiss(True)
        elif event.key in {"n", "escape"}:
            self.dismiss(False)


class BrowseApp(App[None]):
    """Split-pane vault browser with multi-select tag filters, list, and preview."""

    CSS = BROWSE_CSS
    TITLE = "Stash Browse"
    BINDINGS = [
        Binding("c", "copy_entry", "Copy"),
        Binding("o", "open_entry", "Open"),
        Binding("r", "run_entry", "Run"),
        Binding("d", "delete_entry", "Delete"),
        Binding("q", "quit", "Quit"),
        Binding("t", "focus_tags", "Tags", show=False),
        Binding("l", "focus_entries", "Entries", show=False),
        Binding("/", "focus_search", "Search", show=False),
        Binding("space", "toggle_tag_filter", "Toggle tag", show=False),
    ]

    def __init__(self, storage: VaultStorage, options: BrowseOptions) -> None:
        super().__init__()
        self.storage = storage
        self.options = options
        self._entries_by_id: dict[UUID, Entry] = {}
        self._context_entries: list[Entry] = []
        self._selected_tags = initial_selected_tags(options.tags)
        self._untagged_only = False
        self._search_query = options.query

    def compose(self) -> Iterator[Widget]:
        yield Horizontal(
            Vertical(
                Vertical(
                    Static("Tag filters", id="tag_heading"),
                    Static("t focus · Space/Enter toggle", id="tag_hint"),
                    ListView(id="tag_list"),
                    id="tag_section",
                ),
                Input(
                    placeholder="Search entries…",
                    id="search_input",
                    value=self.options.query,
                ),
                ListView(id="entry_list"),
                id="browse_column",
            ),
            Vertical(
                Static(
                    "Select an entry to preview.",
                    id="preview",
                    classes="empty_preview",
                ),
                id="preview_pane",
            ),
            id="main_layout",
        )
        yield Footer()

    def on_mount(self) -> None:
        self._reload_context()
        self._reload_tag_filters()
        self._reload_entries(self._search_query)
        self._apply_responsive_layout(self.size.width)
        self.query_one("#entry_list", ListView).focus()

    @on(Resize)
    def on_resize(self, event: Resize) -> None:
        """Stack panes vertically on narrow terminals."""
        self._apply_responsive_layout(event.size.width)

    def _apply_responsive_layout(self, width: int) -> None:
        """Stack preview below the browse column on narrow terminals."""
        main_layout = self.query_one("#main_layout", Horizontal)
        preview_pane = self.query_one("#preview_pane", Vertical)
        narrow = width < 80
        self.set_class(narrow, "-narrow")
        main_layout.styles.layout = "vertical" if narrow else "horizontal"
        preview_pane.styles.height = "40%" if narrow else "1fr"

    def _reload_context(self) -> None:
        """Reload the entry pool used for folders and list filtering."""
        self._context_entries = load_entries_for_browse_context(
            self.storage,
            base_tags=self.options.tags,
            pinned=self.options.pinned,
            kind=self.options.kind,
            limit=self.options.limit,
        )

    def _reload_tag_filters(self) -> None:
        """Rebuild the tag filter sidebar from the current entry pool."""
        tag_list = self.query_one("#tag_list", ListView)
        tag_list.remove_children()
        for option in build_tag_filter_options(self._context_entries):
            selected = self._is_tag_option_selected(option.option_id)
            tag_list.append(TagFilterItem(option, selected=selected))

    def _is_tag_option_selected(self, option_id: str) -> bool:
        """Return whether a sidebar row should show the active marker."""
        if option_id == ALL_TAGS:
            return not self._selected_tags and not self._untagged_only
        if option_id == UNTAGGED_FILTER:
            return self._untagged_only
        return option_id in self._selected_tags

    def _sync_tag_filter_labels(self) -> None:
        """Refresh checkbox markers without rebuilding the tag list."""
        tag_list = self.query_one("#tag_list", ListView)
        for child in tag_list.children:
            if isinstance(child, TagFilterItem):
                child.set_selected(self._is_tag_option_selected(child.option.option_id))

    def _toggle_tag_filter_item(self, item: TagFilterItem) -> None:
        """Toggle one tag filter and refresh the entry list."""
        option_id = item.option.option_id
        if option_id == ALL_TAGS:
            self._selected_tags.clear()
            self._untagged_only = False
        elif option_id == UNTAGGED_FILTER:
            self._untagged_only = not self._untagged_only
            if self._untagged_only:
                self._selected_tags.clear()
        elif option_id in self._selected_tags:
            self._selected_tags.remove(option_id)
        else:
            self._untagged_only = False
            self._selected_tags.add(option_id)

        self._sync_tag_filter_labels()
        self._reload_entries(self._search_query)

    def _reload_entries(self, query: str) -> None:
        """Filter entries for the active tag selection and repopulate the list."""
        self._search_query = query
        entries = entries_for_tag_filters(
            self._context_entries,
            self._selected_tags,
            untagged_only=self._untagged_only,
            query=query,
            limit=self.options.limit,
            exact=self.options.exact,
        )
        self._entries_by_id = {entry.id: entry for entry in entries}

        entry_list = self.query_one("#entry_list", ListView)
        entry_list.remove_children()
        for entry in entries:
            entry_list.append(EntryListItem(entry))

        preview = self.query_one("#preview", Static)
        if not entries:
            preview.update("No entries match the active tag filters.")
            preview.add_class("empty_preview")
            return

        entry_list.index = 0
        self._show_entry(entries[0])

    def _selected_entry(self) -> Entry | None:
        """Return the currently highlighted entry, if any."""
        entry_list = self.query_one("#entry_list", ListView)
        highlighted = entry_list.highlighted_child
        if isinstance(highlighted, EntryListItem):
            return highlighted.entry
        return None

    def _show_entry(self, entry: Entry) -> None:
        """Update the preview pane and bump ``opened_at`` for the entry."""
        if entry.id not in self._entries_by_id:
            return
        try:
            touched = self.storage.touch_entry(entry.id)
        except EntryNotFoundError:
            return
        self._entries_by_id[entry.id] = touched
        preview = self.query_one("#preview", Static)
        preview.remove_class("empty_preview")
        preview.update(entry_preview_renderable(touched))

    @on(ListView.Highlighted, "#entry_list")
    def on_entry_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if isinstance(item, EntryListItem):
            self._show_entry(item.entry)

    @on(ListView.Selected, "#tag_list")
    def on_tag_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, TagFilterItem):
            self._toggle_tag_filter_item(item)

    @on(Input.Changed, "#search_input")
    def on_search_changed(self, event: Input.Changed) -> None:
        self._reload_entries(event.value)

    def action_toggle_tag_filter(self) -> None:
        tag_list = self.query_one("#tag_list", ListView)
        if not tag_list.has_focus:
            return
        highlighted = tag_list.highlighted_child
        if isinstance(highlighted, TagFilterItem):
            self._toggle_tag_filter_item(highlighted)

    def action_focus_tags(self) -> None:
        self.query_one("#tag_list", ListView).focus()

    def action_focus_entries(self) -> None:
        self.query_one("#entry_list", ListView).focus()

    def action_focus_search(self) -> None:
        self.query_one("#search_input", Input).focus()

    def action_copy_entry(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.notify("No entry selected", severity="warning")
            return
        try:
            text = get_clipboard_text(entry, first_line_only=self.options.first_line_only)
            copy_to_clipboard(text)
        except ValidationError as exc:
            self.notify(exc.message, severity="error")
            return
        self.notify(f"Copied from '{entry.title}'")

    def action_open_entry(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.notify("No entry selected", severity="warning")
            return
        try:
            opened = open_entry_in_browser(entry)
        except ValidationError as exc:
            self.notify(exc.message, severity="error")
            return
        self.notify(f"Opened {opened}")

    def action_run_entry(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.notify("No entry selected", severity="warning")
            return
        if resolve_entry_kind(entry) != EntryKind.COMMAND:
            self.notify("Only command entries can be run", severity="warning")
            return

        command = get_entry_body_text(entry, first_line_only=self.options.first_line_only)
        if not command:
            self.notify("Entry has no command text", severity="error")
            return

        if self.options.force:
            self._run_command(entry)
            return

        self.push_screen(ConfirmRunScreen(command), self._handle_run_confirmation)

    def action_delete_entry(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.notify("No entry selected", severity="warning")
            return
        self.push_screen(ConfirmDeleteScreen(entry.title), self._handle_delete_confirmation)

    def _handle_delete_confirmation(self, confirmed: bool) -> None:
        if not confirmed:
            self.notify("Delete cancelled")
            return
        entry = self._selected_entry()
        if entry is None:
            return
        removed = self.storage.remove_entries([entry.id])
        if removed != 1:
            self.notify("Entry could not be deleted", severity="error")
            return
        self.notify(f"Deleted '{entry.title}'")
        self._reload_context()
        self._reload_tag_filters()
        self._reload_entries(self._search_query)

    def _handle_run_confirmation(self, confirmed: bool) -> None:
        if not confirmed:
            self.notify("Run cancelled")
            return
        entry = self._selected_entry()
        if entry is not None:
            self._run_command(entry)

    @work(thread=True)
    def _run_command(self, entry: Entry) -> None:
        """Execute the command in a worker thread so the UI stays responsive."""
        try:
            exit_code = execute_entry_command(
                entry,
                first_line_only=self.options.first_line_only,
                force=True,
            )
        except ValidationError as exc:
            self.call_from_thread(self.notify, exc.message, severity="error")
            return

        if exit_code == 0:
            self.call_from_thread(self.notify, f"Command finished (exit {exit_code})")
        else:
            self.call_from_thread(
                self.notify,
                f"Command exited with code {exit_code}",
                severity="warning",
            )


def run_browse_app(storage: VaultStorage, options: BrowseOptions) -> None:
    """Launch the browse TUI against *storage*.

    Parameters
    ----------
    storage : VaultStorage
        Active vault (respects ``--config-dir`` from the CLI).
    options : BrowseOptions
        Filters and action flags for the session.
    """
    BrowseApp(storage, options).run()
