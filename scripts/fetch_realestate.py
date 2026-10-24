"""공공데이터포털(국토교통부) 아파트 매매 실거래가 → 시군구 ㎡당 평균 매매가.

사용:  DATA_GO_KR_KEY=키 KOSIS_API_KEY=키 python scripts/fetch_realestate.py
  (fetch_kosis.py 가 만든 data/data.json 에 지표 'apt_price'를 덧붙인다)

- 시군구 법정동 코드(LAWD_CD, 5자리)는 KOSIS 행안부 주민등록 표(DT_1B040A3 등)의 행정기관코드 앞 5자리를 쓴다.
- 최근 2개월 거래의 (거래금액 합 ÷ 전용면적 합) = ㎡당 평균 가격(만원). 취소 거래 제외, 거래 5건 미만 지역은 제외.
- 개발계정 일일 호출 한도(약 1,000건)를 넘지 않도록 월 2개·페이지 1,000건으로 호출한다.
"""
import concurrent.futures, datetime, json, os, pathlib, sys, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

T0 = time.time()
BUDGET = 14 * 60  # 초. 넘으면 지금까지 모은 것으로 마무리

ROOT = pathlib.Path(__file__).resolve().parent.parent
DKEY = os.environ.get("DATA_GO_KR_KEY")
KKEY = os.environ.get("KOSIS_API_KEY")
if not DKEY or not KKEY:
    sys.exit("DATA_GO_KR_KEY, KOSIS_API_KEY 필요 → 건너뜀")

sys.path.insert(0, str(ROOT / "scripts"))
SHORT = [("서울", "서울"), ("부산", "부산"), ("대구", "대구"), ("인천", "인천"), ("광주", "광주"),
         ("대전", "대전"), ("울산", "울산"), ("세종", "세종"), ("경기", "경기"), ("강원", "강원"),
         ("충청북", "충북"), ("충북", "충북"), ("충청남", "충남"), ("충남", "충남"),
         ("전라북", "전북"), ("전북", "전북"), ("전라남", "전남"), ("전남", "전남"),
         ("경상북", "경북"), ("경북", "경북"), ("경상남", "경남"), ("경남", "경남"), ("제주", "제주")]
ENDPOINTS = [
    "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade",
    "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev",
]
log = []


def short_sido(n):
    n = (n or "").replace(" ", "")
    for k, v in SHORT:
        if n.startswith(k):
            return v


def fetch_raw(url):
    """한 번 호출. HTTP 오류도 본문을 돌려줘 원인을 로그에 남긴다."""
    for a in range(2):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return f"HTTP{e.code} " + e.read().decode("utf-8", "replace")[:300]
        except Exception as e:
            err = str(e)
            time.sleep(1.5)
    return "EXC " + err


def get(url, as_json=False):
    err = ""
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                b = r.read().decode("utf-8")
            return json.loads(b) if as_json else b
        except Exception as e:
            err = str(e)
            time.sleep(1.5 * (a + 1))
    return {"err": err} if as_json else ""


# 1) 시군구 법정동 코드 목록 ---------------------------------------------------
def lawd_codes():
    for tbl in ("DT_1B040A3", "DT_1B04006", "DT_1B040B3"):
        for extra in ({}, {"objL2": "ALL"}, {"objL2": "ALL", "objL3": "ALL"}):
            q = {"method": "getList", "apiKey": KKEY, "format": "json", "jsonVD": "Y", "orgId": "101",
                 "tblId": tbl, "itmId": "ALL", "objL1": "ALL", "prdSe": "M", "newEstPrdCnt": 1, **extra}
            rows = get("https://kosis.kr/openapi/Param/statisticsParameterData.do?" + urllib.parse.urlencode(q), True)
            if isinstance(rows, list) and rows:
                out = {}
                for r in rows:
                    c, n = str(r.get("C1", "")), r.get("C1_NM", "")
                    if len(c) >= 5 and c.isdigit() and n:
                        out.setdefault(c[:5], n)
                log.append(f"코드표 {tbl}: {len(out)}개, 코드길이 {sorted({len(str(r.get('C1',''))) for r in rows})}")
                return out
            log.append(f"코드표 {tbl} {extra}: {str(rows)[:120]}")
    return {}


codes = lawd_codes()
if not codes:
    (ROOT / "data" / "realestate_report.txt").write_text("\n".join(log), encoding="utf-8")
    sys.exit("법정동 코드표를 못 가져옴\n" + "\n".join(log))

# 2) 거래 조회 ----------------------------------------------------------------
today = datetime.date.today().replace(day=1)
months = []
d = today
for _ in range(2):
    d = (d - datetime.timedelta(days=1)).replace(day=1)
    months.append(d.strftime("%Y%m"))

endpoint = None


