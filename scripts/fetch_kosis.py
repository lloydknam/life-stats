"""KOSIS OpenAPI 수집기: scripts/indicators.json → data/data.json (광역·기초 분리).

사용:  KOSIS_API_KEY=키 python scripts/fetch_kosis.py

표마다 지역 코드 체계가 달라(통계청 11010 / 행안부 11110 / 국세청 A0101) 코드가 아니라
(시도 약칭, 지역명)으로 지역을 식별한다. 시 아래 일반구는 제외해 시·군·구 기준으로 맞춘다.

지표 필드(indicators.json):
  id, name, unit, higherIsBetter, source, note
  orgId, tblId, itmId(없으면 ALL), objL1~objL4, prdSe(없으면 Y→H→Q→M 순 시도), newEstPrdCnt
    objLn 값에 {"resolve": {"obj": "A", "name": "자살"}} 를 쓰면 메타에서 항목 코드를 찾아 넣는다
  regionDim: 지역 분류의 순번(기본 1) → 응답의 C{n}, C{n}_NM
  sidoCodeLen / sigunguCodeLen: 지역 코드 길이(기본 2 / 5, 없으면 0)
  filters / exclude: 응답 행 필터. 값 "re:정규식", "~부분문자열", 그 외는 일치
  ratio: {"num": {...질의 덮어쓰기...}, "den": {...}, "scale": 100}  → 지역별 num/den*scale
  shareOf: {"dim": 3, "numRegex": "...", "totalName": "계", "scale": 100} → 분류 n의 이름이 정규식에 맞는 합 ÷ 총계
  perPop: {"scale": 1000}  → 지역별 값 ÷ 주민등록인구(DT_1B040M5_1 총계) × scale  (표가 서로 달라도 (시도,지역명)으로 맞춘다)
"""
import json, os, re, sys, time, datetime, pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "scripts" / "indicators.json").read_text(encoding="utf-8"))
KEY = os.environ.get("KOSIS_API_KEY") or sys.exit("KOSIS_API_KEY 환경변수가 필요합니다.")

SIDO_ORDER = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원",
              "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
SIDO_STAT = {"11": "서울", "21": "부산", "22": "대구", "23": "인천", "24": "광주", "25": "대전",
             "26": "울산", "29": "세종", "31": "경기", "32": "강원", "33": "충북", "34": "충남",
             "35": "전북", "36": "전남", "37": "경북", "38": "경남", "39": "제주"}
SHORT = [("서울", "서울"), ("부산", "부산"), ("대구", "대구"), ("인천", "인천"), ("광주", "광주"),
         ("대전", "대전"), ("울산", "울산"), ("세종", "세종"), ("경기", "경기"), ("강원", "강원"),
         ("충청북", "충북"), ("충북", "충북"), ("충청남", "충남"), ("충남", "충남"),
         ("전라북", "전북"), ("전북", "전북"), ("전라남", "전남"), ("전남", "전남"),
         ("경상북", "경북"), ("경북", "경북"), ("경상남", "경남"), ("경남", "경남"), ("제주", "제주")]
DATA_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
META_URL = "https://kosis.kr/openapi/statisticsData.do"


def short_sido(name):
    n = (name or "").replace(" ", "")
    for k, v in SHORT:
        if n.startswith(k):
            return v
    return None


def http(url):
    err = ""
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            err = str(e)
            time.sleep(2 * (a + 1))
    return {"err": "exc", "errMsg": err}


def resolve(ind, spec):
    q = urllib.parse.urlencode({"method": "getMeta", "apiKey": KEY, "format": "json", "jsonVD": "Y",
                                "type": "ITM", "orgId": ind["orgId"], "tblId": ind["tblId"]})
    rows = http(META_URL + "?" + q)
    if isinstance(rows, list):
        for r in rows:
            if r.get("OBJ_ID") == spec["obj"] and spec["name"] in (r.get("ITM_NM") or ""):
                return r["ITM_ID"]
    return None


def query(ind, over=None):
    """질의 1회. prdSe 가 틀리면 Y→H→Q→M 순으로 재시도."""
    cfg = {**ind, **(over or {})}
    q = {"method": "getList", "apiKey": KEY, "format": "json", "jsonVD": "Y",
         "orgId": cfg["orgId"], "tblId": cfg["tblId"], "itmId": cfg.get("itmId", "ALL"),
         "newEstPrdCnt": cfg.get("newEstPrdCnt", 1)}
    for i in range(1, 5):
        v = cfg.get(f"objL{i}")
        if v is None:
            if i == 1:
                v = "ALL"
            else:
                continue
        if isinstance(v, dict):
            code = resolve(cfg, v["resolve"])
            if code is None:
                return {"err": "resolve", "errMsg": f"항목 코드 못 찾음: {v}"}
            v = code
        q[f"objL{i}"] = v
    order = [cfg["prdSe"]] if cfg.get("prdSe") else ["Y", "H", "Q", "M", "F", "IR"]
    last = None
    for pd in order:
        q["prdSe"] = pd
        rows = http(DATA_URL + "?" + urllib.parse.urlencode(q))
        if isinstance(rows, list):
            return rows
        last = rows
    return last


