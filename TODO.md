# TODO - PlagiaSense Firebase scan fixes

## Step 1
- Verify current Firestore adapter behavior for `find_one`, `insert_one`, and `sort` usage in routes.

## Step 2
- Fix Firestore adapter so `find_one({'_id': scan_id})` consistently matches Firestore document id.

## Step 3
- Fix `sort('created_at', -1)` behavior so report endpoints return correct newest-first scans.

## Step 4
- Ensure scan save endpoint stores fields in a Firestore-compatible way (JSON-safe + datetime serialization on read).

## Step 5
- Update any affected routes (`scan.py`, `report.py`, `admin.py`) to align with adapter capabilities.

## Step 6
- Run a quick local smoke test for `/api/scan/detect` and `/api/reports/<scan_id>`.

