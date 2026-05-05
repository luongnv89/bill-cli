"""Bill extraction CLI tool."""

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from bill_extract.extractor import BillExtractor, ExtractedBill
from bill_extract.logging import get_logger, setup_logging
from bill_extract.ocr import CorruptImageError, NoTextDetectedError, OCREngine

console = Console()
logger = get_logger("bill_extract")

try:
    from bill_extract.preprocess import preprocessing_pipeline

    PREPROCESS_AVAILABLE = True
except ImportError:
    PREPROCESS_AVAILABLE = False
    preprocessing_pipeline = None

app = typer.Typer(name="bill-extract", add_completion=False, no_args_is_help=True)


@app.command()
def main(
    ctx: typer.Context,
    input: Annotated[
        Optional[str], typer.Option("--input", "-i", help="Input file or folder path")
    ] = None,
    output: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Output directory")
    ] = None,
    lang: Annotated[str, typer.Option("--lang", "-l", help="OCR language")] = "fr",
    preprocess: Annotated[
        bool, typer.Option("--preprocess", "-p", help="Enable preprocessing")
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Debug output")] = False,
):
    """Extract information from bills and invoices."""
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(level=log_level)

    if not input:
        console.print("[bold red]Error:[/bold red] --input is required")
        console.print("Use bill-extract --help for usage information")
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
        raise typer.Exit(code=1) from e

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

            progress.update(
                file_task, description=f"[cyan]Loading models for {img_file.name}...", completed=0
            )
            logger.info(f"Processing: {img_file.name}")

            try:
                if preprocess:
                    progress.update(
                        file_task,
                        description=f"[cyan]Preprocessing {img_file.name}...",
                        completed=1,
                    )
                    logger.info("Preprocessing image...")

                    if not PREPROCESS_AVAILABLE:
                        console.print(
                            "[bold yellow]Warning:[/bold yellow] opencv-python not installed, skipping preprocessing"
                        )
                        processed = None
                    else:
                        processed = preprocessing_pipeline(str(img_file))
                        logger.info("Preprocessing complete")

                    progress.update(
                        file_task,
                        description=f"[cyan]Running OCR on {img_file.name}...",
                        completed=2,
                    )
                    if processed is not None:
                        ocr_results = ocr_engine.extract_text_from_array(processed)
                    else:
                        ocr_results = ocr_engine.extract_text(str(img_file))

                    logger.info(f"OCR found {len(ocr_results)} text regions")

                    normalized_results = []
                    for bbox, (text, confidence) in ocr_results:
                        x_coords = [pt[0] for pt in bbox]
                        y_coords = [pt[1] for pt in bbox]
                        x_center = sum(x_coords) / len(x_coords)
                        y_center = sum(y_coords) / len(y_coords)
                        normalized_results.append({
                            "text": text,
                            "confidence": confidence,
                            "x_center": x_center,
                            "y_center": y_center,
                            "bbox": bbox,
                        })

                    progress.update(
                        file_task,
                        description=f"[cyan]Extracting fields from {img_file.name}...",
                        completed=3,
                    )
                    bill_data = extractor.extract(normalized_results)
                else:
                    progress.update(
                        file_task,
                        description=f"[cyan]Running OCR on {img_file.name}...",
                        completed=2,
                    )
                    ocr_results = ocr_engine.extract_text(str(img_file))

                    logger.info(f"OCR found {len(ocr_results)} text regions")

                    normalized_results = []
                    for bbox, (text, confidence) in ocr_results:
                        x_coords = [pt[0] for pt in bbox]
                        y_coords = [pt[1] for pt in bbox]
                        x_center = sum(x_coords) / len(x_coords)
                        y_center = sum(y_coords) / len(y_coords)
                        normalized_results.append({
                            "text": text,
                            "confidence": confidence,
                            "x_center": x_center,
                            "y_center": y_center,
                            "bbox": bbox,
                        })

                    progress.update(
                        file_task,
                        description=f"[cyan]Extracting fields from {img_file.name}...",
                        completed=3,
                    )
                    bill_data = extractor.extract(normalized_results)
                logger.info(f"Extracted: vendor={bill_data.vendor}, total={bill_data.total}")
                results.append((img_file.name, bill_data, False))

                progress.update(file_task, description=f"[cyan]Saved {img_file.name}", completed=5)
                logger.info(f"Complete: {img_file.name}")

            except CorruptImageError as e:
                console.print(f"[bold red]Corrupt image error for {img_file.name}:[/bold red] {e}")
                logger.error(f"Corrupt image: {img_file.name} - {e}")
                console.print("[dim]  Skipping this file and continuing with others...[/dim]")
                results.append((img_file.name, _create_empty_bill(), True))

            except NoTextDetectedError as e:
                console.print(f"[yellow]No text detected for {img_file.name}:[/yellow] {e}")
                logger.warning(f"No text detected in {img_file.name}: {e}")
                console.print("[dim]  Skipping this file and continuing with others...[/dim]")
                results.append((img_file.name, _create_empty_bill(), True))

            except Exception as e:
                console.print(f"[bold red]Error processing {img_file.name}:[/bold red] {e}")
                logger.error(f"Failed to process {img_file.name}: {e}")
                if debug:
                    raise
                console.print("[dim]  Skipping this file and continuing with others...[/dim]")
                results.append((img_file.name, _create_empty_bill(), True))

            progress.update(main_task, advance=1)

    _print_batch_summary(results, len(image_files))

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
    return sorted(f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in extensions)


def _create_empty_bill() -> ExtractedBill:
    """Create an empty bill with null values for graceful degradation."""
    return ExtractedBill(
        vendor=None,
        date=None,
        invoice_number=None,
        items=[],
        subtotal=None,
        tax=None,
        total=None,
        currency="EUR",
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


def _format_json_output(bill: ExtractedBill, filename: str) -> dict:
    """Format bill data into the required JSON output format."""
    output = {}

    if bill.date:
        output["date"] = bill.date.isoformat()
    else:
        logger.warning(f"Missing date for {filename}")
        output["date"] = None

    if bill.total is not None:
        output["amount"] = round(bill.total, 2)
    else:
        logger.warning(f"Missing amount for {filename}")
        output["amount"] = None

    if bill.invoice_number:
        output["id"] = bill.invoice_number
    else:
        logger.warning(f"Missing invoice number (id) for {filename}")
        output["id"] = None

    return output


def _save_results(results: list[tuple], output_dir: Path):
    """Save results to output directory."""
    for item in results:
        filename, bill = item[0], item[1]
        output_file = output_dir / f"{Path(filename).stem}.json"
        output = _format_json_output(bill, filename)
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)


def _print_batch_summary(results: list[tuple[str, ExtractedBill, bool]], total: int):
    """Print batch processing summary with success/failure counts."""
    failed = sum(1 for _, _, error in results if error)
    successful = total - failed

    console.print()
    console.print("[bold]Batch Processing Summary[/bold]")
    console.print(f"  Total files processed: [cyan]{total}[/cyan]")
    console.print(f"  Successful: [green]{successful}[/green]")
    if failed > 0:
        console.print(f"  Failed: [red]{failed}[/red]")
    else:
        console.print(f"  Failed: [green]{failed}[/green]")


def _print_json_output(results: list[tuple]):
    """Print results as JSON to stdout."""
    output = [_format_json_output(item[1], item[0]) for item in results]
    console.print_json(json.dumps(output, indent=2))


if __name__ == "__main__":
    app()
