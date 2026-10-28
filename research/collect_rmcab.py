"""CLI secuencial, reanudable y con caché para reportes públicos diarios."""

import argparse
import json
from pathlib import Path

import pandas as pd

from research.air_quality import collect_reports, clean_measurements, coverage_by_year


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pilot", action="store_true", help="Un día de cada año 2015–2025 y una semana de 2025; no representa años completos.")
    group.add_argument("--start", help="Fecha inicial YYYY-MM-DD; descargar por mes para reanudar fácilmente.")
    parser.add_argument("--end", help="Fecha final inclusiva YYYY-MM-DD")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(".local/research/rmcab"))
    parser.add_argument("--network", action="store_true", help="Descargar únicamente las fechas que aún no estén en caché.")
    args = parser.parse_args()
    if args.pilot:
        dates = [f"{year}-02-03" for year in range(2015, 2026)] + list(pd.date_range("2025-02-04", "2025-02-09").strftime("%Y-%m-%d"))
    else:
        if not args.end:
            parser.error("--end es obligatorio con --start")
        dates = list(pd.date_range(args.start, args.end).strftime("%Y-%m-%d"))
        if not 1 <= len(dates) <= 31:
            parser.error("Procesa entre 1 y 31 días por ejecución; usa lotes mensuales para los once años.")
    data, manifests = collect_reports(dates, args.cache, allow_network=args.network)
    data = clean_measurements(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False, lineterminator="\n")
    args.output.with_suffix(".sources.json").write_text(json.dumps(manifests, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    coverage = coverage_by_year(data)
    coverage.to_csv(args.output.with_suffix(".coverage.csv"), index=False, lineterminator="\n")
    print(coverage.to_string(index=False))
    print(f"Guardado: {args.output}. No se cambió el dataset del dashboard.")


if __name__ == "__main__":
    main()
