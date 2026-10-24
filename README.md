# 시군구 삶의 질 랭킹 (life-stats)

시군구별 사회경제지표를 주제별로 순위로 보여주는 정적 사이트 (GitHub Pages).

## 구조
- `index.html` — 화면 (주제 탭 → 지표 선택 → 순위 막대, 시도 필터·검색, 지역 클릭 시 전 지표 순위)
- `data/data.json` — 화면이 읽는 데이터. 현재는 **샘플(난수)**
- `scripts/make_sample.py` — 샘플 생성
- `scripts/fetch_kosis.py` + `scripts/indicators.json` — KOSIS OpenAPI 수집
- `.github/workflows/update-data.yml` — 주 1회 자동 갱신

## 실데이터로 전환
1. KOSIS OpenAPI 키 발급 → GitHub Secrets에 `KOSIS_API_KEY`
2. `indicators.json`에 지표별 `orgId / tblId / itmId / objL1` 입력 (KOSIS URL 생성 화면에서 복사)
3. Actions → update-data 수동 실행 → `data/data.json` 갱신 (`isSample:false` 면 경고 배너 사라짐)
4. Settings → Pages → main / root 배포

## 로컬 확인
```
python scripts/make_sample.py
python -m http.server 8000
```
