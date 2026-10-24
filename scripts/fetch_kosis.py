"""KOSIS OpenAPI 수집기: scripts/indicators.json → data/data.json (광역·기초 분리).

사용:  KOSIS_API_KEY=키 python scripts/fetch_kosis.py

indicators.json 의 분야(themes) → 지표(indicators) 2단 구조.
지표 필드:
  id, name, unit, higherIsBetter, source, note(선택)
  orgId, tblId, itmId(없으면 ALL), objL1(기본 ALL), objL2/objL3(선택), prdSe(기본 Y)
  filters  : 행 필터. {"ITM_NM": "...", "C2_NM": "..."} 처럼 응답 필드가 일치하는 행만 사용
  sidoCodeLen / sigunguCodeLen : 행정구역 코드 길이(기본 2 / 5)
"""
import json, os, sys, time, datetime, pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "scripts" / "indicators.json").read_text(encoding="utf-8"))
KEY = os.environ.get("KOSIS_API_KEY") or sys.exit("KOSIS_API_KEY 환경변수가 필요합니다.")

SIDO = {"11": "서울", "21": "부산", "22": "대구", "23": "인천", "24": "광주", "25": "대전",
        "26": "울산", "29": "세종", "31": "경기", "32": "강원", "33": "충북", "34": "충남",
        "35": "전북", "36": "전남", "37": "경북", "38": "경남", "39": "제주"}
BASE = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


def fetch(ind):
    q = {"method": "getList", "apiKey": KEY, "format": "json", "jsonVD": "Y",
         "orgId": ind["orgId"], "tblId": ind["tblId"], "itmId": ind.get("itmId", "ALL"),
         "objL1": ind.get("objL1", "ALL"), "prdSe": ind.get("prdSe", "Y"),
         "newEstPrdCnt": ind.get("newEstPrdCnt", 1)}
    for k in ("objL2", "objL3", "objL4"):
        if k in ind:
            q[k] = ind[k]
    url = BASE + "?" + urllib.parse.urlencode(q)
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = str(e)
            time.sleep(2 * (a + 1))
    return {"err": "exc", "errMsg": err}


regions, seen = [], set()
values, sido_values, themes, report = {}, {}, [], []

for theme in CFG["themes"]:
    items = []
    for ind in theme["indicators"]:
        rows = fetch(ind)
        if isinstance(rows, dict):
            report.append(f'SKIP {ind["id"]}: {rows.get("errMsg")}')
            continue
        fl = ind.get("filters", {})
        sl, gl = ind.get("sidoCodeLen", 2), ind.get("sigunguCodeLen", 5)
        sg, sd, year = {}, {}, None
        for r in rows:
            if any(r.get(k) != v for k, v in fl.items()):
                continue
            dt = r.get("DT")
            if dt in (None, "", "-", "X"):
                continue
            try:
                val = float(str(dt).replace(",", ""))
            except ValueError:
                continue
            code = str(r.get("C1", ""))
            if code in ("", "00"):
                continue
            year = r.get("PRD_DE", year)
            if len(code) == sl:
                sd[SIDO.get(code, r.get("C1_NM", code))] = val
            elif len(code) == gl:
                if code not in seen:
                    seen.add(code)
                    regions.append({"code": code, "sido": SIDO.get(code[:2], code[:2]), "name": r.get("C1_NM", code)})
                sg[code] = val
        if not sg and not sd:
            report.append(f'EMPTY {ind["id"]} (filters={fl})')
            continue
        values[ind["id"]] = sg
        sido_values[ind["id"]] = sd
        unit = ind.get("unit") or next((r.get("UNIT_NM") for r in rows if r.get("UNIT_NM")), "")
        items.append({"id": ind["id"], "name": ind["name"], "unit": unit,
                      "higherIsBetter": ind["higherIsBetter"], "source": ind.get("source", "KOSIS"),
                      "yearSido": year if sd else None, "yearSigungu": year if sg else None,
                      "note": ind.get("note", "")})
        report.append(f'OK {ind["id"]}: sido {len(sd)}, sigungu {len(sg)}, {year}')
        time.sleep(0.3)
    if items:
        themes.append({"id": theme["id"], "name": theme["name"], "indicators": items})

out = {"meta": {"isSample": False, "updated": datetime.date.today().isoformat()},
       "themes": themes, "sidos": list(SIDO.values()), "regions": regions,
       "values": values, "sidoValues": sido_values}
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "data.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
(ROOT / "data" / "fetch_report.txt").write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))
print("regions", len(regions), "indicators", len(values))
