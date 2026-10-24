"""KOSIS 통계검색 API로 지표별 통계표 후보를 찾아 data/table_candidates.json 에 저장.

사용: KOSIS_API_KEY=키 python scripts/find_tables.py
결과의 ORG_ID / TBL_ID / TBL_NM 을 보고 indicators.json 을 채웁니다.
"""
import json, os, sys, pathlib, urllib.parse, urllib.request

KEY = os.environ.get("KOSIS_API_KEY") or sys.exit("KOSIS_API_KEY 필요")
ROOT = pathlib.Path(__file__).resolve().parent.parent

KEYWORDS = {
    "suicide": ["시군구 자살률", "사망원인 시군구 자살", "자살 사망률 시도 시군구"],
    "employment": ["시군구 고용률", "지역별고용조사 시군구 고용률"],
    "aging": ["시군구 고령인구비율", "주민등록 연령별 인구 시군구"],
    "fiscal_indep": ["재정자립도 시군구"],
    "birth": ["합계출산율 시군구"],
    "basic_living": ["국민기초생활수급자 시군구"],
}

out = {}
for ind, kws in KEYWORDS.items():
    out[ind] = []
    for kw in kws:
        q = urllib.parse.urlencode({
            "method": "getList", "apiKey": KEY, "format": "json", "jsonVD": "Y",
            "vwCd": "MT_ZTITLE", "searchNm": kw, "resultCount": 15, "startCount": 1})
        url = "https://kosis.kr/openapi/statisticsSearch.do?" + q
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                rows = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            out[ind].append({"keyword": kw, "error": str(e)})
            continue
        if isinstance(rows, dict):
            out[ind].append({"keyword": kw, "error": rows})
            continue
        for x in rows:
            out[ind].append({"keyword": kw, "ORG_ID": x.get("ORG_ID"), "TBL_ID": x.get("TBL_ID"),
                             "TBL_NM": x.get("TBL_NM"), "ORG_NM": x.get("ORG_NM"),
                             "STRT_PRD_DE": x.get("STRT_PRD_DE"), "END_PRD_DE": x.get("END_PRD_DE")})

(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "table_candidates.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print({k: len(v) for k, v in out.items()})
