"""Агрегация неопределённости probe-канала: N≥5 прогонов → доверительный интервал (AC-7).

ЧИСТАЯ функция, без I/O и без часов — детерминирована при фиксированном входе (тестируется
mock'ом). Инвариант §6.7: улучшение Visibility заявляется только ВНЕ полосы шума, поэтому
роутер отдаёт не одно число, а ``{mean, ci_lower, ci_upper, n}``.

**Метод CI (документирован явно).** Двусторонний доверительный интервал Стьюдента:
``mean ± t(df=n-1, α) · s/√n``, где ``s`` — выборочное СКО, ``s/√n`` — стандартная ошибка
среднего. t-распределение (а не нормальное) корректно для МАЛЫХ выборок — probe как раз
работает на N около 5. Критические значения t для доверия 95% берутся из стандартной
таблицы (`_T_CRIT_95`, df 1..30); при df>30 t→z, используется нормальная аппроксимация
(``z = Φ⁻¹((1+conf)/2)`` через ``statistics.NormalDist``). Для доверия, отличного от 95%,
таблицы t нет — тогда применяется нормальная аппроксимация (задокументированный компромисс;
probe по умолчанию использует 95%). Все прогоны равны — при s=0 (полное согласие) интервал
вырождается в точку (``ci_lower==ci_upper==mean``), что корректно.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from math import sqrt

from wizor.llm_router.schemas import UncertaintyStats

# Минимум прогонов для честной оценки неопределённости (charter §6.7, AC-7).
MIN_RUNS = 5

# Уровень доверия по умолчанию для probe-канала.
_DEFAULT_CONFIDENCE = 0.95

# Критические значения t (двусторонние, доверие 95% / α=0.05) по df=n-1.
# Источник: стандартная таблица t-распределения Стьюдента. df>30 → нормальная аппрокс.
_T_CRIT_95: dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def _normal_critical(confidence: float) -> float:
    """z-критическое значение (нормальная аппроксимация) для двустороннего интервала."""
    return statistics.NormalDist().inv_cdf((1.0 + confidence) / 2.0)


def _critical_value(df: int, confidence: float) -> float:
    """Критическое значение: t-таблица для 95% при df≤30, иначе нормальная аппроксимация.

    df — число степеней свободы (n-1). Возвращает множитель для стандартной ошибки.
    """
    if confidence == _DEFAULT_CONFIDENCE and df in _T_CRIT_95:
        return _T_CRIT_95[df]
    # df>30 (t→z) или нестандартное доверие → нормальная аппроксимация (см. докстринг модуля).
    return _normal_critical(confidence)


def aggregate_uncertainty(
    values: Sequence[float],
    *,
    confidence: float = _DEFAULT_CONFIDENCE,
    min_runs: int = MIN_RUNS,
) -> UncertaintyStats:
    """Свести N прогонов в ``UncertaintyStats`` с t-доверительным интервалом (AC-7).

    ``values`` — скалярный сигнал одного прогона probe (напр. presence/score в [0..1]).
    Требуется ``len(values) >= min_runs`` (§6.7: N≥5) — иначе :class:`ValueError`
    (не молчаливое ослабление честности). При нулевой дисперсии интервал = точка.
    """
    n = len(values)
    if n < min_runs:
        msg = (
            f"uncertainty требует N≥{min_runs} прогонов (§6.7), получено {n}: "
            f"недостаточно для честного доверительного интервала."
        )
        raise ValueError(msg)

    mean = statistics.fmean(values)
    sample_sd = statistics.stdev(values)  # выборочное СКО (ddof=1)
    std_error = sample_sd / sqrt(n)
    margin = _critical_value(n - 1, confidence) * std_error

    return UncertaintyStats(
        mean=mean,
        ci_lower=mean - margin,
        ci_upper=mean + margin,
        n=n,
    )
