#! /usr/bin/env python3

# https://blog.stephane-robert.info/docs/developper/programmation/python/textual/

"""Moniteur de services — application Textual complète."""
import asyncio
from datetime import datetime

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
)

SERVICES = [
    ("nginx", 80, "running"),
    ("postgresql", 5432, "running"),
    ("redis", 6379, "running"),
    ("prometheus", 9090, "stopped"),
    ("grafana", 3000, "running"),
    ("alertmanager", 9093, "stopped"),
]


class ConfirmRestart(Screen[bool]):
    """Écran de confirmation de redémarrage."""

    CSS = """
    ConfirmRestart { align: center middle; }
    #dialog {
        width: 50;
        height: 11;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    #question {
        width: 100%;
        content-align: center middle;
        margin: 1 0;
    }
    .dialog-buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }
    Button { margin: 0 2; }
    """

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(
                f"Redémarrer [bold]{self.service_name}[/bold] ?",
                id="question",
            )
            with Horizontal(classes="dialog-buttons"):
                yield Button("Confirmer", id="yes", variant="success")
                yield Button("Annuler", id="no", variant="error")

    @on(Button.Pressed, "#yes")
    def confirm(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def cancel(self) -> None:
        self.dismiss(False)


class ServiceMonitor(App):
    """Moniteur de services."""

    TITLE = "Service Monitor"

    CSS = """
    #sidebar {
        width: 25;
        background: $panel;
        padding: 1 2;
        border-right: tall $primary;
        text-style: bold;
    }
    #sidebar:hover {
        background: $primary 20%;
    }
    #sidebar:light {
        background: #e8e8f0;
        color: #333333;
    }
    #main {
        width: 1fr;
    }
    Input {
        margin: 0 0 1 0;
    }
    DataTable {
        height: 1fr;
    }
    #alerts {
        height: auto;
        max-height: 8;
        background: $surface;
        border: solid $warning;
        border-title-color: $warning;
        border-title-style: bold;
        padding: 1 2;
        margin: 1 0 0 0;
    }
    #alerts:hover {
        tint: $warning 10%;
    }
    #status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 2;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("d", "toggle_dark", "Thème"),
        ("r", "refresh", "Rafraîchir"),
    ]

    last_update: reactive[str] = reactive("")
    service_count: reactive[int] = reactive(0)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield Static(
                "[bold]Navigation[/]\n\n"
                "• Services\n• [blink]Alertes[/blink]\n• Logs",
                id="sidebar",
            )
            with Vertical(id="main"):
                yield Input(placeholder="Filtrer les services...", id="filter")
                yield DataTable()
                alerts = Static(
                    "[red bold]CRIT[/] disk 94% on node-2\n"
                    "[yellow]WARN[/] memory pressure node-1\n"
                    "[green]OK[/]   backup completed",
                    id="alerts",
                )
                alerts.border_title = "Alertes système"
                yield alerts
        yield Static(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Service", "Port", "Status")
        self.load_services()

    def load_services(self, filtre: str = "") -> None:
        table = self.query_one(DataTable)
        table.clear()
        count = 0
        for name, port, status in SERVICES:
            if filtre and filtre.lower() not in name.lower():
                continue
            marker = (
                "[green]● running[/]" if status == "running"
                else "[red]● stopped[/]"
            )
            table.add_row(name, str(port), marker)
            count += 1
        self.service_count = count
        self.last_update = datetime.now().strftime("%H:%M:%S")

    def watch_last_update(self, value: str) -> None:
        if value:
            self.query_one("#status-bar", Static).update(
                f"Services : {self.service_count} | Mis à jour : {value}"
            )

    def on_input_changed(self, event: Input.Changed) -> None:
        self.load_services(filtre=event.value)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row = event.data_table.get_row(event.row_key)
        service_name = str(row[0])
        self.push_screen(
            ConfirmRestart(service_name), callback=self.handle_restart
        )

    def handle_restart(self, confirmed: bool) -> None:
        if confirmed:
            self.notify("Service redémarré !", severity="information")
        else:
            self.notify("Redémarrage annulé.", severity="warning")

    @work(exclusive=True)
    async def refresh_services(self) -> None:
        """Rafraîchit les services en arrière-plan."""
        self.query_one("#status-bar", Static).update("Rafraîchissement...")
        await asyncio.sleep(1)
        filtre = self.query_one(Input).value
        self.load_services(filtre=filtre)
        self.notify("Services rafraîchis !")

    def action_refresh(self) -> None:
        self.refresh_services()


if __name__ == "__main__":
    ServiceMonitor().run()