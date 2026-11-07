"""일회성: 70대 구분 가능 여부 — 가구특성별 자산·부채(DT_1HDAAD01) 등 연령 분류 덤프 → data/probe70/."""
import json, os, pathlib, urllib.parse, urllib.request, time
KEY = os.environ["KOSIS_API_KEY"]
OUT = pathlib.Path("data/probe70"); OUT.mkdir(parents=True, exist_ok=True)
META = "https://kosis.kr/openapi/statisticsData.do"
DATA = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
def get(base, **q):
    q.update({"apiKey": KEY, "format": "json", "jsonVD": "Y"})
    url = base + "?" + urllib.parse.urlencode(q)
    err = ""
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = str(e); time.sleep(2 * (a + 1))
    return {"err": err}
for tbl in ["DT_1HDAAD01", "DT_1HDAAA16"]:
    for typ in ["OBJ", "ITM", "PRD"]:
        json.dump(get(META, method="getMeta", type=typ, orgId="101", tblId=tbl),
                  open(OUT / f"meta_{tbl}_{typ}.json", "w"), ensure_ascii=False, indent=1)
    res = get(DATA, method="getList", orgId="101", tblId=tbl, itmId="ALL", objL1="ALL", objL2="ALL",
              objL3="ALL", prdSe="Y", startPrdDe="2017", endPrdDe="2025")
    json.dump(res, open(OUT / f"data_{tbl}.json", "w"), ensure_ascii=False)
print("ok")
