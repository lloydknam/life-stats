"""KOSIS 통계검색 API로 지표별 통계표 후보를 찾아 data/table_candidates.json 에 저장.

사용: KOSIS_API_KEY=키 python scripts/find_tables.py
결과의 ORG_ID / TBL_ID / TBL_NM 을 보고 indicators.json 을 채웁니다.
"""
import json, os, sys, pathlib, urllib.parse, urllib.request

KEY = os.environ.get("KOSIS_API_KEY") or sys.exit("KOSIS_API_KEY 필요")
ROOT = pathlib.Path(__file__).resolve().parent.parent

KEYWORDS = {
    # 인구·가구
    "population": ["시군구 주민등록인구", "시군구 인구 이동 전입 전출"],
    "aging": ["시군구 고령인구비율", "주민등록 연령별 인구 시군구"],
    "single_household": ["시군구 1인가구 비율"],
    "foreigner": ["시군구 외국인 주민 등록"],
    "birth": ["합계출산율 시군구", "시군구 출생아수 조출생률"],
    "marriage": ["시군구 혼인 이혼 건수"],
    # 건강·안전
    "suicide": ["시군구 자살률", "사망원인 시군구 자살"],
    "life_exp": ["시군구 기대수명", "시군구 건강수명"],
    "mortality": ["시군구 사망률 사망원인"],
    "crime": ["시군구 범죄 발생 건수", "경찰서 관할 범죄"],
    "traffic": ["시군구 교통사고 사망자"],
    "fire": ["시군구 화재 발생 사망"],
    "smoking_drinking": ["지역사회건강조사 시군구 흡연율 음주율"],
    "hospital_beds": ["시군구 의료기관 병상수 의사수"],
    # 경제·일자리
    "employment": ["시군구 고용률", "지역별고용조사 시군구"],
    "unemployment": ["시군구 실업률"],
    "income": ["시군구 개인소득 지역소득", "시군구 근로소득 연말정산"],
    "grdp": ["시군구 지역내총생산 GRDP"],
    "fiscal_indep": ["재정자립도 시군구", "지방자치단체 재정자립도"],
    "business": ["시군구 사업체수 종사자수 전국사업체조사"],
    "self_employed": ["시군구 자영업자 폐업"],
    "wage": ["시군구 임금 근로자 평균임금"],
    # 주거·교통·환경
    "house_price": ["시군구 주택 매매가격 아파트"],
    "housing_own": ["시군구 자가보유율 주거실태"],
    "housing_supply": ["시군구 주택보급률 미분양"],
    "park": ["시군구 1인당 도시공원 면적"],
    "bus": ["시군구 대중교통 버스 지하철 이용"],
    "car": ["시군구 자동차 등록대수"],
    "air": ["시군구 대기오염 미세먼지"],
    # 교육·문화
    "school": ["시군구 학교수 학생수 학급당"],
    "univ_rate": ["시군구 대학 진학률 고등학교 졸업자"],
    "private_edu": ["시군구 사교육 학원수"],
    "library": ["시군구 공공도서관 수"],
    "culture": ["시군구 문화기반시설 공연장 박물관"],
    "sports": ["시군구 공공체육시설"],
    # 복지
    "basic_living": ["국민기초생활수급자 시군구"],
    "basic_pension": ["시군구 기초연금 수급자"],
    "childcare": ["시군구 어린이집 보육 아동수"],
    "elderly_care": ["시군구 노인복지시설 장기요양"],
    "disability": ["시군구 등록장애인"],
    # 이광재 의원 제시 지표 (우선순위)
    "semi_basement": ["반지하 옥탑 주택 시군구 인구주택총조사", "지하 옥상 거처 가구 시군구", "주택이외의 거처 지하"],
    "homeless_household": ["주택소유통계 시군구 무주택 가구", "무주택가구비율 시군구", "주택소유 가구 시군구"],
    "basic_living_rate": ["국민기초생활보장 수급률 시군구", "기초생활수급자 시군구 수급자수 인구"],
    "disposable_income": ["시군구 가계 총처분가능소득", "1인당 가계총처분가능소득", "지역소득 시군구 개인소득 가계"],
    "tfr_trend": ["인구동향조사 시군구 합계출산율"],
    # 2차 탐색 (신규 분야)
    "r2_basic_living": ["시군구별 국민기초생활보장 수급자 수", "기초생활보장 수급자 시군구 보건복지부", "시군구별 기초생활수급자 현황"],
    "r2_crime": ["경찰서별 범죄 발생 검거", "시군구별 5대범죄 발생", "범죄 발생 지역별 시군구 대검찰청"],
    "r2_traffic": ["시군구별 교통사고 발생 사망자 도로교통공단", "시군구 교통사고 사상자"],
    "r2_fire": ["시군구별 화재발생 소방청", "시군구 화재 인명피해"],
    "r2_medical": ["시군구별 의료기관 병상 의사 수 건강보험심사평가원", "시군구 인구 천명당 의사수", "시군구별 요양기관 현황"],
    "r2_school": ["시군구별 학교 수 학생 수 교육통계", "시군구 교원 1인당 학생수", "시군구별 학급당 학생수"],
    "r2_edu_attain": ["시군구 대졸 이상 학력 인구비율", "시군구 고등학교 졸업자 대학진학"],
    "r2_childcare": ["시군구별 어린이집 현황 보건복지부", "시군구 보육시설 정원 현원"],
    "r2_culture": ["시군구별 공공도서관 현황", "시군구별 문화시설 박물관 미술관 공연장", "공공체육시설 시군구 보유"],
    "r2_park": ["시군구별 도시공원 면적 1인당", "생활권 공원 시군구"],
    "r2_foreign": ["시군구별 외국인주민 현황 행정안전부", "지방자치단체 외국인주민 현황 시군구"],
    "r2_single": ["시군구 1인가구 인구주택총조사 가구원수별", "가구원수별 일반가구 시군구"],
    "r2_pension": ["시군구별 기초연금 수급자 보건복지부", "시군구별 국민연금 가입자 수급자"],
    "r2_business": ["시군구별 사업체수 종사자수 전국사업체조사 2023", "시군구 산업대분류별 사업체 종사자"],
    "r2_pop_dens": ["시군구 인구밀도 면적", "행정구역별 면적 인구밀도 시군구"],
    "r2_transfer": ["시군구 순이동 전입 전출 국내인구이동", "시군구별 인구이동 순이동률"],
    "r2_hospital_dist": ["시군구 응급의료기관 접근성", "시군구 지역별 건강보험 가입자 급여"],
}

