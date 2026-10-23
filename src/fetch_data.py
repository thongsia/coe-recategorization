#!/usr/bin/env python3
"""
Step 3 - Data fetch from data.gov.sg (action API), with provenance logging.

Fetches IN FULL, via https://data.gov.sg/api/action/datastore_search only
(versioned api.data.gov.sg/v1 and /v3 are DEAD - do not use):
  (a) COE bidding results   d_69b3380ad7e51aff3a7dcc84eba52b8a  -> data/raw/coe_bids.csv
  (b) vehicle registrations d_d3f4d708e1d0a37b4365414e2fad3a07  -> data/raw/registrations.csv

CPI (d_bdaff844e3ef89d39fceb962ff8f0791) is NOT fetched: it is optional
context only, and no step of this study uses it -> recorded as 'not used'
in verification/provenance_log.csv and provenance.md.

Pagination (plan-mandated): offset pagination, limit <= 500 rows/request.
(`start` is IGNORED by the endpoint; large single fetches return HTTP 413.)
A per-request status log is written to verification/fetch_requests.csv.

Writes:
  data/raw/coe_bids.csv          (raw records, untouched - real fields in
                                  response field order; _id used only for
                                  uniqueness checks)
  data/raw/registrations.csv
  verification/fetch_requests.csv   (per-request: offset, http status, n records, latency, ts)
  verification/provenance_log.csv   (per resource: timestamps, row counts, sha256)

HARD-FAILS (raises) if fetched count != API-stated total, or if duplicate
_id rows appear, for any resource.

Layering contract: reads nothing local; writes only data/raw/ and
verification/ (fetch logs + provenance). Root of the pipeline.

Run:  python3 src/fetch_data.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402  (single source of truth for ids/limits/paths)

BASE = config.DATA_GOVSG_API_ENDPOINT
PAGE = min(500, config.DATA_GOVSG_MAX_ROWS_PER_REQUEST)  # plan-mandated cap
MAX_ATTEMPTS = 4
BACKOFF_S = [2, 5, 10]

ROOT = Path(config.WORKSPACE_ROOT)
RAW = ROOT / "data" / "raw"
VER = ROOT / "verification"
RAW.mkdir(parents=True, exist_ok=True)
VER.mkdir(parents=True, exist_ok=True)

# (key, resource_id, raw csv filename)
RESOURCES = [
    ("coe_bids", config.RESOURCES["coe_bids"], "coe_bids.csv"),
    ("registrations", config.RESOURCES["registrations"], "registrations.csv"),
]

# CPI is optional context, unused by this study -> recorded, not fetched.
CPI_RECORD = {
    "resource_key": "cpi",
    "resource_id": config.RESOURCES["cpi"],
    "endpoint": BASE,
    "fetch_started_utc": "",
    "fetch_completed_utc": "",
    "api_stated_total": "",
    "fetched_rows": 0,
    "unique_id_rows": 0,
    "raw_file": "NOT FETCHED",
    "sha256": "n/a",
    "n_fields": 0,
    "n_requests": 0,
    "status": "not used (optional context; no study step uses CPI)",
}

UA = "coe-category-study/1.0 (research fetch; contact: hermes agent)"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_page(session: requests.Session, resource_id: str, limit: int, offset: int):
    """One paginated request with retries on transient failures.

    Returns (result_dict, http_status, latency_ms, attempts_used).
    Raises RuntimeError if all attempts fail.
    """
    url = f"{BASE}?resource_id={resource_id}&limit={limit}&offset={offset}"
    last_err = None
    for attempt in range(MAX_ATTEMPTS):
        t0 = time.monotonic()
        status, latency_ms = None, 0
        try:
            resp = session.get(url, timeout=120, headers={"User-Agent": UA})
            status = resp.status_code
            latency_ms = int((time.monotonic() - t0) * 1000)
            if status == 413:
                raise RuntimeError(
                    f"HTTP 413 (payload too large) at offset={offset} limit={limit}"
                )
            if status in (429,) or status >= 500:
                raise RuntimeError(f"HTTP {status} transient at offset={offset}")
            if status != 200:
                raise RuntimeError(
                    f"HTTP {status} at offset={offset}: {resp.text[:300]}"
                )
            data = json.loads(resp.content.decode("utf-8"), strict=False)
            if not data.get("success", data.get("result") is not None):
                raise RuntimeError(f"API error payload at offset={offset}: {str(data)[:300]}")
            return data["result"], status, latency_ms, attempt + 1
        except (requests.exceptions.RequestException, RuntimeError, json.JSONDecodeError) as e:
            last_err = e
            latency_ms = latency_ms or int((time.monotonic() - t0) * 1000)
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)])
    raise RuntimeError(
        f"giving up on {resource_id} offset={offset} after {MAX_ATTEMPTS} attempts: {last_err}"
    )


def fetch_full(resource_id: str, req_log: list) -> tuple[int, list, list]:
    """Page through the whole store at PAGE rows/request.

    Returns (api_stated_total, records, field_order).
    """
    session = requests.Session()
    records: list[dict] = []
    total: int | None = None
    fields: list[str] | None = None
    offset = 0
    req_no = 0
    while True:
        req_no += 1
        result, status, latency_ms, attempts = fetch_page(session, resource_id, PAGE, offset)
        ts = _now()
        if total is None:
            total = int(result.get("total", 0))
        if fields is None:
            fields = [f["id"] for f in result.get("fields", [])]
        page = result.get("records", [])
        req_log.append({
            "resource_id": resource_id,
            "request_no": req_no,
            "offset": offset,
            "limit": PAGE,
            "http_status": status,
            "n_records": len(page),
            "latency_ms": latency_ms,
            "attempts": attempts,
            "ts_utc": ts,
        })
        print(f"  [{resource_id[:8]}] req {req_no:3d} offset={offset:6d} "
              f"n={len(page):4d} total={total} ({latency_ms} ms)", flush=True)
        if not page:
            break
        records.extend(page)
        offset += PAGE
        if len(page) < PAGE or offset >= total:
            break
        time.sleep(0.25)  # polite delay to avoid throttling (429)
        if offset > total + PAGE:  # safety guard against runaway pagination
            raise RuntimeError("runaway pagination guard tripped")
    session.close()
    return total, records, fields


def write_csv(path: Path, records: list[dict], field_order: list[str]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(field_order)
        for rec in records:
            w.writerow(["" if rec.get(c) is None else rec.get(c, "") for c in field_order])


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    req_log: list[dict] = []
    prov_rows: list[dict] = []

    for key, rid, fname in RESOURCES:
        out = RAW / fname
        # --- resumability: if the raw file already exists and matches the
        # API-stated total, do NOT re-fetch (raw files are immutable once
        # written; a partial file is deleted and re-fetched).
        if out.exists():
            t0 = time.monotonic()
            first, status, lat, _ = fetch_page(
                requests.Session(), rid, 1, 0)
            stated = int(first.get("total", 0))
            n_lines = sum(1 for _ in open(out)) - 1  # minus header
            if n_lines == stated:
                ts = _now()
                prov_rows.append({
                    "resource_key": key,
                    "resource_id": rid,
                    "endpoint": BASE,
                    "fetch_started_utc": ts,
                    "fetch_completed_utc": ts,
                    "api_stated_total": stated,
                    "fetched_rows": n_lines,
                    "unique_id_rows": n_lines,
                    "raw_file": f"data/raw/{fname}",
                    "sha256": sha256_of(out),
                    "n_fields": len(first.get("fields", [])),
                    "field_order": ",".join(f["id"] for f in first.get("fields", [])),
                    "n_requests": 1,
                    "status": "ok (resumed from existing complete fetch)",
                })
                print(f"[fetch] {key}: already complete ({n_lines} rows) - "
                      f"skipped re-fetch", flush=True)
                continue
            else:
                print(f"[fetch] {key}: existing file incomplete "
                      f"({n_lines} != {stated}) - re-fetching", flush=True)
                out.unlink()
        print(f"[fetch] {key}: resource_id={rid} (page={PAGE}, offset pagination) ...",
              flush=True)
        started = _now()
        stated_total, records, fields = fetch_full(rid, req_log)
        completed = _now()
        n = len(records)
        ids = [r.get("_id") for r in records]
        n_unique = len(set(ids))
        if n != stated_total:
            raise RuntimeError(
                f"HARD-FAIL [{key}]: fetched {n} != API-stated total {stated_total}"
            )
        if n_unique != n:
            raise RuntimeError(
                f"HARD-FAIL [{key}]: duplicate _id rows ({n_unique} unique of {n})"
            )
        write_csv(out, records, fields)
        digest = sha256_of(out)
        prov_rows.append({
            "resource_key": key,
            "resource_id": rid,
            "endpoint": BASE,
            "fetch_started_utc": started,
            "fetch_completed_utc": completed,
            "api_stated_total": stated_total,
            "fetched_rows": n,
            "unique_id_rows": n_unique,
            "raw_file": f"data/raw/{fname}",
            "sha256": digest,
            "n_fields": len(fields),
            "field_order": ",".join(fields),
            "n_requests": sum(1 for r in req_log if r["resource_id"] == rid),
            "status": "ok" if n == stated_total else "MISMATCH",
        })
        print(f"[fetch] {key}: stated={stated_total} fetched={n} unique={n_unique} "
              f"sha256={digest[:16]}... -> {out}", flush=True)

    # CPI: recorded as not used (plan step 3c - fetch only if used).
    prov_rows.append(CPI_RECORD)

    # ---- per-request log ----
    req_path = VER / "fetch_requests.csv"
    with open(req_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "resource_id", "request_no", "offset", "limit", "http_status",
            "n_records", "latency_ms", "attempts", "ts_utc"])
        w.writeheader()
        w.writerows(req_log)
    print(f"[fetch] per-request log -> {req_path} ({len(req_log)} requests)")

    # ---- provenance log ----
    prov_path = VER / "provenance_log.csv"
    with open(prov_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prov_rows[0].keys()))
        w.writeheader()
        w.writerows(prov_rows)
    print(f"[fetch] provenance -> {prov_path}")
    print("[fetch] DONE")


if __name__ == "__main__":
    main()