def deals(lawd, ym):
    global endpoint
    if time.time() - T0 > BUDGET:
        return None
    for ep in ([endpoint] if endpoint else ENDPOINTS):
        q = urllib.parse.urlencode({"serviceKey": DKEY, "LAWD_CD": lawd, "DEAL_YMD": ym, "numOfRows": 1000, "pageNo": 1})
        body = fetch_raw(f"{ep}?{q}")
        if not body.lstrip().startswith("<"):
            if len(log) < 15:
                log.append(f"{ep.split('/')[-1]} {lawd} {ym}: {body[:200]}")
            continue
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            continue
        code = (root.findtext(".//resultCode") or "").strip()
        if code not in ("00", "000"):
            if len(log) < 15:
                log.append(f"{ep.split('/')[-1]} {lawd} {ym}: {code} {root.findtext('.//resultMsg')}")
            continue
        endpoint = ep
        out = []
        for it in root.iter("item"):
            if (it.findtext("cdealType") or "").strip():
                continue  # 해제(취소) 거래
            try:
                amt = float((it.findtext("dealAmount") or "").replace(",", "").strip())
                ar = float((it.findtext("excluUseAr") or "").strip())
            except ValueError:
                continue
            if ar > 0:
                out.append((amt, ar))
        return out
    return None


agg = {}  # lawd → [sum_amt, sum_area, n]
fail = 0
# 먼저 1건으로 키·엔드포인트 확인 (안 되면 바로 종료)
probe = deals("11680", months[0])
if probe is None:
    log.append("진단 호출 실패 → 중단(키 승인·엔드포인트 확인 필요)")
    (ROOT / "data" / "realestate_report.txt").write_text("\n".join(log), encoding="utf-8")
    sys.exit("\n".join(log))
log.append(f"진단 호출 OK: 강남구 {months[0]} {len(probe)}건")


def work(job):
    lawd, ym = job
    return lawd, deals(lawd, ym)


jobs = [(c, ym) for c in sorted(codes) for ym in months]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    for lawd, r in ex.map(work, jobs):
        if r is None:
            fail += 1
        else:
            a = agg.setdefault(lawd, [0.0, 0.0, 0])
            for amt, ar in r:
                a[0] += amt
                a[1] += ar
                a[2] += 1
log.append(f"엔드포인트 {endpoint}, 코드 {len(codes)}개, 실패 호출 {fail}, 개월 {months}")

# 3) 시군구(기준 목록)·시도로 집계 ---------------------------------------------
data = json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))
canon = [(r["sido"], r["name"]) for r in data["regions"]]
by_name = {}
for c, n in codes.items():
    n = n.strip()
    sido = short_sido(n.split(" ")[0])
    nm = " ".join(n.split(" ")[1:]) if sido and len(n.split(" ")) > 1 else n
    by_name[(sido, nm)] = c
values, sido_sum, miss = {}, {}, []
for sido, name in canon:
    cs = [c for (s, n), c in by_name.items() if s == sido and n.startswith(name + " ")]  # 구가 있는 시 → 구 합산
    if name in [n for (s, n) in by_name if s == sido]:
        own = by_name[(sido, name)]
        if own in agg and agg[own][2]:
            cs = [own]
        elif not cs:
            cs = [own]
    if not cs:
        miss.append(f"{sido} {name}")
        continue
    s_amt = sum(agg[c][0] for c in cs if c in agg)
    s_ar = sum(agg[c][1] for c in cs if c in agg)
    n_deals = sum(agg[c][2] for c in cs if c in agg)
    if n_deals >= 5 and s_ar:
        values[f"{sido}|{name}"] = round(s_amt / s_ar, 1)
for c, (amt, ar, n) in agg.items():
    s = short_sido(codes[c].split(" ")[0])
    if s and n:
        t = sido_sum.setdefault(s, [0.0, 0.0])
        t[0] += amt
        t[1] += ar
sido_vals = {s: round(a / b, 1) for s, (a, b) in sido_sum.items() if b}
log.append(f"시군구 {len(values)}개, 시도 {len(sido_vals)}개, 코드 미매칭 {len(miss)}: {miss[:10]}")

if values:
    for t in data["themes"]:
        t["indicators"] = [i for i in t["indicators"] if i["id"] != "apt_price"]
    housing = next(t for t in data["themes"] if t["id"] == "housing")
    housing["indicators"].append({
        "id": "apt_price", "name": "아파트 ㎡당 매매 실거래가", "unit": "만원/㎡", "higherIsBetter": False,
        "source": "국토교통부 아파트 매매 실거래가(공공데이터포털)", "yearSido": months[0], "yearSigungu": months[0],
        "note": f"{months[-1]}~{months[0]} 거래의 거래금액 합 ÷ 전용면적 합. 거래 5건 미만 지역 제외"})
    data["values"]["apt_price"] = values
    data["sidoValues"]["apt_price"] = sido_vals
    (ROOT / "data" / "data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
(ROOT / "data" / "realestate_report.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))
