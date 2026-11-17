# OpenCEM: Multimodal photovoltaic and battery microgrid dataset with context records and sky imagery

Version 1.0.0 · DOI: [10.5281/zenodo.21436223](https://doi.org/10.5281/zenodo.21436223)

OpenCEM is a one-year record of a physical, on-campus PV-battery microgrid in
Longgang, Shenzhen, China. The release aligns detailed inverter state, settings,
statistics and fault history with privacy-reviewed operational context and an
upward-facing sky-image archive.

The version of record is published on Zenodo at
[10.5281/zenodo.21436223](https://doi.org/10.5281/zenodo.21436223). This
directory mirrors the contents and organization of the deposited release.

## Contents

- `data/opencem-v1.0.0.sqlite`: the main SQLite artifact.
- `sky_images/frames/`: retained 1920 by 1920 JPEG frames organized as
  `YYYY/MM/DD/YYYYMMDDTHHMM00Z.jpg`.
- `documentation/`: schema, column dictionary, image manifest, provenance, and
  validation reports.
- `validation/`: rerunnable release validator and generated machine-readable
  outputs.
- `code/`: sanitized acquisition implementation, database construction, context, image,
  weather/news enrichment, simulator, and visualization code.
- `manifests/`: release-tree checksums and the machine-readable release manifest.

## Packed Zenodo layout

The Zenodo record distributes the release as the following upload files:

- `README.md` and `LICENSE-DATA.txt`: standalone orientation and data licence.
- `opencem-v1.0.0-support.zip`: code, documentation, validation resources,
  metadata, licences, and release-tree manifests under a top-level
  `opencem-v1.0.0/` directory.
- `opencem-v1.0.0.sqlite.zst`: the Zstandard-compressed SQLite database.
- `opencem-v1.0.0-sky-2026-03.tar.zst` through
  `opencem-v1.0.0-sky-2026-07.tar.zst`: monthly sky-image archives. Their
  members begin at `sky_images/frames/2026/MM/`.
- `opencem-v1.0.0-SHA256SUMS.txt`: SHA-256 checksums for every other uploaded
  file.

The complete working layout can be reconstructed with `unzip`, `zstd`, and
`tar`:

```bash
unzip opencem-v1.0.0-support.zip
mkdir -p opencem-v1.0.0/data
zstd -d opencem-v1.0.0.sqlite.zst \
  -o opencem-v1.0.0/data/opencem-v1.0.0.sqlite
for archive in opencem-v1.0.0-sky-2026-*.tar.zst; do
  zstd -dc "$archive" | tar -xf - -C opencem-v1.0.0
done
cd opencem-v1.0.0
```

The filename digits for sky images reproduce the camera-local wall clock in the
`Asia/Shanghai` timezone. The historical trailing `Z` is a naming convention and
does not mean that those digits are UTC. Database timestamps are fractional Unix
seconds in UTC. The retained image archive intentionally continues through
14 July 2026, 12:25 local time, after the electrical series ends on 13 July
2026, 13:13:53 local time; each modality should be bounded by its own manifest.

## Quick start

```bash
sqlite3 data/opencem-v1.0.0.sqlite ".tables"
sqlite3 data/opencem-v1.0.0.sqlite \
  "SELECT inverter, datetime(MIN(read_ts),'unixepoch'), datetime(MAX(read_ts),'unixepoch') FROM analog_measurements GROUP BY inverter;"
```

Python users can query the file directly with the standard `sqlite3` module,
Pandas, DuckDB's SQLite scanner, or the included dataset-backed simulator. Array
columns are JSON text. Context rows use separate `recorded`, `start`, and `end`
timestamps so prediction studies can enforce the information available at a
given decision time.

## Reproducibility and component-specific material

The release includes the transformations needed to validate, enrich, and use the
published artifacts. The installed inverter's proprietary register map, the
private technical manual, recorder authentication/download code, raw workstation
logs, raw Modbus JSON captures, PostgreSQL backups, and privacy-review working
files are excluded. Component-specific acquisition and packed-clock operations
are documented through public interfaces, output schema, and provenance rather
than redistributed source material.

## Validation

See `validation/README.md`. The frozen report checks SQLite integrity, public-key
uniqueness, JSON encodings, timestamp ranges, cadence, missingness, electrical
identities, context intervals, image decoding and dimensions, image cadence, and
cross-modal timing.

## Licence and citation

Data, images, documentation, and manifests are licensed under CC BY 4.0. Code is
MIT licensed. Cite the dataset using DOI `10.5281/zenodo.21436223`; the Zenodo
record provides the complete creator metadata.
