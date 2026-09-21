오늘 할 일 v1.0.1 — 스킨 실제 적용 수정

문제 원인
- 이전 Windows 빌드가 v0.9 소스 구조를 그대로 사용했습니다.
- 그래서 블러썸/감성/드림 등의 색상 팔레트만 바뀌고 실제 이미지 자산은 사용되지 않았습니다.

v1.0.1 수정
- 앱 제목 v1.0.1
- skins/*/theme.json 실제 로드
- background_soft.jpg → 프로그램 전체 배경
- sidebar_texture.jpg → 왼쪽 하단 장식 영역
- hero.jpg → 오른쪽 무드 카드
- 기본/감성/블러썸/다크/드림/우드 6종 모두 적용
- 스킨 선택 메뉴 추가
- 통계 메뉴 추가
- 기존 일정/달력/메모/알람/미완료 이월 유지
- EXE 패키징에서 skins/icons 포함

GitHub에서 교체할 파일
- app.py
- VERIFY_RELEASE.py
- .github/workflows/build-windows.yml
(나머지 skins/icons는 기존 저장소에 이미 있다면 그대로 사용 가능)

권장: 이 ZIP의 전체 내용을 기존 저장소에 덮어올리면 가장 확실합니다.