def match(row, spec):
    for k, cond in (spec or {}).items():
        v = str(row.get(k, ""))
        if cond.startswith("re:"):
            if not re.search(cond[3:], v):
                return False
        elif cond.startswith("~"):
            if cond[1:] not in v:
                return False
        elif v != cond:
            return False
    return True


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


def prepare(ind):
    """질의·가공을 거쳐 (code, name, DT, period, unit) 행 목록을 만든다."""
    rd = ind.get("regionDim", 1)
    cf, nf = f"C{rd}", f"C{rd}_NM"
    if "ratio" in ind:
        rt = ind["ratio"]
        a, b = query(ind, rt["num"]), query(ind, rt["den"])
        for x in (a, b):
            if isinstance(x, dict):
                return x
        den = {r[cf]: num(r.get("DT")) for r in b if match(r, ind.get("filters"))}
        out = []
        for r in a:
            if not match(r, ind.get("filters")):
                continue
            n, d = num(r.get("DT")), den.get(r[cf])
            if n is None and rt.get("nullAsZero") and d:
                n = 0.0  # KOSIS의 '-'(해당 없음)를 0으로 본다
            if n is None or not d:
                continue
            out.append({"code": r[cf], "name": r.get(nf, ""), "v": n / d * rt.get("scale", 1),
                        "per": r.get("PRD_DE"), "unit": "", "n": n, "d": d, "scale": rt.get("scale", 1)})
        return out
    rows = query(ind)
    if isinstance(rows, dict):
        return rows
    if "shareOf" in ind:
        so = ind["shareOf"]
        d = f"C{so['dim']}_NM"
        rx = re.compile(so["numRegex"])
        agg = {}
        for r in rows:
            if not match(r, ind.get("filters")):
                continue
            v = num(r.get("DT"))
            if v is None:
                continue
            g = agg.setdefault(r[cf], {"name": r.get(nf, ""), "n": 0.0, "t": None, "per": r.get("PRD_DE")})
            nm = (r.get(d) or "").strip()
            if nm == so.get("totalName", "계"):
                g["t"] = v
            elif rx.search(nm):
                g["n"] += v
        return [{"code": c, "name": g["name"], "v": g["n"] / g["t"] * so.get("scale", 100),
                 "per": g["per"], "unit": "%"} for c, g in agg.items() if g["t"]]
    out = []
    for r in rows:
        if not match(r, ind.get("filters")) or match(r, ind.get("exclude")) and ind.get("exclude"):
            continue
        v = num(r.get("DT"))
        if v is None:
            continue
        out.append({"code": r.get(cf, ""), "name": r.get(nf, ""), "v": v,
                    "per": r.get("PRD_DE"), "unit": r.get("UNIT_NM") or ""})
    return out


def split_levels(rows, ind, canon_codes=None):
    sl, gl = ind.get("sidoCodeLen", 2), ind.get("sigunguCodeLen", 5)
    sidomap, sd = {}, {}
    for r in rows:
        if sl and len(r["code"]) == sl and r["code"] != "0" * sl:
            s = short_sido(r["name"]) or SIDO_STAT.get(r["code"])
            if s:
                sidomap[r["code"]] = s
                sd[s] = r["v"]
    cand = [r for r in rows if gl and len(r["code"]) == gl and not r["code"].startswith("0" * gl)]
    codes = {r["code"] for r in cand}
    # 시 행이 없고 일반구만 있는 표: 기준 목록(canon)에 시가 있으면 구의 분자·분모를 합산해 시 값을 만든다
    kids, skip = {}, set()
    if gl == 5 and canon_codes:
        for r in cand:
            c = r["code"]
            par = c[:-1] + "0"
            if c.isdigit() and c[-1] != "0" and par not in codes and par in canon_codes and "n" in r:
                kids.setdefault(par, []).append(r)
                skip.add(c)
    sg, cmap = {}, {}
    for par, ks in kids.items():
        d = sum(k["d"] for k in ks)
        if d:
            sg[canon_codes[par]] = sum(k["n"] for k in ks) / d * ks[0]["scale"]
            cmap[canon_codes[par]] = par
    for r in cand:
        c = r["code"]
        if c in skip:
            continue
        # 일반구(시 아래 구) 제외: 통계청·행안부식 숫자 5자리 코드(시 31010 → 구 31011)에만 적용.
        # 4자리 순번형(1101…)·국세청식(A0101…)은 순번이라 이 규칙이 맞지 않는다.
        if gl == 5 and c.isdigit() and c[:-1] + "0" in codes and c[-1] != "0":
            continue
        sido = sidomap.get(c[:sl]) if sl else None
        sido = sido or SIDO_STAT.get(c[:2]) or short_sido(r["name"].split(" ")[0])
        if not sido:
            continue
        name = r["name"].strip()
        parts = name.split(" ")
        if len(parts) > 1 and short_sido(parts[0]):
            name = " ".join(parts[1:])
        if short_sido(name) == "세종" and "세종" in name:
            name = "세종"
        sg[(sido, name)] = r["v"]
        cmap[(sido, name)] = c
    return sd, sg, cmap


