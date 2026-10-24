"""KOSIS 통계목록(주제별 MT_ZTITLE)을 전부 훑어 '시군구' 단위 통계표를 수집.

결과: data/kosis_sigungu_tables.json  (ORG_ID, TBL_ID, TBL_NM, 경로, 기간)
호출 수 상한(MAX_CALLS)으로 쿼터를 보호하고, 중단돼도 지금까지 결과를 저장한다.
"""
import json, os, sys, time, pathlib, urllib.parse, urllib.request

KEY = os.environ.get("KOSIS_API_KEY") or sys.exit("KOSIS_API_KEY 필요")
ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_CALLS = int(os.environ.get("MAX_CALLS", "6000"))
PATTERNS = ("시군구", "시·군·구", "시/군/구", "시도/시/군/구", "시군", "읍면동")

calls = 0


def call(parent):
    global calls
    calls += 1
    q = urllib.parse.urlencode({
        "method": "getList", "apiKey": KEY, "format": "json", "jsonVD": "Y",
        "vwCd": "MT_ZTITLE", "parentListId": parent})
    url = "https://kosis.kr/openapi/statisticsList.do?" + q
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return []


found, seen_tbl = [], set()
# 루트("")가 비어 올 수 있어 최상위 분류 코드 A~Z를 함께 시드로 사용
queue = [("", "")] + [(c, c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
errors = []
while queue and calls < MAX_CALLS:
    parent, path = queue.pop(0)
    rows = call(parent)
    if not isinstance(rows, list):
        if len(errors) < 5:
            errors.append({"parent": parent, "resp": rows})
        continue
    for x in rows:
        nm = x.get("LIST_NM") or x.get("TBL_NM") or ""
        if x.get("TBL_ID"):
            key = (x.get("ORG_ID"), x["TBL_ID"])
            if key in seen_tbl:
                continue
            seen_tbl.add(key)
            tnm = x.get("TBL_NM") or nm
            if any(p in tnm for p in PATTERNS):
                found.append({"ORG_ID": x.get("ORG_ID"), "TBL_ID": x["TBL_ID"], "TBL_NM": tnm,
                              "ORG_NM": x.get("ORG_NM"), "PATH": path})
        elif x.get("LIST_ID"):
            queue.append((x["LIST_ID"], f"{path}/{nm}" if path else nm))
    time.sleep(0.1)

(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "kosis_sigungu_tables.json").write_text(
    json.dumps({"calls": calls, "remaining_folders": len(queue), "errors": errors, "tables": found},
               ensure_ascii=False, indent=1), encoding="utf-8")
print("calls", calls, "tables", len(found), "remaining", len(queue))
