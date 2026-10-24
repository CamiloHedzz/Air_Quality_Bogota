"""Reglas de relleno corto y variación sintética reproducible para el mapa.

La variación es una elección de escenario, no un intervalo de confianza ni
una medición. Nunca se aplica a días respaldados por fuentes o huecos cortos.
"""
import hashlib

import numpy as np
import pandas as pd

SHORT_GAP_DAYS = 3
DEFAULT_VARIATION = 10
SIMULATION_SEED = 20251024
AR_COEFFICIENT = 0.65


def variation_rate(value):
    value = float(DEFAULT_VARIATION if value is None else value)
    if not np.isfinite(value) or not 0 <= value <= 30:
        raise ValueError('La variación del escenario debe estar entre 0 y 30 %.')
    return value


def fill_short_gaps(values, max_gap=SHORT_GAP_DAYS):
    """Solo tramos completos de hasta tres días, entre dos observaciones.

    Un limit de pandas por sí solo también rellenaría el principio de huecos
    largos. Se comprueba la longitud TOTAL del tramo y no se extrapolan bordes.
    El índice debe corresponder a días consecutivos, en orden.
    """
    values = values.astype(float)
    missing = values.isna()
    run_length = missing.groupby((~missing).cumsum()).transform('sum')
    candidate = values.interpolate(method='linear', limit_area='inside')
    return candidate.where(~missing | run_length.le(max_gap))


def scenario_noise(names, dates, variable, variation, scale):
    """AR(1) aproximado con una ventana de 21 días; semilla por sector/variable.

    El calendario absoluto evita cambiar el escenario al filtrar mes/año o
    reordenar sectores. PCG64 explícito evita depender del generador por defecto.
    Un componente común y otro local evitan curvas idénticas sin asumir que
    los sectores tienen meteorología independiente. No es un modelo físico.
    """
    variation = variation_rate(variation)
    if not len(dates) or not len(names):
        return np.empty((len(dates), len(names)))
    if variation == 0:
        return np.zeros((len(dates), len(names)))
    calendar = pd.date_range('2015-01-01', '2025-12-31')
    offsets = calendar.get_indexer(dates)
    if (offsets < 0).any():
        raise ValueError('Fechas fuera del calendario del escenario.')
    kernel = AR_COEFFICIENT ** np.arange(21)
    kernel /= np.sqrt(np.square(kernel).sum())

    def draw(key):
        seed = int.from_bytes(hashlib.sha256(f'{SIMULATION_SEED}|{variable}|{key}'.encode()).digest()[:8], 'little')
        rng = np.random.Generator(np.random.PCG64(seed))
        innovation = rng.standard_normal(len(calendar) + len(kernel) - 1)
        return np.convolve(innovation, kernel, mode='valid')[offsets]

    common = draw('__common__')
    noise = np.column_stack([0.5 * common + np.sqrt(0.75) * draw(str(name)) for name in names])
    return noise * float(scale) * variation / 100
