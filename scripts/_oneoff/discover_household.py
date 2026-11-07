"""일회성: 가계금융복지조사 표 탐색 + 메타 덤프 → out/ 에 원본 JSON 저장 (artifact로 업로드)."""
import json, os, pathlib, urllib.parse, urllib.request, time

KEY = os.environ["KOSIS_API_KEY"]
OUT = pathlib.Path("out"); OUT.mkdir(exist_ok=True)

def get(base, **q):
    q.update({"apiKey": KEY, "format": "json", "jsonVD": "Y"})
    url = base + "?" + urllib.parse.urlencode(q)
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = str(e); time.sleep(2 * (a + 1))
    return {"err": err}

SEARCH = "https://kosis.kr/openapi/statisticsSearch.do"
META = "https://kosis.kr/openapi/statisticsData.do"

hits = {}
for kw in ["가계금융복지조사", "가구주 연령 자산", "가구주 연령 소득", "가구 자산 부채 연령", "가계금융 복지 소득 연령별"]:
    res = get(SEARCH, method="getList", vwCd="MT_ZTITLE", searchNm=kw)
    hits[kw] = res
json.dump(hits, open(OUT / "search.json", "w"), ensure_ascii=False, indent=1)

# 알려진 후보 표의 메타(분류·항목·수록기간)
for tbl in ["DT_1HDAAD01"]:
    for typ in ["OBJ", "ITM", "PRD"]:
        if typ == "PRD":
            res = get(META, method="getMeta", type="PRD", orgId="101", tblId=tbl)
        else:
            res = get(META, method="getMeta", type=typ, orgId="101", tblId=tbl)
        json.dump(res, open(OUT / f"meta_{tbl}_{typ}.json", "w"), ensure_ascii=False, indent=1)
print("done", list(hits.keys()))
