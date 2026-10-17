"""
Command-line interface: OCR one or more PDFs and print or save the text.

    python ocr.py scan.pdf
    python ocr.py --grayscale -o out/ a.pdf b.pdf
"""
import argparse
import sys
from pathlib import Path

from tesseract import PageSegMode


def parse_variable(value: str):
    key, sep, val = value.partition("=")
    if not sep or not key:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {value!r}")
    return key, val


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extract text from scanned PDFs with Tesseract."
    )
    parser.add_argument("pdfs", nargs="+", type=Path, metavar="PDF")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="write <name>.txt for each PDF here instead of printing to stdout",
    )
    parser.add_argument("--first-page", type=int, default=1)
    parser.add_argument(
        "--last-page",
        type=int,
        default=0,
        help="last page to OCR; 0 or negative counts back from the end (default: 0)",
    )
    parser.add_argument("--dpi", type=int, default=250, help="render resolution (default: 250)")
    parser.add_argument(
        "--psm",
        type=int,
        default=int(PageSegMode.AUTO),
        choices=[int(mode) for mode in PageSegMode],
        help="page segmentation mode (default: 3)",
    )
    parser.add_argument("--grayscale", action="store_true", help="render pages in grayscale")
    parser.add_argument(
        "-c",
        dest="variables",
        action="append",
        default=[],
        type=parse_variable,
        metavar="KEY=VALUE",
        help="set a Tesseract variable (repeatable)",
    )
    args = parser.parse_args(argv)
    for pdf in args.pdfs:
        if not pdf.is_file():
            parser.error(f"no such file: {pdf}")

    from utils import ocr_to_text

    options = dict(args.variables)
    options.update(grayscale=args.grayscale, user_defined_dpi=args.dpi, psm=args.psm)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    for pdf in args.pdfs:
        pages = sorted(
            ocr_to_text(str(pdf), first_page=args.first_page, last_page=args.last_page, **options),
            key=lambda page: page[1],
        )
        text = "\n".join(page_text for page_text, _ in pages)
        if args.output_dir:
            target = args.output_dir / f"{pdf.stem}.txt"
            target.write_text(text, encoding="utf-8")
            print(f"{pdf} -> {target}", file=sys.stderr)
        else:
            sys.stdout.write(text)


if __name__ == "__main__":
    main()
