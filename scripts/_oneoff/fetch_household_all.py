"""일회성: 가계금융복지조사 연령계층 표 — 가용 연도 전부 + 옛 시리즈 탐색 → data/household/."""
import json, os, pathlib, urllib.parse, urllib.request, time

KEY = os.environ["KOSIS_API_KEY"]
OUT = pathlib.Path("data/household"); OUT.mkdir(parents=True, exist_ok=True)
META = "https://kosis.kr/openapi/statisticsData.do"
DATA = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
SEARCH = "https://kosis.kr/openapi/statisticsSearch.do"

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

# 1) 옛 시리즈 탐색: 키워드 검색 결과를 모두 저장
kws = ["가계금융복지조사", "가계금융 복지조사 연령", "가구주 연령계층별 자산", "가구주 연령계층별 소득",
       "가구 자산 부채 소득 현황", "가구주 연령별 자산", "가계금융조사", "가구 소득 자산 2012 2016"]
found = {}
for kw in kws:
    res = get(SEARCH, method="getList", vwCd="MT_ZTITLE", searchNm=kw)
    if isinstance(res, list):
        for r in res:
            found[(r.get("ORG_ID"), r.get("TBL_ID"))] = r
json.dump(list(found.values()), open(OUT / "search_all.json", "w"), ensure_ascii=False, indent=1)

# 2) 후보 표들의 기간 메타 (연령·자산·소득 관련 이름만)
cands = [(o, t, r.get("TBL_NM", "")) for (o, t), r in found.items()
         if any(k in r.get("TBL_NM", "") for k in ["연령", "자산", "가계", "가구주"]) and o]
periods = {}
for o, t, nm in cands[:60]:
    periods[f"{o}|{t}|{nm}"] = get(META, method="getMeta", type="PRD", orgId=o, tblId=t)
json.dump(periods, open(OUT / "candidate_periods.json", "w"), ensure_ascii=False, indent=1)

# 3) 주 표: 가능한 모든 기간(2000~2025) 요청 → 실제 응답 확인
for start in ["2000", "2012"]:
    res = get(DATA, method="getList", orgId="101", tblId="DT_1HDAAA06", itmId="ALL", objL1="ALL",
              objL2="ALL", objL3="ALL", prdSe="Y", startPrdDe=start, endPrdDe="2025")
    json.dump(res, open(OUT / f"DT_1HDAAA06_from{start}.json", "w"), ensure_ascii=False)
print("cands", len(cands), "found", len(found))
