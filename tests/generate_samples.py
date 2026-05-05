#!/usr/bin/env python3
"""Generate synthetic sample invoice images for testing."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES_DIR.mkdir(exist_ok=True)

VENDORS = [
    "EDIFICE SARL",
    "SOLUTIONS SERVICES",
    "BOULANGERIE DU CENTRE",
    "AUTO-ECOLE PERMIS",
    "PHARMACIE PRINCIPALE",
    "LE RESTAURANT GOURMAND",
    "STUDIO PHOTO",
    "MECANIQUE AUTO",
    "CAFE DU MARCHE",
    "BOUTIQUE MODE",
]

INVOICE_PREFIXES = ["FA", "FAC", "FACT", "INV", "F"]


def create_invoice_image(
    vendor: str, invoice_num: str, date: str, amount: float, output_path: Path
):
    """Create a synthetic invoice image."""
    width, height = 800, 600
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.rectangle([(50, 50), (750, 550)], outline="black", width=2)

    draw.text((100, 80), "FACTURE", fill="black", font=font_large)
    draw.text((500, 80), f"N° {invoice_num}", fill="black", font=font_medium)

    draw.text((100, 150), f"Émetteur: {vendor}", fill="black", font=font_medium)

    draw.text((100, 220), f"Date: {date}", fill="black", font=font_medium)

    draw.text((100, 290), "Description", fill="black", font=font_medium)
    draw.text((100, 320), "Prestations de services", fill="black", font=font_small)

    draw.text((100, 400), "Sous-total:", fill="black", font=font_small)
    draw.text((600, 400), f"{amount * 0.8:.2f} €", fill="black", font=font_small)

    draw.text((100, 430), "TVA (20%):", fill="black", font=font_small)
    draw.text((600, 430), f"{amount * 0.2:.2f} €", fill="black", font=font_small)

    draw.rectangle([(100, 470), (700, 475)], fill="black")

    draw.text((100, 500), "TOTAL TTC:", fill="black", font=font_medium)
    draw.text((550, 500), f"{amount:.2f} €", fill="black", font=font_large)

    img.save(output_path)
    print(f"Created: {output_path}")


def generate_samples():
    """Generate all sample invoice images."""
    samples = [
        ("EDIFICE SARL", "FA2024-001", "15/03/2024", 150.00),
        ("SOLUTIONS SERVICES", "FAC-2024-0456", "22/03/2024", 299.99),
        ("BOULANGERIE DU CENTRE", "FACT-789", "01/04/2024", 45.50),
        ("AUTO-ECOLE PERMIS", "INV-2024-123", "10/04/2024", 850.00),
        ("PHARMACIE PRINCIPALE", "FA2024012", "18/04/2024", 23.90),
        ("LE RESTAURANT GOURMAND", "F-2024-056", "25/04/2024", 127.50),
        ("STUDIO PHOTO", "FAC20240089", "02/05/2024", 75.00),
        ("MECANIQUE AUTO", "INV2024050", "08/05/2024", 420.00),
        ("CAFE DU MARCHE", "FA-24-0156", "15/05/2024", 18.50),
        ("BOUTIQUE MODE", "FACT-2024-78", "20/05/2024", 199.99),
    ]

    for i, (vendor, inv_num, date, amount) in enumerate(samples, 1):
        output_path = SAMPLES_DIR / f"facture{i}.png"
        create_invoice_image(vendor, inv_num, date, amount, output_path)


if __name__ == "__main__":
    generate_samples()
    print(f"\nGenerated {len(list(SAMPLES_DIR.glob('*.png')))} sample invoices in {SAMPLES_DIR}")
