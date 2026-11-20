# Synthetic catalog benchmark

Measured 2026-11-21 on Windows 11 (build 26200), Python 3.14.0, AMD Ryzen 7 5800HS (16 logical processors). Run `python tools/benchmark.py` to repeat.

| Records | Index rebuild | Search | Traced peak |
| ---: | ---: | ---: | ---: |
| 0 | 4.63 ms | 0.49 ms | 0.13 MiB |
| 1 | 6.64 ms | 6.18 ms | 0.13 MiB |
| 100 | 36.89 ms | 10.52 ms | 0.16 MiB |
| 1,000 | 166.59 ms | 24.41 ms | 0.57 MiB |
| 10,000 | 1,448.62 ms | 110.01 ms | 5.70 MiB |

The script generates metadata records in a temporary directory, rebuilds category indexes, and searches for two matching terms. It does not import 10,000 actual bundles or measure agent context usage. Traced peak starts after the Python records are constructed, so it excludes that resident memory. Values are one-run observations, not performance guarantees.
