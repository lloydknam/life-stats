"""후보 통계표의 구조(항목·분류)를 조회해 data/table_meta.json 에 저장.
indicators.json 의 itmId / 분류 필터를 정확히 채우기 위한 사전 조사용.

사용: KOSIS_API_KEY=키 python scripts/probe_tables.py
"""
import json, os, sys, time, pathlib, urllib.parse, urllib.request

KEY = os.environ.get("KOSIS_API_KEY") or sys.exit("KOSIS_API_KEY 필요")
ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_TABLES = int(os.environ.get("MAX_TABLES", "90"))

FIXED = [
    ("101", "DT_1B34E13"), ("101", "DT_1ES3A03_A01S"), ("101", "DT_1ES3A01S"),
    ("101", "DT_1B81A23"), ("101", "INH_1B81A17"), ("101", "DT_1YL20921"),
    ("101", "DT_1YL202004"), ("133", "DT_133001N_4214"), ("101", "DT_1MH2090"),
    ("101", "DT_1C96"), ("101", "INH_1C96_04"),
]


def get(url):
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = str(e)
            time.sleep(1.5 * (a + 1))
    return {"err": "exc", "errMsg": err}


def meta(org, tbl, typ):
    q = urllib.parse.urlencode({"method": "getMeta", "apiKey": KEY, "format": "json", "jsonVD": "Y",
                                "type": typ, "orgId": org, "tblId": tbl})
    return get("https://kosis.kr/openapi/statisticsData.do?" + q)


# 후보 파일에서 시군구 표 추가 (국가데이터처·국세청 등 전국 단위 기관 위주)
tables = list(FIXED)
cand = ROOT / "data" / "table_candidates.json"
if cand.exists():
    seen = set(tables)
    for rows in json.loads(cand.read_text(encoding="utf-8")).values():
        for x in rows:
            if "error" in x or not x.get("TBL_ID"):
                continue
            key = (x["ORG_ID"], x["TBL_ID"])
            nm = x.get("TBL_NM") or ""
            if key in seen or x["ORG_ID"] in ("203", "201") or not any(k in nm for k in ("시군구", "시·군·구", "시도/시/군/구")):
                continue
            seen.add(key)
            tables.append(key)

out = {}
for org, tbl in tables[:MAX_TABLES]:
    itm = meta(org, tbl, "ITM")
    obj = meta(org, tbl, "OBJ")
    entry = {"orgId": org}
    if isinstance(itm, list):
        entry["items"] = [{"ITM_ID": r.get("ITM_ID"), "ITM_NM": r.get("ITM_NM"), "UNIT_NM": r.get("UNIT_NM")} for r in itm][:60]
    else:
        entry["items_err"] = itm
    if isinstance(obj, list):
        grp = {}
        for r in obj:
            g = grp.setdefault(r.get("OBJ_ID"), {"OBJ_NM": r.get("OBJ_NM"), "n": 0, "sample": []})
            g["n"] += 1
            if len(g["sample"]) < 12:
                g["sample"].append(f'{r.get("ITM_ID")}:{r.get("ITM_NM")}')
        entry["objs"] = grp
    else:
        entry["objs_err"] = obj
    out[tbl] = entry
    time.sleep(0.2)

(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "table_meta.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("tables", len(out))
