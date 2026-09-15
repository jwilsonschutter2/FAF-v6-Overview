# FAF6 Freight Flow Explorer

A static Mapbox GL JS interface joining FAF6.0 origin-destination flows to FAF6 area polygons.

## Run

1. Open a terminal in this folder.
2. Run `python -m http.server 8000`.
3. Open `http://localhost:8000`.
4. Paste a public Mapbox token in the header and click **Save token**.

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

## Folder structure

- `js/app.js`: application logic
- `styles/styles.css`: application styles
- `data/`: local JSON and GeoJSON data

## If you see “Unexpected token <”

The server returned an HTML page for a requested JSON file. This usually means a file in `data/` was not uploaded, the filename changed, or the host redirects unknown paths to `index.html`. This build reports the exact failing data path. Keep the full folder structure intact and run from the site root.

## GeoJSON export

**Export filtered GeoJSON** downloads the currently filtered area polygons and flow lines. The export includes readable area, commodity, mode, trade-type, direction, measure, units, and selection metadata.

## Scrollable table and CSV export

The bottom panel lists aggregated connected FAF areas for the current filters, sorted from highest to lowest flow. **Export table CSV** downloads the visible filtered results. Map hover uses one reusable dark popup so multiple popups cannot accumulate.
