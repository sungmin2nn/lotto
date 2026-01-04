# 🎱 로또 분석기

로또 당첨번호 조회, 통계 분석, AI 예측 웹앱

## 🚀 기능

### 📊 기본 기능
- 최신 당첨번호 조회
- 회차별 검색
- 당첨금 정보 (1~5등)
- 내 번호 당첨 확인

### 📈 통계 분석
- **출현 빈도**: HOT/COLD 번호, 번호별 출현 횟수
- **패턴 분석**: 홀짝, 고저, 번호대, 끝수, 총합, 연속번호
- **고급 통계**: 평균, 표준편차, 사분위수, Z-Score, AC값
- **당첨금 분석**: 등수별 평균, 추이, 역대 최고

### 🔮 예측
- 7가지 전략 (균형, HOT, COLD, 패턴, Z-Score, 트렌드, 랜덤)
- 제외 번호 설정
- 필수 번호 설정 (최대 5개)
- 생성 개수 설정 (1~10세트)

## 📁 파일 구조

```
lotto-analyzer/
├── .github/workflows/
│   └── collect.yml      # 자동 수집 워크플로우
├── collect_lotto.py      # 데이터 수집 스크립트
├── requirements.txt
├── index.html           # 프론트엔드
├── lotto_data.json      # 수집된 데이터 (자동 생성)
└── README.md
```

## ⚙️ 설정 방법

### 1. GitHub 저장소 생성
새 저장소를 만들고 모든 파일 업로드

### 2. Actions 권한 설정
Settings → Actions → General → Workflow permissions
- ✅ Read and write permissions

### 3. 첫 데이터 수집
Actions → 로또 데이터 수집 → Run workflow

### 4. GitHub Pages 활성화
Settings → Pages → Branch: main → Save

### 5. 접속
`https://[username].github.io/[repository]/`

## 🔄 자동 업데이트

매주 일요일 오전 9시 (한국시간) 자동으로 최신 데이터 수집

## ⚠️ 주의사항

로또는 완전한 무작위 추첨입니다. 통계 분석은 참고용이며, 당첨을 보장하지 않습니다.

## 📜 라이선스

MIT License
