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

print("OK - app.py 문법 및 6종 스킨 자산 검증 완료")
