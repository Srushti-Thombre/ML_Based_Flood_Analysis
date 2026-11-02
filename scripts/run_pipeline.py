"""Command-line entry point for the flood analysis pipeline."""

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from flood_analysis.pipeline import run_pipeline


def main() -> None:
    """Parse arguments and run the Kurla flood analysis."""
    parser = argparse.ArgumentParser(description="Run flood vulnerability analysis.")
    parser.add_argument("--place-name", default="Kurla, Mumbai, India")
    parser.add_argument(
        "--dem-path",
        type=Path,
        default=PROJECT_ROOT / "Project_Files" / "kurla.tif",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "Project_Files",
    )
    parser.add_argument(
        "--include-historic",
        action="store_true",
        help="Stream and join the historical Mumbai Salsette flood dataset.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip automatic HTML and PDF report generation.",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Skip standalone Leaflet dashboard generation.",
    )
    args = parser.parse_args()
    run_pipeline(
        args.place_name,
        args.dem_path,
        args.output_dir,
        include_historic=args.include_historic,
        generate_report_output=not args.no_report,
        generate_dashboard_output=not args.no_dashboard,
    )


if __name__ == "__main__":
    main()
