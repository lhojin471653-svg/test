from pathlib import Path
import json, py_compile

root = Path(__file__).resolve().parent
py_compile.compile(str(root/"app.py"), doraise=True)

required = ["basic","emotional","blossom","dark","dream","wood"]
for sid in required:
    d = root/"skins"/sid
    if not d.exists():
        raise SystemExit(f"누락된 스킨 폴더: {sid}")

    data = json.loads((d/"theme.json").read_text(encoding="utf-8"))
    for key in ["background","sidebar_texture","hero","reference"]:
        p = d/data["assets"][key]
        if not p.exists():
            raise SystemExit(f"누락된 자산: {p}")

# 서연 개인스킨은 reference_screen 없이 실제 사용자 사진 패널을 사용한다.
sd=root/"skins"/"seoyeon"
if not sd.exists():
    raise SystemExit("누락된 스킨 폴더: seoyeon")
sdata=json.loads((sd/"theme.json").read_text(encoding="utf-8"))
for key in ["background","sidebar_texture","hero"]:
    p=sd/sdata["assets"][key]
    if not p.exists():
        raise SystemExit(f"누락된 서연 스킨 자산: {p}")
side_model=sd/"side_model.jpg"
if not side_model.exists():
    raise SystemExit(f"누락된 서연 왼쪽 모델컷: {side_model}")


# v1.2.3 하루 한마디 기본 검증
app_text=(root/"app.py").read_text(encoding="utf-8")
if "SEOYEON_DAILY_MESSAGES" not in app_text or "seoyeon_daily_message" not in app_text:
    raise SystemExit("서연 하루 한마디 기능이 누락되었습니다.")

print("OK - app.py syntax, 7 skin assets, Seoyeon side model, and daily-message feature verified")
