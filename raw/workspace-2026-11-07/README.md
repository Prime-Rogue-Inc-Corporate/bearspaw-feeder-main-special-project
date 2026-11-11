# raw/workspace-2026-11-07: records collected in the analysis session, 7 Nov 2026

Public records pulled or received in the first analysis session, archived as collected. Each folder keeps the `SHA256SUMS`,
`MANIFEST.json` and `_fetch_log.tsv` written when it was collected, so file names here differ from the `{utc}-name` pattern used
elsewhere in `raw/`.

| Folder | Source | Where | Collected (UTC) |
|---|---|---|---|
| `opendata/water_main_breaks_dpcu-jr23_2026-11-07.csv` | City of Calgary Open Data, Water Main Breaks (dpcu-jr23) | https://data.calgary.ca/d/dpcu-jr23 | Exported by hand on 7 Nov 2026; export time not recorded |
| `opendata/public_water_main_w6h9-w33i_2026-11-07.csv` | City of Calgary Open Data, Public Water Main (w6h9-w33i) | https://data.calgary.ca/d/w6h9-w33i | Same. The file is complete: 60,740 segments, 5,419 km. The `DIAM` column uses a thousands comma (`1,950`) |
| `weather/` | Environment and Climate Change Canada historical climate data: Calgary Int'l CS, Calgary Int'l, Springbank A, COP Upper; daily and hourly | https://climate.weather.gc.ca/climate_data/bulk_data_e.html (one URL per file in `_fetch_log.tsv`) | 2026-11-07 09:51–09:58 |
| `eccc_stations/` | ECCC station lists near Calgary and the GeoMet service description | https://api.weather.gc.ca (URLs in `_fetch_log.tsv`) | 2026-11-07 |
| `hydrometric/` | Water Survey of Canada daily mean and real-time flows, Bow and Elbow stations | https://api.weather.gc.ca/collections/hydrometric-daily-mean and `hydrometric-realtime` | 2026-11-07 10:01–10:02 |
| `seismic/`, `reanalysis/` | Collection manifests only | see each `MANIFEST.json` | 2026-11-07 |
| `dem/` | Elevation: NRCan HRDEM index and metadata, and small clips of Copernicus GLO-30, NASADEM and ALOS for the project area | see `dem/MANIFEST.json` | 2026-11-07 |
| `fire/firms_public_snapshot/` | NASA FIRMS public active-fire snapshot | see `fire/MANIFEST.json` | 2026-11-07 |
| `city/maps/`, `city/pages/` | City of Calgary project maps and replacement-project page text | calgary.ca | Screenshots and a text copy captured by hand; dates are in the file names |
| `docs/` | The session's capture log, fetch queue and reachability test | n/a | 2026-11-07 |

## Listed in a manifest but not stored here
These are too large for git. Their checksums are in the folder's `SHA256SUMS` and `MANIFEST.json`, so a fresh download can be checked.
- `dem/`: the 1 m HRDEM lidar tiles (about 2.2 GB).
- `fire/cwfis_hotspots/` (about 400 MB) and `fire/firms_country_yearly/` (about 150 MB).
- Satellite imagery: Sentinel-2 (4.0 GB, `s2/`), GOES land-surface temperature (3.2 GB, `goes_lst/`), Sentinel-1 (1.9 GB, `s1/`),
  Landsat (1.1 GB, `landsat/`). Each of those folders here holds only its `MANIFEST.json` and `SHA256SUMS`.
