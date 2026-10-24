"""샘플 데이터 생성기 — 실제 통계가 아니라 화면 확인용 난수입니다.
실제 데이터는 scripts/fetch_kosis.py 로 data/data.json 을 덮어씁니다."""
import json, random, datetime, pathlib

random.seed(2026)

REGIONS = {
    "서울": ["종로구", "중구", "용산구", "성동구", "강남구", "서초구", "송파구", "노원구", "관악구", "강서구"],
    "부산": ["해운대구", "수영구", "동래구", "사하구", "영도구", "기장군"],
    "대구": ["수성구", "달서구", "중구", "달성군"],
    "인천": ["연수구", "부평구", "계양구", "강화군", "옹진군"],
    "광주": ["북구", "서구", "광산구"],
    "대전": ["유성구", "서구", "중구"],
    "울산": ["남구", "울주군"],
    "세종": ["세종시"],
    "경기": ["수원시", "성남시", "고양시", "용인시", "화성시", "평택시", "양평군", "가평군", "연천군"],
    "강원": ["춘천시", "원주시", "강릉시", "태백시", "양구군", "정선군"],
    "충북": ["청주시", "충주시", "제천시", "단양군", "괴산군"],
    "충남": ["천안시", "아산시", "서산시", "당진시", "부여군", "청양군"],
    "전북": ["전주시", "익산시", "군산시", "남원시", "진안군", "임실군"],
    "전남": ["목포시", "여수시", "순천시", "나주시", "신안군", "고흥군", "곡성군"],
    "경북": ["포항시", "구미시", "경주시", "안동시", "영양군", "울릉군", "의성군"],
    "경남": ["창원시", "김해시", "진주시", "양산시", "거제시", "남해군", "합천군"],
    "제주": ["제주시", "서귀포시"],
}

# (id, 이름, 단위, 높을수록 좋은가, 범위, 출처 표시)
THEMES = [
    ("health", "건강·안전", [
        ("suicide", "자살률", "인구 10만명당", False, (12, 45)),
        ("crime", "범죄 발생률", "인구 10만명당", False, (800, 3500)),
        ("traffic_death", "교통사고 사망자", "인구 10만명당", False, (2, 15)),
        ("life_exp", "기대수명", "세", True, (80, 87)),
    ]),
    ("economy", "경제·일자리", [
        ("employment", "고용률", "%", True, (52, 72)),
        ("income", "1인당 개인소득", "만원", True, (2200, 4800)),
        ("fiscal_indep", "재정자립도", "%", True, (8, 70)),
        ("biz_density", "인구 천명당 사업체", "개", True, (55, 130)),
    ]),
    ("housing", "주거·교통", [
        ("price_income", "PIR(소득 대비 주택가격)", "배", False, (3, 18)),
        ("own_rate", "자가보유율", "%", True, (35, 75)),
        ("bus_access", "대중교통 접근성", "점", True, (30, 95)),
        ("park_area", "1인당 도시공원 면적", "㎡", True, (3, 25)),
    ]),
    ("edu_culture", "교육·문화", [
        ("univ_rate", "대학 진학률", "%", True, (55, 82)),
        ("library", "인구 10만명당 도서관", "개", True, (1, 9)),
        ("culture_fac", "인구 10만명당 문화기반시설", "개", True, (2, 20)),
    ]),
    ("welfare", "복지·인구", [
        ("aging", "고령인구 비율", "%", False, (10, 45)),
        ("birth", "합계출산율", "명", True, (0.5, 1.4)),
        ("basic_living", "기초생활수급자 비율", "%", False, (1.5, 9)),
        ("childcare", "아동 천명당 어린이집", "개", True, (6, 22)),
    ]),
]

regions = []
for sido, names in REGIONS.items():
    for n in names:
        regions.append({"code": f"{sido}-{n}", "sido": sido, "name": n})

themes, values = [], {}
for tid, tname, inds in THEMES:
    items = []
    for iid, name, unit, hib, (lo, hi) in inds:
        items.append({"id": iid, "name": name, "unit": unit, "higherIsBetter": hib,
                      "source": "샘플", "year": 2025})
        d = 2 if hi < 5 else (1 if hi < 100 else 0)
        values[iid] = {r["code"]: round(random.uniform(lo, hi), d) for r in regions}
    themes.append({"id": tid, "name": tname, "indicators": items})

out = {"meta": {"isSample": True, "updated": datetime.date.today().isoformat(),
                "note": "샘플 데이터(난수). 실제 통계 아님"},
       "themes": themes, "regions": regions, "values": values}

p = pathlib.Path(__file__).resolve().parent.parent / "data" / "data.json"
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", p, len(regions), "regions")