# 기준 시·군·구 목록(229): 합계출산율 표에서 가져온다. 다른 표는 이 목록에 있는 지역만 사용.
_bi = next(i for t in CFG["themes"] for i in t["indicators"] if i["id"] == "birth")
_rows = prepare(_bi)
CANON_CODES, CANON_KEYS = {}, set()
if isinstance(_rows, list):
    _sd, _sg, _cm = split_levels(_rows, _bi)
    CANON_KEYS = set(_sg.keys())
    CANON_CODES = {c: k for k, c in _cm.items()}

# 인구(분모) — 주민등록연앙인구 총계. perPop 지표가 공통으로 쓴다.
POP = {}
_ag = next(i for t in CFG["themes"] for i in t["indicators"] if i["id"] == "aging")
_pi = {k: v for k, v in _ag.items() if k != "shareOf"}
_pi["filters"] = {"C3_NM": "계"}
_prow = prepare(_pi)
if isinstance(_prow, list):
    _psd, _psg, _ = split_levels(_prow, _pi, CANON_CODES)
    POP = {"sd": _psd, "sg": {k: v for k, v in _psg.items() if k in CANON_KEYS}}

regions, rindex = [], {}
values, sido_values, themes, report = {}, {}, [], []

for theme in CFG["themes"]:
    items = []
    for ind in theme["indicators"]:
        rows = prepare(ind)
        if isinstance(rows, dict):
            report.append(f'SKIP {ind["id"]}: {rows.get("errMsg")}')
            continue
        sd, sg, _ = split_levels(rows, ind, CANON_CODES)
        if CANON_KEYS:
            sg = {k: v for k, v in sg.items() if k in CANON_KEYS}
        if "perPop" in ind:
            if not POP:
                report.append(f'SKIP {ind["id"]}: 인구 분모 없음')
                continue
            k = ind["perPop"].get("scale", 1)
            sd = {a: v / POP["sd"][a] * k for a, v in sd.items() if POP["sd"].get(a)}
            sg = {a: v / POP["sg"][a] * k for a, v in sg.items() if POP["sg"].get(a)}
        if not sd and not sg:
            report.append(f'EMPTY {ind["id"]}: rows={len(rows)} sample={[r["code"]+":"+r["name"] for r in rows[:3]]}')
            continue
        gv = {}
        for (sido, name), v in sg.items():
            key = f"{sido}|{name}"
            if key not in rindex:
                rindex[key] = True
                regions.append({"code": key, "sido": sido, "name": name})
            gv[key] = v
        values[ind["id"]] = gv
        sido_values[ind["id"]] = sd
        per = max((r["per"] for r in rows if r.get("per")), default=None)
        unit = ind.get("unit") or next((r["unit"] for r in rows if r.get("unit")), "")
        items.append({"id": ind["id"], "name": ind["name"], "unit": unit,
                      "higherIsBetter": ind["higherIsBetter"], "source": ind.get("source", "KOSIS"),
                      "yearSido": per if sd else None, "yearSigungu": per if sg else None,
                      "note": ind.get("note", "")})
        report.append(f'OK {ind["id"]}: 시도 {len(sd)}, 시군구 {len(sg)}, {per}')
        time.sleep(0.3)
    if items:
        themes.append({"id": theme["id"], "name": theme["name"], "indicators": items})

out = {"meta": {"isSample": False, "updated": datetime.date.today().isoformat()},
       "themes": themes, "sidos": SIDO_ORDER, "regions": regions,
       "values": values, "sidoValues": sido_values}
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "data.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
(ROOT / "data" / "fetch_report.txt").write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))
print("regions", len(regions), "indicators", len(values))
