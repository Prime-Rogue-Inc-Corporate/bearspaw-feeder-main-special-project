# bearspaw-feeder-main-special-project

Roger Wilco Imagery special project **RWI-SP-002: Bearspaw South Feeder Main, Calgary**. Project page:
https://rogerwilcoimagery.com/project/bearspaw.html

This repository holds **raw public records only**: City, Council and provincial documents, open data, river and weather series and
satellite imagery, archived unchanged. Analysis and drafts are kept elsewhere; nothing here is an investigative finding.

| Path | What |
|---|---|
| `raw/` | Archived public records, each as received |
| `site/project.yaml` | The project page manifest read by the site build |
| `tools/stamp.py` | Checksums and Bitcoin timestamps |
| `SHA256SUMS`, `proofs/` | SHA-256 of every file and its OpenTimestamps proof (`proofs/index.json` lists status and Bitcoin block) |

Every file is checksummed and stamped on push; pending proofs are upgraded every 3 hours. Check any file with
`ots verify proofs/<path>.ots -f <path>`.
