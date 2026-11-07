"""일회성: 옛 시리즈 연령계층 표 전체 데이터 + 메타 → data/household/."""
import json, os, pathlib, urllib.parse, urllib.request, time

KEY = os.environ["KOSIS_API_KEY"]
OUT = pathlib.Path("data/household"); OUT.mkdir(parents=True, exist_ok=True)
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

TABLES = [("DT_1HDBA06", "2012", "2017"), ("DT_1HDCA06_HF", "2010", "2011"), ("DT_1HDALF06", "2011", "2024")]
for tbl, s, e in TABLES:
    for typ in ["OBJ", "ITM"]:
        json.dump(get(META, method="getMeta", type=typ, orgId="101", tblId=tbl),
                  open(OUT / f"meta_{tbl}_{typ}.json", "w"), ensure_ascii=False, indent=1)
    res = get(DATA, method="getList", orgId="101", tblId=tbl, itmId="ALL", objL1="ALL", objL2="ALL",
              objL3="ALL", prdSe="Y", startPrdDe=s, endPrdDe=e)
    json.dump(res, open(OUT / f"data_{tbl}.json", "w"), ensure_ascii=False)
print("ok")
