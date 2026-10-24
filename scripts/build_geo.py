"""시군구 경계(통계청 2018, southkorea-maps) → 단순화한 GeoJSON.  결과: data/geo_sigungu.json, data/geo_sido.json
일반구는 시로 합치고, 지역 키는 data.json 과 같은 '시도|이름'.
사용: pip install shapely; python scripts/build_geo.py path/to/skorea-municipalities-2018-geo.json
"""
import json, re, sys, pathlib
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parent.parent
SIDO = {"11": "서울", "21": "부산", "22": "대구", "23": "인천", "24": "광주", "25": "대전", "26": "울산",
        "29": "세종", "31": "경기", "32": "강원", "33": "충북", "34": "충남", "35": "전북", "36": "전남",
        "37": "경북", "38": "경남", "39": "제주"}
src = json.load(open(sys.argv[1], encoding="utf-8"))
groups, sidos = {}, {}
for f in src["features"]:
    code, name = f["properties"]["code"], f["properties"]["name"]
    sido = SIDO[code[:2]]
    m = re.match(r"^(.+시)(.+구)$", name)
    if m:
        name = m.group(1)
    # 2018 → 현재 행정구역: 군위군 경북→대구, 세종시→세종, 인천 남구→미추홀구
    if (sido, name) == ("경북", "군위군"):
        sido = "대구"
    elif (sido, name) == ("세종", "세종시"):
        name = "세종"
    elif (sido, name) == ("인천", "남구"):
        name = "미추홀구"
    g = shape(f["geometry"]).buffer(0)
    groups.setdefault((sido, name), []).append(g)
    sidos.setdefault(sido, []).append(g)


def fc(items, tol):
    feats = []
    for key, gs in items:
        g = unary_union([x.buffer(0.002) for x in gs]).buffer(-0.002).simplify(tol, preserve_topology=True)
        m = mapping(g)
        m["coordinates"] = json.loads(json.dumps(m["coordinates"]), parse_float=lambda x: round(float(x), 3))
        feats.append({"type": "Feature", "properties": {"k": key}, "geometry": m})
    return {"type": "FeatureCollection", "features": feats}


sg = fc([(f"{s}|{n}", gs) for (s, n), gs in groups.items()], 0.004)
sd = fc(list(sidos.items()), 0.02)
for fn, d in (("geo_sigungu.json", sg), ("geo_sido.json", sd)):
    p = ROOT / "data" / fn
    p.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(fn, len(d["features"]), p.stat().st_size // 1024, "KB")
