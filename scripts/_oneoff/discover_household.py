"""일회성: 가구주연령계층별(10세) 자산·부채·소득 표 메타 + 전체 데이터 덤프 → out/."""
import json, os, pathlib, urllib.parse, urllib.request, time

KEY = os.environ["KOSIS_API_KEY"]
OUT = pathlib.Path("out"); OUT.mkdir(exist_ok=True)

def get(base, **q):
    q.update({"apiKey": KEY, "format": "json", "jsonVD": "Y"})
    url = base + "?" + urllib.parse.urlencode(q)
    err = ""
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = str(e); time.sleep(2 * (a + 1))
    return {"err": err}

META = "https://kosis.kr/openapi/statisticsData.do"
DATA = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
TBL = "DT_1HDAAA06"

for typ in ["OBJ", "ITM", "PRD"]:
    res = get(META, method="getMeta", type=typ, orgId="101", tblId=TBL)
    json.dump(res, open(OUT / f"meta_{TBL}_{typ}.json", "w"), ensure_ascii=False, indent=1)

# 전체 데이터: 항목·분류 ALL, 연 단위 2017~2025
res = get(DATA, method="getList", orgId="101", tblId=TBL, itmId="ALL", objL1="ALL", objL2="ALL",
          objL3="ALL", prdSe="Y", startPrdDe="2017", endPrdDe="2025", newEstPrdCnt="")
json.dump(res, open(OUT / f"data_{TBL}_all.json", "w"), ensure_ascii=False, indent=1)
print("done")
