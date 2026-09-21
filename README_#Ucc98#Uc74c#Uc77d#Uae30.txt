오늘 할 일 v1.0 — Windows Release Build Kit

최종 목표
- 오빠 PC에는 Python 설치 필요 없음
- 최종 파일은 오늘할일.exe 한 개
- 더블클릭으로 실행

포함
- app.py
- skins/: 기본·감성·블러썸·다크·드림·우드 6종 실자산
- icons/: 공통 UI 아이콘
- 오늘할일.spec
- version_info.txt
- .github/workflows/build-windows.yml
- BUILD_WINDOWS_EXE.bat
- VERIFY_RELEASE.py

오빠 PC에 Python을 설치하지 않는 방법
1. 이 ZIP 내용 전체를 GitHub 저장소에 올립니다.
2. GitHub에서 Actions 탭을 엽니다.
3. 'Build 오늘할일 Windows EXE'를 선택합니다.
4. Run workflow를 누릅니다.
5. 작업 완료 후 Artifact '오늘할일-v1.0-Windows'를 받습니다.
6. 압축 안의 오늘할일.exe를 실행합니다.

EXE 첫 실행 테스트
[ ] 실행
[ ] 기본/감성/블러썸/다크/드림/우드 전환
[ ] 재실행 후 선택 스킨 유지
[ ] 오늘 일정 추가
[ ] 내일 일정 추가
[ ] 완료 체크
[ ] 수정/삭제
[ ] 달력 날짜 선택
[ ] 메모
[ ] 통계
[ ] 지정시간 팝업/알림음
[ ] 지난 미완료 일정 자동 이월

중요
현재 ChatGPT 작업 환경은 Windows가 아니므로 실제 Windows EXE 파일 자체를
이 자리에서 컴파일하고 실행 검증했다고 말할 수는 없습니다.
이 키트는 Windows 빌드 서버에서 EXE를 만들도록 구성된 최종 빌드용 패키지입니다.
