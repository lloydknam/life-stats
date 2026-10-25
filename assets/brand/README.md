# Lloyd's balcony lab — 브랜드 키트

모든 개인 프로젝트(GitHub 레포·사이트·영상) 하단 크레딧에 공통으로 쓰는 로고 모음입니다.

| 파일 | 용도 |
|---|---|
| `mark.svg`, `mark-512.png` | 마크(베란다에서 커피 마시는 나 + 열일하는 AI 노트북) |
| `lockup-light.svg/.png` | 밝은 배경용 가로형 로고: Lloyd's balcony lab / with claude · GitHub(@lloydknam) |
| `lockup-dark.svg/.png` | 어두운 배경용 가로형 로고 |
| `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` | 작은 크기용 단순형(창틀 + AI 노트북) |

## 붙이는 법

사이트 하단(HTML):

```html
<a href="https://github.com/lloydknam"><img src="https://lloydknam.github.io/life-stats/assets/brand/lockup-light.svg" alt="Lloyd's balcony lab · with claude · GitHub(@lloydknam)" height="48"></a>
```

README(마크다운):

```markdown
[![Lloyd's balcony lab](https://lloydknam.github.io/life-stats/assets/brand/lockup-light.png)](https://github.com/lloydknam)
```

색: 먹색 `#1d2a44`, 종이색 `#f6f1e6`, 주황 `#e8772e`, 방 불빛 `#ffe7bf`, 스웨터 파랑 `#3c5a9a`
글꼴: IBM Plex Mono(글자는 SVG 안에서 윤곽선으로 변환되어 있어 글꼴 설치 불필요)
