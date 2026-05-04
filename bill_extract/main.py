"""Bill extraction CLI tool."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from bill_extract.logging import setup_logging, get_logger

try:
    from bill_extract.preprocess import preprocessing_pipeline
    PREPROCESS_AVAILABLE = True
except ImportError:
    PREPROCESS_AVAILABLE = False
    preprocessing_pipeline = None

from bill_extract.extractor import BillExtractor, ExtractedBill
from bill_extract.ocr import OCREngine, FIRST_LOAD as OCR_FIRST_LOAD

app = typer.Typer(name="bill-extract")
console = Console()

logger = get_logger("bill_extract")

InputArg = Annotated[Optional[str], typer.Option("--input", "-i", help="Input file or folder path")]
OutputArg = Annotated[Optional[str], typer.Option("--output", "-o", help="Output directory (default: stdout)")]
LangArg = Annotated[str, typer.Option("--lang", "-l", help="OCR language")]
PreprocessArg = Annotated[bool, typer.Option("--preprocess", "-p", help="Enable image preprocessing")]
VerboseArg = Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")]
DebugArg = Annotated[bool, typer.Option("--debug", "-d", help="Enable debug output")]


@app.command()
def main(
    input: InputArg = None,
    output: OutputArg = None,
    lang: LangArg = "fr",
    preprocess: PreprocessArg = False,
    verbose: VerboseArg = False,
    debug: DebugArg = False,
):
    """Extract information from bills and invoices."""
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(level=log_level)
    
    if not input:
        console.print("[bold red]Error:[/bold red] --input is required")
        raise typer.Exit(code=1)

    input_path = Path(input)
    if not input_path.exists():
        console.print(f"[bold red]Error:[/bold red] Input path does not exist: {input}")
        raise typer.Exit(code=1)

    if input_path.is_dir():
        image_files = _collect_images(input_path)
    else:
        image_files = [input_path]

    if not image_files:
        console.print("[bold red]Error:[/bold red] No valid image files found")
        raise typer.Exit(code=1)

    output_dir = None
    if output:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        if verbose:
            console.print(f"[dim]Output directory: {output_dir}[/dim]")

    if verbose:
        console.print(f"[dim]Processing {len(image_files)} file(s)[/dim]")

    logger.info("[bold]Starting bill extraction...[/bold]")

    try:
        ocr_engine = OCREngine(lang=lang)
    except ImportError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    extractor = BillExtractor()
    results: list[tuple[str, ExtractedBill]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        main_task = progress.add_task("[cyan]Processing files...", total=len(image_files))

        for img_file in image_files:
            file_task = progress.add_task(f"[dim]{img_file.name}[/dim]", total=5, parent=main_task)
            
            progress.update(file_task, description=f"[cyan]Loading models for {img_file.name}...", completed=0)
            logger.info(f"Processing: {img_file.name}")

            try:
                if preprocess:
                    progress.update(file_task, description=f"[cyan]Preprocessing {img_file.name}...", completed=1)
                    logger.info("Preprocessing image...")
                    
                    if not PREPROCESS_AVAILABLE:
                        console.print("[bold yellow]Warning:[/bold yellow] opencv-python not installed, skipping preprocessing")
                        processed = None
                    else:
                        processed = preprocessing_pipeline(str(img_file))
                        logger.info(f"Preprocessing complete")
                    
                    progress.update(file_task, description=f"[cyan]Running OCR on {img_file.name}...", completed=2)
                    if processed is not None:
                        ocr_results = ocr_engine.read_text_from_array(processed)
                    else:
                        ocr_results = ocr_engine.read_text(str(img_file))
                else:
                    progress.update(file_task, description=f"[cyan]Running OCR on {img_file.name}...", completed=2)
                    ocr_results = ocr_engine.read_text(str(img_file))
                
                logger.info(f"OCR found {len(ocr_results)} text regions")

                progress.update(file_task, description=f"[cyan]Extracting fields from {img_file.name}...", completed=3)
                bill_data = extractor.extract(ocr_results)
                logger.info(f"Extracted: vendor={bill_data.vendor}, total={bill_data.total}")
                results.append((img_file.name, bill_data))
                
                progress.update(file_task, description=f"[cyan]Saved {img_file.name}", completed=5)
                logger.info(f"Complete: {img_file.name}")

            except Exception as e:
                console.print(f"[bold red]Error processing {img_file.name}:[/bold red] {e}")
                logger.error(f"Failed to process {img_file.name}: {e}")
                if debug:
                    raise

            progress.update(main_task, advance=1)

    if output_dir:
        logger.info(f"Saving results to {output_dir}")
        _save_results(results, output_dir)
        logger.info("[green]Results saved successfully[/green]")
        console.print(f"[bold green]Results saved to:[/bold green] {output_dir}")
    else:
        _print_json_output(results)


def _collect_images(folder: Path) -> list[Path]:
    """Collect image files from a folder."""
    extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    return sorted(
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    )


def _display_results(results: list[tuple[str, ExtractedBill]], verbose: bool):
    """Display results in a table."""
    table = Table(title="Extraction Results")
    table.add_column("File", style="cyan")
    table.add_column("Vendor", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Invoice #", style="magenta")
    table.add_column("Total", style="bold green")
    table.add_column("Tax", style="yellow")
    table.add_column("Currency", style="cyan")

    for filename, bill in results:
        table.add_row(
            filename,
            bill.vendor or "-",
            str(bill.date) if bill.date else "-",
            bill.invoice_number or "-",
            f"{bill.total:.2f}" if bill.total else "-",
            f"{bill.tax:.2f}" if bill.tax else "-",
            bill.currency,
        )

    console.print(table)

    if verbose:
        for filename, bill in results:
            console.print(f"\n[bold cyan]Details for {filename}:[/bold cyan]")
            console.print(f"  Items: {len(bill.items)}")
            if bill.subtotal:
                console.print(f"  Subtotal: {bill.subtotal:.2f}")


def _save_results(results: list[tuple[str, ExtractedBill]], output_dir: Path):
    """Save results to output directory."""
    for filename, bill in results:
        output_file = output_dir / f"{Path(filename).stem}.json"
        with open(output_file, "w") as f:
            json.dump(bill.model_dump(mode="json"), f, indent=2, default=str)


def _print_json_output(results: list[tuple[str, ExtractedBill]]):
    """Print results as JSON to stdout."""
    output = [
        {"file": filename, "data": bill.model_dump(mode="json")}
        for filename, bill in results
    ]
    console.print_json(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    app()