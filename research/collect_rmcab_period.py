"""Recolector de un periodo acotado (máximo 92 días), secuencial y reanudable."""

import argparse
import json
from pathlib import Path
import time

import pandas as pd

from research.air_quality import clean_measurements, coverage_by_year, fetch_report


def collect_period(start, end, *, cache, allow_network=False, progress=print):
    """No publica un periodo completo si falla cualquiera de sus fechas.

    Las descargas correctas permanecen en caché, incluso si una fecha falla.
    No se solicita más de un reporte simultáneamente.
    """
    dates = pd.date_range(start, end).strftime("%Y-%m-%d").tolist()
    if not 1 <= len(dates) <= 92:
        raise ValueError("Selecciona entre 1 y 92 días; usa lotes trimestrales o menores.")
    frames, sources, failures = [], [], []
    for number, day in enumerate(dates, 1):
        attempts = 2 if allow_network else 1
        for attempt in range(1, attempts + 1):
            try:
                frame, source = fetch_report(day, cache, allow_network=allow_network)
                if frame.empty:
                    raise ValueError("Reporte sin filas de estación; revisar antes de publicar el lote.")
                frames.append(frame)
                sources.append(source)
                progress(f"{number}/{len(dates)} {day}: {len(frame)} filas; PM25={frame.pm_25.notna().sum()}, PM10={frame.pm_10.notna().sum()}")
                break
            except Exception as error:
                progress(f"{day}, intento {attempt}: {type(error).__name__}: {str(error)[:180]}")
                if attempt == attempts:
                    failures.append(day)
                else:
                    time.sleep(4)
    if failures:
        raise RuntimeError(f"No se publica un periodo incompleto. Fechas fallidas: {', '.join(failures)}. Caché conservada.")
    data = clean_measurements(pd.concat(frames, ignore_index=True))
    if data.duplicated(["station_id", "datetime"]).any():
        raise ValueError("Estación/hora duplicada en el periodo.")
    if set(pd.to_datetime(data.report_date).dt.strftime("%Y-%m-%d")) != set(dates):
        raise ValueError("Las fechas observadas no coinciden con las solicitadas.")
    return data.sort_values(["datetime", "station_id"]).reset_index(drop=True), sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(".local/research/rmcab"))
    parser.add_argument("--network", action="store_true", help="Descargar solo las fechas ausentes de caché.")
    args = parser.parse_args()
    data, sources = collect_period(args.start, args.end, cache=args.cache, allow_network=args.network,
                                   progress=lambda message: print(message, flush=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False, lineterminator="\n")
    args.output.with_suffix(".sources.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    coverage_by_year(data).to_csv(args.output.with_suffix(".coverage.csv"), index=False, lineterminator="\n")
    print(f"Guardado: {args.output}; {data.report_date.nunique()} reportes. Ausencias de sensores conservadas.")


if __name__ == "__main__":
    main()
