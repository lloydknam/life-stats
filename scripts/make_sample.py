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

# 분야(KOSIS 대분류 이름) → 지표. (id, 이름, 단위, 높을수록 좋은가, 시군구 범위, 시도 범위, 비고, 0 비중)
THEMES = [
    ("pop", "인구", [
        ("aging", "고령인구 비율", "%", False, (10, 45), (14, 30), "", 0),
        ("birth", "합계출산율", "명", True, (0.5, 1.4), (0.55, 1.0), "", 0),
        ("single_hh", "1인 가구 비율", "%", False, (20, 50), (28, 40), "", 0),
        ("foreign", "외국인 주민 비율", "%", True, (0.3, 9), (1, 5), "", 0),
    ]),
    ("health", "보건", [
        ("obgyn", "인구 10만 명당 산부인과 전문의", "명", True, (3, 55), (6, 18), "전문의 0명인 지역이 다수", 0.15),
        ("suicide", "자살률", "인구 10만 명당", False, (12, 45), (18, 32), "", 0),
        ("life_exp", "기대수명", "세", True, (80, 87), (82, 85.5), "", 0),
        ("beds", "인구 천 명당 병상 수", "개", True, (2, 40), (8, 20), "", 0),
    ]),
    ("welfare", "복지", [
        ("basic_living", "기초생활수급자 비율", "%", False, (1.5, 9), (2.5, 6.5), "", 0),
        ("basic_pension", "기초연금 수급률", "%", False, (40, 90), (55, 80), "", 0),
        ("childcare", "아동 천 명당 어린이집", "개", True, (6, 22), (9, 16), "", 0),
    ]),
    ("labor", "노동", [
        ("employment", "고용률", "%", True, (52, 72), (58, 68), "", 0),
        ("unemployment", "실업률", "%", False, (1, 6), (2, 4.5), "", 0),
        ("youth_emp", "청년(15~29세) 고용률", "%", True, (30, 60), (38, 52), "", 0),
        ("lfp", "경제활동참가율", "%", True, (55, 75), (60, 70), "", 0),
    ]),
    ("income", "소득·소비·자산", [
        ("income", "1인당 개인소득", "만원", True, (2200, 4800), (2800, 4000), "", 0),
        ("wage", "근로자 평균 연봉", "만원", True, (2800, 6000), (3500, 5200), "", 0),
    ]),
    ("housing", "주거", [
        ("price_income", "소득 대비 주택가격(PIR)", "배", False, (3, 18), (5, 14), "", 0),
        ("own_rate", "자가보유율", "%", True, (35, 75), (45, 65), "", 0),
        ("no_house", "무주택 가구 비율", "%", False, (30, 65), (38, 55), "", 0),
        ("semi_base", "반지하·옥탑 거주 가구 비율", "%", False, (0.1, 8), (0.3, 4), "", 0),
        ("old_house", "노후주택 비율", "%", False, (10, 70), (20, 55), "", 0),
    ]),
    ("edu", "교육·훈련", [
        ("univ_rate", "대학 진학률", "%", True, (55, 82), (62, 78), "", 0),
        ("class_size", "학급당 학생 수", "명", False, (10, 28), (16, 25), "", 0),
        ("academy", "인구 천 명당 학원", "개", True, (1, 9), (2, 7), "", 0),
    ]),
    ("culture", "문화·여가", [
        ("library", "인구 10만 명당 도서관", "개", True, (1, 9), (2, 6), "", 0),
        ("culture_fac", "인구 10만 명당 문화기반시설", "개", True, (2, 20), (4, 14), "", 0),
        ("sports_fac", "인구 만 명당 공공체육시설", "개", True, (1, 12), (3, 8), "", 0),
    ]),
    ("safety", "범죄·안전", [
        ("crime", "범죄 발생률", "인구 10만 명당", False, (800, 3500), (1500, 2800), "", 0),
        ("traffic_death", "교통사고 사망자", "인구 10만 명당", False, (2, 15), (4, 10), "", 0),
        ("fire", "화재 사망·부상자", "인구 10만 명당", False, (3, 30), (8, 20), "", 0),
    ]),
    ("economy", "경제일반·경기", [
        ("grdp", "1인당 지역내총생산", "만원", True, (2200, 9000), (3000, 6500), "", 0),
        ("biz_density", "인구 천 명당 사업체", "개", True, (55, 130), (70, 110), "", 0),
        ("workers", "사업체 종사자 수 증가율", "%", True, (-5, 8), (-1, 4), "", 0),
    ]),
    ("fiscal", "정부·재정", [
        ("fiscal_indep", "재정자립도", "%", True, (8, 70), (20, 70), "", 0),
    ]),
    ("env", "환경", [
        ("park_area", "1인당 도시공원 면적", "㎡", True, (3, 25), (5, 20), "", 0),
        ("pm25", "초미세먼지 농도", "㎍/㎥", False, (12, 28), (15, 25), "", 0),
    ]),
    ("transport", "교통·물류", [
        ("bus_access", "대중교통 접근성", "점", True, (30, 95), (50, 90), "", 0),
        ("cars", "가구당 자동차 등록 대수", "대", False, (0.6, 1.6), (0.8, 1.3), "", 0),
    ]),
]

regions = []
for sido, names in REGIONS.items():
    for n in names:
        regions.append({"code": f"{sido}-{n}", "sido": sido, "name": n})
sidos = list(REGIONS.keys())


def digits(hi):
    return 2 if hi < 5 else (1 if hi < 100 else 0)


themes, values, sido_values = [], {}, {}
for tid, tname, inds in THEMES:
    items = []
    for iid, name, unit, hib, (lo, hi), (slo, shi), note, zero in inds:
        items.append({"id": iid, "name": name, "unit": unit, "higherIsBetter": hib,
                      "source": "샘플(난수)", "yearSido": "2025", "yearSigungu": "2025", "note": note})
        d = digits(hi)
        v = {}
        for r in regions:
            v[r["code"]] = 0 if random.random() < zero else round(random.uniform(lo, hi), d)
        values[iid] = v
        sido_values[iid] = {s: round(random.uniform(slo, shi), d) for s in sidos}
    themes.append({"id": tid, "name": tname, "indicators": items})

out = {"meta": {"isSample": True, "updated": datetime.date.today().isoformat(),
                "note": "샘플 데이터(난수). 실제 통계 아님"},
       "themes": themes, "sidos": sidos, "regions": regions,
       "values": values, "sidoValues": sido_values}

p = pathlib.Path(__file__).resolve().parent.parent / "data" / "data.json"
p.parent.mkdir(exist_ok=True)
p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", p, len(regions), "regions,", len(sidos), "sidos")