R3 = {
    "r3_basic_living": ["기초생활수급자 시군구", "국민기초생활보장 수급자 시도 시군구별", "수급자 현황 읍면동 시군구 보건복지부", "생계급여 수급자 시군구", "기초생활보장 수급자 지역별", "시군구 주요통계 기초생활수급"],
    "r3_crime": ["시군구 범죄 발생", "경찰서 범죄 발생 지역별", "5대 범죄 시군구", "범죄 발생 건수 행정안전부 지방자치단체", "지방자치단체 안전 범죄 교통사고 화재 시군구"],
    "r3_library": ["공공도서관 시군구", "도서관 수 시군구별", "도서관 현황 지방자치단체", "문화기반시설 시군구별", "문화시설 수 시군구"],
    "r3_park": ["도시공원 시군구", "공원 면적 시군구별", "1인당 공원면적", "지방자치단체 도시공원 현황"],
    "r3_edu": ["학교 수 시군구", "초등학교 학생수 시군구별", "교육통계 시군구 학급당 학생수", "고등학교 졸업자 진학 시군구", "학원 수 시군구"],
    "r3_local": ["지방자치단체 주요통계 시군구", "시군구 주요지표 지방자치단체", "자치단체 기초통계 시군구"],
}
if os.environ.get("ROUND") == "3":
    KEYWORDS = R3

out = {}
for ind, kws in KEYWORDS.items():
    out[ind] = []
    for kw in kws:
        q = urllib.parse.urlencode({
            "method": "getList", "apiKey": KEY, "format": "json", "jsonVD": "Y",
            "vwCd": "MT_ZTITLE", "searchNm": kw, "resultCount": 20, "startCount": 1})
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
(ROOT / "data" / ("table_candidates_r3.json" if os.environ.get("ROUND") == "3" else "table_candidates.json")).write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print({k: len(v) for k, v in out.items()})
