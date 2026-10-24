# 시군구 삶의 질 랭킹 (life-stats)

분야 → 지표 2단 체계로 지표를 고르면, 광역 17개 시도와 기초 229개 시군구의 상위 3·하위 3을 보여주는 정적 사이트(GitHub Pages).

## 구조
- `index.html` — 화면(스코어카드). 지표 선택 → 광역·기초 상위/하위 3, 동률 묶음, 전체 순위, 지역 검색, 시군구 지도(단계구분도)
- `data/data.json` — 화면이 읽는 데이터 (`isSample:false`면 실데이터)
- `scripts/indicators.json` — 분야·지표 설정(KOSIS 통계표 코드)
- `scripts/fetch_kosis.py` — 수집. 표마다 지역 코드 체계가 달라 (시도, 지역명)으로 맞추고, 시 아래 일반구는 제외(229개 기준)
- `scripts/find_tables.py`, `crawl_kosis_list.py`, `probe_tables.py` — 새 지표를 찾기 위한 탐색 도구
- `scripts/make_sample.py` — 화면 확인용 샘플(난수) 생성

## 워크플로 (Actions)
| 이름 | 용도 |
|---|---|
| `update-data` | 실데이터 수집 → `data/data.json`, `data/fetch_report.txt` (매주 월 06:00 KST) |
| `find-tables` | 키워드로 통계표 후보 탐색 → `data/table_candidates.json` |
| `probe-tables` | 통계표 항목·분류 구조 조회 → `data/table_meta.json` |
| `crawl-kosis` | KOSIS 통계목록 전체 순회(호출량 큼) |

Secrets: `KOSIS_API_KEY`(KOSIS), `DATA_GO_KR_KEY`(공공데이터포털, 아직 미사용)

## 지표 추가하는 법
1. `find-tables`의 키워드를 추가해 실행 → `table_candidates.json`에서 시군구 표 확인
2. `probe-tables`로 항목(`itmId`)·분류 구조 확인
3. `indicators.json`의 분야 아래에 지표 추가 (`ratio`, `shareOf`, `filters`, `regionDim` 등은 `fetch_kosis.py` 상단 설명 참조)
4. `update-data` 실행 후 `data/fetch_report.txt`로 시도·시군구 건수 확인

## 로컬 확인
```
python -m http.server 8000
```

## 추가 구성 (2026-10)
- `scripts/fetch_realestate.py` — 공공데이터포털 아파트 매매 실거래가 → ㎡당 평균 매매가(`apt_price`). Secret `DATA_GO_KR_KEY` 필요. 키 승인 전에는 `data/realestate_report.txt`에 원인만 남기고 종료.
- `scripts/build_geo.py` — 통계청 2018 시군구 경계를 현재 행정구역(군위군 대구 편입, 미추홀구 등)에 맞춰 단순화 → `data/geo_*.json`
- `perPop` — 지표 값을 주민등록인구로 나눠 인구 대비 비율로 만드는 옵션(`fetch_kosis.py` 상단 설명)
- 한계: 범죄율은 시도만(광주·전남 제외), 기초생활수급률·교육 지표는 전국 시군구 표를 찾지 못해 미포함

## 종합 삶의 질 지수 (시범)
- `data/qol_config.json` — 분야(7)와 소속 지표·방향. 산식은 `index.html`의 `computeQol()`: 5·95백분위 절단 min-max(0~100) → 분야 단순평균 → 사용자 가중치로 합성(산술 또는 멱평균 β=0.5)
- 해외 사례: OECD 지역 웰빙, 도요게이자 住みよさ, County Health Rankings, EU-SPI (화면의 "산식과 해외 사례 보기")
- 비교 대상 버튼(전체/자치구/시/군): 같은 유형끼리 순위·정규화를 다시 계산
