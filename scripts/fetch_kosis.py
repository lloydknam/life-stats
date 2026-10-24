"""KOSIS OpenAPI 수집기: scripts/indicators.json 에 적힌 통계표를 받아 data/data.json 생성.

사용:  KOSIS_API_KEY=발급키 python scripts/fetch_kosis.py
- indicators.json 의 orgId/tblId/itmId/objL1 값은 KOSIS '통계표 > OpenAPI 활용 > 자료등록(URL생성)'
  화면에서 확인한 값을 그대로 넣으세요. (placeholder 값은 실제 코드가 아님)
- 시군구 코드(C1)는 KOSIS 행정구역 코드. 표기 이름은 C1_NM 사용.
"""
import json, os, sys, time, datetime, pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "scripts" / "indicators.json").read_text(encoding="utf-8"))
KEY = os.environ.get("KOSIS_API_KEY")
if not KEY:
    sys.exit("KOSIS_API_KEY 환경변수가 필요합니다.")

# 시도 코드 앞 2자리 → 시도명 (KOSIS 행정구역 분류 기준; 실제 응답으로 한 번 검증 필요)
SIDO = {"11": "서울", "21": "부산", "22": "대구", "23": "인천", "24": "광주", "25": "대전",
        "26": "울산", "29": "세종", "31": "경기", "32": "강원", "33": "충북", "34": "충남",
        "35": "전북", "36": "전남", "37": "경북", "38": "경남", "39": "제주"}

BASE = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


def fetch(ind):
    q = {
        "method": "getList", "apiKey": KEY, "format": "json", "jsonVD": "Y",
        "orgId": ind["orgId"], "tblId": ind["tblId"], "itmId": ind["itmId"],
        "objL1": ind.get("objL1", "ALL"), "prdSe": ind.get("prdSe", "Y"),
        "newEstPrdCnt": ind.get("newEstPrdCnt", 1),
    }
    for k in ("objL2", "objL3"):
        if k in ind:
            q[k] = ind[k]
    url = BASE + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


regions, seen, values, themes = [], {}, {}, []
for theme in CFG["themes"]:
    items = []
    for ind in theme["indicators"]:
        rows = fetch(ind)
        if isinstance(rows, dict):  # 오류 응답 {"err":..., "errMsg":...}
            print("SKIP", ind["id"], rows.get("errMsg"))
            continue
        vals, year = {}, None
        for r in rows:
            name = r["C1_NM"]
            code = r["C1"]
            if r.get("DT") in (None, "", "-"):
                continue
            if code not in seen:
                seen[code] = True
                regions.append({"code": code, "sido": SIDO.get(code[:2], code[:2]), "name": name})
            vals[code] = float(r["DT"])
            year = r.get("PRD_DE", year)
        values[ind["id"]] = vals
        items.append({"id": ind["id"], "name": ind["name"], "unit": ind["unit"],
                      "higherIsBetter": ind["higherIsBetter"], "source": ind.get("source", "KOSIS"),
                      "year": year})
        time.sleep(0.3)
    themes.append({"id": theme["id"], "name": theme["name"], "indicators": items})

out = {"meta": {"isSample": False, "updated": datetime.date.today().isoformat()},
       "themes": themes, "regions": regions, "values": values}
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "data.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print("regions", len(regions), "indicators", len(values))
