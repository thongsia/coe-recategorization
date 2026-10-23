"""
Step 1 - Environment access check.

Verifies environment access BEFORE any modeling and records each check in
verification/constraint_report.csv (pass/fail + detail). If any access is
blocked, the affected stage is reported as a documented constraint and the
study proceeds only on the accessible subset - never fabricated data.

Checks:
  1. workspace writability (each layout dir)
  2. data.gov.sg action-API reachability (PROBE ONLY: one small
     datastore_search request on the COE resource, limit=1; no bulk fetch)
  3. onemotoring.lta.gov.sg reachability (GET homepage, HEAD ok)
  4. presence of local consultation-paper and Car Cost PDFs (+ annexes)
  5. method-precedent documentation present (docs/methodology_notes.md)
"""
from __future__ import annotations

import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402

HTTP_TIMEOUT = 30
UA = "coe-category-study/batchA (research; probe only)"


def http_probe(url: str, params: dict | None = None, method: str = "GET"):
    """Small HTTP probe. Returns (status, body_preview, detail)."""
    if params:
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            body = resp.read(4000).decode("utf-8", errors="replace")
            return resp.status, body, f"HTTP {resp.status} from {url}"
    except urllib.error.HTTPError as e:
        return e.code, "", f"HTTP {e.code} from {url}"
    except Exception as e:  # URLError, timeout, etc.
        return None, "", f"{type(e).__name__}: {e} for {url}"


def main() -> int:
    rows = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def record(check, status, detail):
        rows.append({
            "check": check, "status": status, "detail": detail,
            "timestamp_utc": ts,
            "constraint_stage": "",
        })
        print(f"[{status.upper():4s}] {check}: {detail}")

    # ------------------------------------------------------------------
    # 1. Workspace writability
    # ------------------------------------------------------------------
    for name, d in [
        ("workspace_root", config.WORKSPACE_ROOT),
        ("src/", config.DIR_SRC),
        ("data/raw/", config.DIR_DATA_RAW),
        ("data/processed/", config.DIR_DATA_PROCESSED),
        ("tables/", config.DIR_TABLES),
        ("charts/", config.DIR_CHARTS),
        ("docs/", config.DIR_DOCS),
        ("verification/", config.DIR_VERIFICATION),
    ]:
        ok = os.path.isdir(d) and os.access(d, os.W_OK)
        detail = f"dir exists={os.path.isdir(d)} writable={os.access(d, os.W_OK)}"
        if ok:
            # actual write/read/delete round-trip
            probe = os.path.join(d, f".envcheck_{os.getpid()}")
            try:
                with open(probe, "w") as f:
                    f.write("ok")
                with open(probe) as f:
                    readback = f.read()
                os.remove(probe)
                detail += f"; write/read/delete round-trip ok ({readback!r})"
            except OSError as e:
                ok = False
                detail += f"; round-trip FAILED: {e}"
        record(f"workspace_writability:{name}", "pass" if ok else "fail", detail)

    # ------------------------------------------------------------------
    # 2. data.gov.sg action-API reachability (PROBE ONLY)
    # ------------------------------------------------------------------
    url = config.DATA_GOVSG_API_ENDPOINT
    params = {
        "resource_id": config.RESOURCES["coe_bids"],
        "limit": 1,  # probe only - NOT a bulk fetch
    }
    status, body, detail = http_probe(url, params=params)
    api_ok = status == 200
    if api_ok:
        try:
            payload = json.loads(body)
            n = payload.get("result", {}).get("total")
            detail += f"; response ok, total rows reported={n}"
            if n is not None and abs(n - 1990) > 20:
                detail += f" (NOTE: plan expected ~1,990)"
        except (json.JSONDecodeError, AttributeError):
            api_ok = False
            detail += "; response was not valid JSON"
    record("data_govsg_action_api_reachability", "pass" if api_ok else "fail", detail)

    # Also probe a versioned endpoint to document that it is dead (plan
    # assumption 3). Not required to pass; result is informational.
    s2, _, d2 = http_probe(
        "https://api.data.gov.sg/v1/action/datastore_search",
        params={"resource_id": config.RESOURCES["coe_bids"], "limit": 1},
    )
    usable = s2 == 200
    note = ("CONFIRMED unusable, consistent with plan" if not usable
            else "UNEXPECTED: versioned endpoint appears usable")
    print(f"[INFO] versioned api.data.gov.sg/v1 probe: {d2} -> {note}")
    rows.append({
        "check": "data_govsg_versioned_endpoint_v1 (informational)",
        "status": "info",
        "detail": (f"{d2}; {note}; plan assumption 3: versioned v1/v3 "
                   f"endpoints are dead - action-API only"),
        "timestamp_utc": ts, "constraint_stage": "",
    })

    # ------------------------------------------------------------------
    # 3. onemotoring.lta.gov.sg reachability
    # ------------------------------------------------------------------
    status, body, detail = http_probe(config.LTA_ONEMOTORING)
    lta_ok = status in (200, 301, 302, 307)
    if status is not None and status not in (200,):
        detail += f" (final status after redirects: {status})"
    record("onemotoring_lta_reachability", "pass" if lta_ok else "fail", detail)

    # ------------------------------------------------------------------
    # 4. Local PDF presence
    # ------------------------------------------------------------------
    for name, p in [
        ("consult_paper.pdf", config.DOC_CONSULT_PAPER),
        ("annex_b.pdf", config.DOC_ANNEX_B),
        ("annex_c.pdf", config.DOC_ANNEX_C),
        ("car_cost_aug2026.pdf", config.DOC_CAR_COST_AUG2026),
    ]:
        exists = os.path.isfile(p)
        size = os.path.getsize(p) if exists else 0
        ok = exists and size > 0
        record(f"local_pdf:{name}", "pass" if ok else "fail",
               f"path={p}; exists={exists}; bytes={size}")

    # ------------------------------------------------------------------
    # 5. Method-precedent documentation present (the repo is
    #    self-contained; no external prior-study directory is a
    #    runtime dependency)
    # ------------------------------------------------------------------
    mp = os.path.join(config.WORKSPACE_ROOT, "docs", "methodology_notes.md")
    ok = os.path.isfile(mp) and os.path.getsize(mp) > 0
    record("method_precedent_documented", "pass" if ok else "fail",
           f"path={mp}; exists={os.path.isfile(mp)}; "
           f"bytes={os.path.getsize(mp) if ok else 0}")

    # ------------------------------------------------------------------
    # Write constraint_report.csv
    # ------------------------------------------------------------------
    out = os.path.join(config.DIR_VERIFICATION, "constraint_report.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check", "status", "detail",
                                          "timestamp_utc", "constraint_stage"])
        w.writeheader()
        w.writerows(rows)
    fails = [r["check"] for r in rows if r["status"] == "fail"]
    print(f"\nWROTE {out}")
    print(f"total checks={len(rows)}; fail={len(fails)} {fails if fails else ''}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
