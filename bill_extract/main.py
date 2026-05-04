"""Bill extraction CLI tool."""

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer(name="bill-extract")
console = Console()


@app.command()
def main():
    """Extract information from bills and invoices."""
    console.print("[bold green]Bill Extractor CLI[/bold green]")
    console.print("Extract data from your bills and invoices with ease.")


if __name__ == "__main__":
    app()