# FAF6 Freight Flow Explorer

A static Mapbox GL JS interface joining FAF6.0 origin-destination flows to FAF6 area polygons.

## Run

1. Open a terminal in this folder.
2. Run `python -m http.server 8000`.
3. Open `http://localhost:8000`.
4. Click **Mapbox token** and enter a public token.

Do not open `index.html` directly because browsers commonly block local `fetch()` requests.

## Controls

- **Outbound** filters records where `dms_orig` equals the selected FAF area.
- **Inbound** filters records where `dms_dest` equals the selected FAF area.
- Commodity, domestic mode, trade type, and within-area flow filters are applied before aggregation.
- Tonnage is shown in thousand short tons; value is shown in millions of 2022 constant dollars.

## Data

- `data/faf6_zones.geojson`: FAF6 polygons keyed by `FAF6`.
- `data/flows.json`: compact rows keyed by `dms_orig` and `dms_dest`.
- `data/metadata.json`: legible zone, commodity, mode, trade, and field labels.
