# Quant AI Server

Multi-Agent LLM 기반 퀀트 투자 분석 서비스 AI 서버

## 프로젝트 구조

```
ai-server/
├── agents/
│   ├── agent1_collect.py   ← 희재 작성
│   ├── agent2_strategy.py  ← 희재 작성
│   ├── agent3_execute.py   ← 주원 작성
│   └── graph.py            ← 주원 작성
├── services/
│   ├── quant/              ← 희재 핵심 로직
│   └── nlp/                ← 주원 핵심 로직
├── models/
│   └── state.py            ← 주원 작성
├── db/
├── main.py
└── .env
```

## 브랜치 전략

- main: 최종 완성본
- develop: 통합 브랜치
- feature/이름-기능명: 각자 작업 브랜치

## 커밋 메시지 규칙

- feat: 새 기능 추가
- fix: 버그 수정
- docs: 문서 수정
- refactor: 코드 개선

## 예시

feat: 뉴스 수집 노드 구현
fix: 감성 분석 JSON 파싱 오류 수정

## 담당

- B (희재): 주가 수집 · 지표 계산 · 전략 수립 · 백테스트 · 수집 안정화
- C (주원): LangGraph 설계·연결 · 뉴스 수집 · 감성 분석 ·
            비중 조합 · 추천 근거 생성 · 리포트 생성 ·
            가상 잔고 · 주문 실행
