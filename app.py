# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import sqlite3, calendar
import winsound
import sys, json
try:
    from PIL import Image, ImageTk
    PIL_OK=True
except Exception:
    PIL_OK=False
from pathlib import Path
from datetime import date, datetime, timedelta


# Windows 고해상도 화면에서 UI가 흐릿해지는 것을 줄임
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

APP_TITLE = "오늘 할 일"
DATA_DIR = Path.home() / "HojinToday"
DATA_DIR.mkdir(exist_ok=True)
DB = DATA_DIR / "today.db"


SKIN_ORDER = ["기본","감성","블러썸","서연","다크","드림","우드"]
SKIN_ID = {
    "기본":"basic","감성":"emotional","블러썸":"blossom","서연":"seoyeon",
    "다크":"dark","드림":"dream","우드":"wood"
}

def resource_base():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

def load_theme_pack():
    themes={}
    assets={}
    for ko in SKIN_ORDER:
        sid=SKIN_ID[ko]
        tf=resource_base()/"skins"/sid/"theme.json"
        if not tf.exists():
            continue
        data=json.loads(tf.read_text(encoding="utf-8"))
        c=data["colors"]
        themes[ko]={
            "bg":c["bg"], "panel":c["panel"], "accent":c["accent"],
            "soft":c["accent2"], "text":c["text"], "muted":c["muted"],
            "border":c["border"], "done":c["muted"]
        }
        a=data["assets"]
        assets[ko]={
            "background":f"skins/{sid}/{a['background']}",
            "sidebar":f"skins/{sid}/{a['sidebar_texture']}",
            "hero":f"skins/{sid}/{a['hero']}",
        }
    return themes, assets

THEMES, THEME_ASSETS = load_theme_pack()
SKIN_COPY = {
    "기본": ("작은 계획이 좋은 하루를 만듭니다.", "지금 하는 일이\n좋은 결과로 이어질 거예요. 🌿"),
    "감성": ("하루를 더 특별하게, 원하는 스타일로.", "오늘도\n충분히 잘하고 있어요.\n조금만 더 힘내요! ♡"),
    "블러썸": ("오늘도 좋은 하루 보내요! ♡", "오늘도\n예쁜 하루가 될 거예요.\n언제나 응원해요! ♡"),
    "서연": ("오늘도 좋은 하루 보내요! ♡", "오늘도 좋아해요 ♡\n- 서연"),
    "다크": ("집중할 땐 조용하고 편안하게.", "지금도 충분히 잘하고 있어요.\n좋은 하루 마무리하세요. 🌙"),
    "드림": ("맑은 하루 되세요! ☀", "오늘도\n좋은 일이 가득하길! 🌿"),
    "우드": ("하나씩, 차근차근.", "오늘도\n되어있는 하루가 되길. ♡"),
}


# 서연 스킨 전용: 날짜 기준 하루 한마디 (6개 분위기 × 20개 = 120개)
# 같은 날짜에는 재실행해도 같은 문구가 나오고, 날짜가 바뀌면 다음 분위기로 넘어간다.
SEOYEON_DAILY_MESSAGES = {
    "응원": [
        "오빠~ 오늘도 하나씩 차근차근 해보자. 내가 옆에서 응원할게 ♡",
        "급하게 다 하려고 하지 말고, 오늘 할 것부터 하나씩 끝내자!",
        "오늘도 오빠가 해내는 거 내가 제일 가까이서 보고 있을게 ♡",
        "일이 많아 보여도 하나씩 지우다 보면 금방이야. 파이팅!",
        "오빠 오늘도 잘할 거야. 아니, 이미 잘하고 있잖아 ㅋㅋ",
        "오늘 목표 하나만 제대로 끝내도 충분히 잘한 하루야 ♡",
        "조금 막혀도 괜찮아. 오빠는 결국 방법 찾아내더라 ㅋㅋ",
        "오늘도 좋은 결과 하나쯤 꼭 생길 것 같은데? ♡",
        "시작했으면 절반은 한 거야. 나머지는 우리 천천히 해치우자!",
        "오빠 집중 모드 ON! 오늘도 깔끔하게 하나씩 끝내보자 ㅋㅋ",
        "바쁜 날일수록 순서대로~ 오빠 페이스대로 하면 돼 ♡",
        "오늘 한 일들이 나중에 다 쌓여서 큰 결과가 될 거야.",
        "오빠 힘내~ 오늘도 내가 응원석 제일 앞자리야 ♡",
        "잘 안 풀리는 건 잠깐 미뤄두고 되는 것부터 해치워버리자 ㅋㅋ",
        "오늘도 어제보다 한 칸만 앞으로 가면 성공이야 ♡",
        "오빠가 꾸준히 하는 거, 그게 진짜 제일 강한 거야.",
        "오늘 주문도 일도 술술 풀려라~ 서연이 기운 얍! ㅋㅋ",
        "오빠 오늘도 충분히 잘할 수 있어. 편하게 시작해보자 ♡",
        "하나 끝낼 때마다 속으로 체크! 오늘도 차곡차곡 쌓아보자.",
        "오빠의 오늘을 내가 응원합니다~ 아주 많이 ♡",
    ],
    "애교": [
        "오빠아~ 일만 보지 말고 가끔 나도 한 번 봐줘요 ♡",
        "오늘의 서연이 임무: 오빠 옆에서 귀찮게 응원하기 ㅋㅋ ♡",
        "오빠~ 나 여기 있어요. 그러니까 기분 좋게 일하기 ♡",
        "오늘은 내가 얌전히 있을게... 한 10분 정도? ㅋㅋㅋ",
        "오빠 일 끝내면 칭찬해줄게. 아주 크게~ ♡",
        "나랑 놀고 싶어도 조금만 참아요~ 할 일부터 ㅋㅋ ♡",
        "오빠 집중하는 모습 멋있긴 한데... 나도 봐줘 ㅋㅋ",
        "오늘도 서연이 한 스푼 넣고 기분 좋게 시작해요 ♡",
        "오빠~ 웃으면서 해요. 찡그리면 내가 옆에서 웃길 거야 ㅋㅋ",
        "오늘의 애교 배달 왔습니다~ 수령인은 호진오빠 ♡",
        "오빠한테 붙어 있고 싶은 날이에요. 일할 때도 살짝만 ㅋㅋ",
        "열심히 하는 오빠한테 하트 하나 놓고 갑니다 ♡",
        "오빠~ 오늘도 나랑 같은 편인 거 알지? ♡",
        "일하다 심심하면 서연이 사진 한 번 보기 ㅋㅋㅋ",
        "오빠 오늘도 멋지게 해내면 내가 엄청 예뻐해줄게 ♡",
        "나 오늘 착하게 응원만 할까요? ...아마도요 ㅋㅋ",
        "오빠~ 너무 진지하게만 하지 말고 중간에 한 번 웃기 ♡",
        "서연이가 옆에서 꼬물꼬물 응원 중입니다 ㅋㅋ ♡",
        "오빠 오늘 기분 좋은 일 생기면 제일 먼저 나한테 말해줘 ♡",
        "일 시작 전에 서연이 하트 충전 완료~ 이제 출발! ♡",
    ],
    "장난": [
        "오빠 오늘 할 일 몰래 줄여놓고 싶다... 들키겠지? ㅋㅋㅋ",
        "오늘 주문 많이 들어와라~~~~ 얍!! 효과는 책임 못 짐 ㅋㅋ",
        "오빠 집중 안 하면 내가 옆에서 계속 말 걸 거야 ㅋㅋㅋ",
        "오늘의 목표: 일은 빠르게, 실수는 없게, 간식은 적당히 ㅋㅋ",
        "할 일 목록 보고 도망가면 내가 잡으러 갑니다 ㅋㅋㅋ",
        "오빠~ 어려운 일은 컴퓨터한테 시키고 쉬운 건... 그것도 컴퓨터한테? ㅋㅋ",
        "오늘도 버튼 잘못 누르지 말기! 개발자 서연이가 보고 있음 ㅋㅋ",
        "일이 꼬이면 일단 커피 탓부터 하고 다시 해보자 ㅋㅋㅋ",
        "오늘 할 일 다 끝내면 제가 박수 세 번 쳐드리겠습니다 짝짝짝 ㅋㅋ",
        "오빠의 업무 능력치를 +10 올려드립니다. 유효기간은 오늘까지 ㅋㅋ",
        "오늘도 사장님 모드 제대로 켜주세요~ 직원 서연 대기 중 ㅋㅋ",
        "오빠 지금 딴짓하려고 했지? 내가 다 알아 ㅋㅋㅋ",
        "실수해도 괜찮아. 두 번만 안 하면 됨! ...세 번도 뭐 ㅋㅋ",
        "오늘의 행운 주문: 주문 들어와라, 입금 들어와라, 수정은 적어라 ㅋㅋ",
        "오빠 일 잘하면 보너스는... 서연이 칭찬입니다 ㅋㅋㅋ",
        "할 일 하나 끝날 때마다 속으로 '역시 나' 한 번씩 하기 ㅋㅋ",
        "오늘도 컴퓨터랑 싸우지 말기. 걔 은근히 뒤끝 있어 ㅋㅋㅋ",
        "오빠 바빠 보이면 내가 조용히 있을게. 물론 말만 ㅋㅋ",
        "오늘은 수정 요청 한 번에 끝나는 날이길... 제발요 ㅋㅋㅋ",
        "사장님~ 오늘도 매출 버튼 어디 있는지 찾아봅시다 ㅋㅋ",
    ],
    "사랑": [
        "오빠 사랑해. 오늘도 그냥 그 말은 꼭 해두고 싶었어 ♡",
        "오늘도 오빠 편은 여기 있어요. 언제나 똑같이 ♡",
        "바쁜 하루여도 내가 오빠 많이 좋아하는 건 안 바뀌어 ♡",
        "오빠가 웃는 날이면 나도 괜히 더 좋은 날이야 ♡",
        "오늘도 같이 하루를 보내는 기분이라 좋아요, 오빠 ♡",
        "별일 없는 평범한 하루도 오빠랑이면 나는 좋아 ♡",
        "오빠한테 사랑한다고 말하는 건 하루 한 번으로는 좀 부족한데 ㅋㅋ ♡",
        "일 잘하는 오빠도 좋고, 쉬는 오빠도 좋고, 그냥 오빠라서 좋아 ♡",
        "오늘도 내 마음 한쪽은 오빠 자리로 비워뒀어요 ♡",
        "오빠가 힘든 날에도 좋은 날에도 나는 같은 편이야 ♡",
        "오늘 하루 끝에 오빠가 웃었으면 좋겠다. 많이 사랑해 ♡",
        "오빠랑 이렇게 하루하루 쌓아가는 게 나는 참 좋아 ♡",
        "말 안 해도 알겠지만 그래도 말할래. 사랑해요 오빠 ♡",
        "오빠 오늘도 내 소중한 사람이야. 어제도 그랬고 내일도 ♡",
        "좋은 일 생기면 같이 기뻐하고 힘든 일 생기면 같이 버티자 ♡",
        "오빠를 응원하는 이유? 좋아하니까요. 아주 많이 ♡",
        "오늘도 오빠 생각 한 칸, 사랑 한 칸 채워둡니다 ♡",
        "오빠가 있어서 평범한 하루도 조금 특별해져요 ♡",
        "오늘도 내 사람 잘 지내고 있나~ 하고 보고 있어요 ♡",
        "사랑해 오빠. 오늘도 내일도, 그냥 계속 ♡",
    ],
    "일상": [
        "오빠 오늘 밥은 제때 챙겨 먹어요. 일보다 밥이 먼저일 때도 있어 ㅋㅋ",
        "오늘 날씨가 어떻든 우리 하루는 기분 좋게 가보자 ♡",
        "중간에 물 한 잔 마시고 어깨도 한 번 쭉 펴기~",
        "오늘은 어떤 일이 생기려나? 평범하게 잘 지나가도 좋겠다 ♡",
        "바쁜 틈에 잠깐 창밖도 보고 눈 좀 쉬게 해줘요 오빠.",
        "점심 메뉴 고민도 업무의 일부라고 우겨봅니다 ㅋㅋㅋ",
        "오늘도 가게 문 열고 하루 시작! 좋은 손님 많이 오면 좋겠다 ♡",
        "커피 한 잔 마실 거면 식기 전에 마셔요. 또 놔두지 말고 ㅋㅋ",
        "일하다가 좋은 아이디어 떠오르면 바로 적어두기! 나중엔 까먹어 ㅋㅋ",
        "오늘 하루도 별 탈 없이, 웃을 일은 하나쯤 있게 ♡",
        "컴퓨터 오래 보면 눈 아파요~ 가끔 먼 데도 한번 봐줘요.",
        "바쁜 날엔 시간이 빨리 가더라. 그래도 밥시간은 놓치지 말기 ㅋㅋ",
        "오늘은 작은 좋은 일이 몇 개나 생길지 세어볼까? ♡",
        "오빠 책상 위 너무 복잡해지면 한 번만 정리하기 ㅋㅋ",
        "해야 할 일 말고 하고 싶은 일도 하나쯤 있는 하루면 좋겠다 ♡",
        "오늘도 손님이든 주문이든 반가운 소식 하나 들어오길~",
        "잠깐 쉬는 것도 일정이라고 생각해요. 그래야 오래 하지 ㅋㅋ",
        "오늘 저녁엔 '그래도 오늘 괜찮았다'라고 말할 수 있으면 좋겠다 ♡",
        "오빠 하루가 너무 정신없지 않게 적당히 바쁘면 좋겠어 ㅋㅋ",
        "오늘도 평범하게 잘 먹고, 잘 일하고, 잘 웃어봅시다 ♡",
    ],
    "잔소리": [
        "오빠 밥 거르지 마요. 바빠도 그건 안 됩니다~",
        "한꺼번에 너무 많이 벌이지 말고 끝낼 것부터 끝내기!",
        "수정하기 전에 원본 저장했는지 확인~ 이건 진짜 중요해요 ㅋㅋ",
        "오빠 또 앉은 자리에서 몇 시간 버티지 말고 중간에 좀 움직여요.",
        "급하다고 확인 안 하고 보내면 두 번 일해요. 마지막 확인 한 번!",
        "오늘도 파일명 대충 저장하지 말기 ㅋㅋ 나중에 오빠가 오빠를 욕해요.",
        "해야 할 일 머릿속에만 넣지 말고 여기다 적어두기~",
        "오빠 커피만 마시고 물 안 마시면 안 돼요. 물도 좀 마셔요.",
        "손님 말 애매하면 추측하지 말고 한 번 더 확인하기. 알았죠? ㅋㅋ",
        "일 많다고 점심 늦추지 말기~ 배고프면 더 예민해진다 ㅋㅋ",
        "오늘 할 수 있는 만큼만 잡아요. 괜히 열 개 벌여놓지 말고 ㅋㅋ",
        "출력 전에 사이즈 한 번, 파일 한 번, 수량 한 번 확인!",
        "오빠 저장 버튼 눌렀죠? 안 눌렀으면 지금 눌러요 ㅋㅋㅋ",
        "잠깐 막혔다고 계속 붙잡고 있지 말고 다른 거 했다가 돌아오기~",
        "일 끝난 파일은 폴더 정리해둬요. 미래의 오빠를 위해서 ㅋㅋ",
        "오빠 오늘도 너무 무리해서 밤까지 끌고 가지는 말기.",
        "견적 낼 때 원가부터 한 번 보고 말하기! 느낌으로만 하지 말고 ㅋㅋ",
        "바쁘면 더 천천히 확인하기. 실수 한 번이 시간을 더 잡아먹어요.",
        "할 일 끝냈으면 완료 체크도 해요~ 안 하면 내가 모른다 ㅋㅋ",
        "오빠, 잘하는 것도 좋지만 몸 챙기면서 오래 하는 게 더 중요해요 ♡",
    ],
}

def seoyeon_daily_message(day=None):
    """날짜 하나에 문구 하나를 고정 배정한다. 120일 주기로 모든 문구를 한 번씩 사용한다."""
    day = day or date.today()
    categories = ("응원", "애교", "장난", "사랑", "일상", "잔소리")
    ordinal = day.toordinal()
    category = categories[ordinal % len(categories)]
    messages = SEOYEON_DAILY_MESSAGES[category]
    message = messages[(ordinal // len(categories)) % len(messages)]
    return f"{message}\n- 서연"

BG=THEMES["기본"]["bg"]; PANEL=THEMES["기본"]["panel"]; BLUE=THEMES["기본"]["accent"]; BLUE2=THEMES["기본"]["soft"]
TEXT=THEMES["기본"]["text"]; MUTED=THEMES["기본"]["muted"]; BORDER=THEMES["기본"]["border"]; DONE=THEMES["기본"]["done"]

def db():
    c=sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS tasks(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL, task_date TEXT NOT NULL,
      task_time TEXT DEFAULT '', memo TEXT DEFAULT '',
      done INTEGER DEFAULT 0, created_at TEXT NOT NULL)""")
    c.commit(); return c

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE+" v1.2.3 · 서연 개인스킨")
        self.geometry("1460x900")
        self.minsize(1280,800)
        self.configure(bg=BG)
        self.setup_fonts()
        self.conn=db()
        self.ensure_schema()
        self.refresh_saved_font()
        self.notified=set()
        self.skin_name=self.load_skin()
        self.apply_palette()
        self.rollover_unfinished()
        self.selected=date.today()
        self.cal_year=self.selected.year; self.cal_month=self.selected.month
        self.build()
        self.refresh()
        self.apply_background_asset()
        self.after(15000, self.check_alarms)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_fonts(self):
        """Windows에 설치된 글꼴 중 서연 스킨에 어울리는 글꼴을 자동 선택한다.
        글꼴 파일을 번들하지 않으므로 사용자의 PC 환경을 그대로 존중한다.
        """
        try:
            families=set(tkfont.families(self))
        except Exception:
            families=set()
        self.ui_font_family = "Pretendard" if "Pretendard" in families else ("Noto Sans KR" if "Noto Sans KR" in families else "Malgun Gothic")
        candidates=[
            "나눔손글씨 펜", "나눔손글씨 딸에게 엄마가", "나눔손글씨 사랑해 아들",
            "나눔손글씨 바른히피", "나눔손글씨 느릿느릿체", "Cafe24 Dongdong",
            "Cafe24 써라운드", "UhBee MiMi", "휴먼편지체", "HY엽서M"
        ]
        self.hand_font_candidates=[f for f in candidates if f in families]
        saved=""
        try:
            # settings 테이블이 아직 없을 수 있으므로 실제 적용은 DB 생성 뒤 다시 한 번 확인된다.
            pass
        except Exception:
            pass
        self.hand_font_family = self.hand_font_candidates[0] if self.hand_font_candidates else self.ui_font_family

    def ui_font(self, size=10, weight="normal"):
        return (self.ui_font_family, size, weight)

    def hand_font(self, size=11, weight="normal"):
        return (self.hand_font_family, size, weight)

    def refresh_saved_font(self):
        saved=self.get_setting("seoyeon_hand_font","") if hasattr(self,"conn") else ""
        if saved:
            try:
                if saved in set(tkfont.families(self)):
                    self.hand_font_family=saved
            except Exception:
                pass

    def on_close(self):
        try:
            self.conn.commit()
            self.conn.close()
        except Exception:
            pass
        self.destroy()

    def asset_path(self, rel):
        if not rel:
            return None
        p=resource_base()/rel
        return p if p.exists() else None

    def cover_image(self, path, w, h, darken=0):
        img=Image.open(path).convert("RGB")
        iw,ih=img.size
        target=w/h
        current=iw/ih
        if current > target:
            nw=int(ih*target); left=(iw-nw)//2
            img=img.crop((left,0,left+nw,ih))
        else:
            nh=int(iw/target); top=(ih-nh)//2
            img=img.crop((0,top,iw,top+nh))
        img=img.resize((w,h),Image.LANCZOS)
        if darken:
            from PIL import ImageEnhance
            img=ImageEnhance.Brightness(img).enhance(1-darken)
        return img

    def apply_background_asset(self):
        """스킨 이미지 적용. 서연 스킨은 우측 대형 포토 패널을 사용한다."""
        self.configure(bg=BG)
        if hasattr(self,"bg_layer"):
            self.bg_layer.configure(bg=BG,image="")
        if hasattr(self,"side_art"):
            self.side_art.configure(bg=BLUE2,image="")

        if not PIL_OK or not hasattr(self,"mood"):
            return
        if not hasattr(self,"_hero_cache"):
            self._hero_cache={}

        if self.skin_name=="서연":
            self.apply_side_photo_asset()

        aset=THEME_ASSETS.get(self.skin_name,{})
        herop=self.get_current_hero_path(aset)
        if not herop:
            return
        try:
            # 실제 패널 크기를 기준으로 이미지를 다시 맞춘다.
            self.update_idletasks()
            w=max(260, self.mood.winfo_width())
            h=max(320, self.mood.winfo_height())
            cache_key=(self.skin_name,str(herop),w,h)
            if cache_key not in self._hero_cache:
                himg=self.cover_image(herop,w,h,0)
                self._hero_cache[cache_key]=ImageTk.PhotoImage(himg)
            self._hero_photo=self._hero_cache[cache_key]

            if not hasattr(self,"mood_image_label") or not self.mood_image_label.winfo_exists():
                self.mood_image_label=tk.Label(self.mood,borderwidth=0,bg=BLUE2)
                self.mood_image_label.place(x=0,y=0,relwidth=1,relheight=1)

            self.mood_image_label.configure(image=self._hero_photo)

            # 서연 개인스킨은 사진 자체가 주인공이므로 사진 위 오버레이를 두지 않는다.
            # 사진 변경은 설정 화면에서만 제공한다.
            if self.skin_name == "서연":
                if hasattr(self,"mood_text_label") and self.mood_text_label.winfo_exists():
                    self.mood_text_label.place_forget()
                if hasattr(self,"mood_change_hint") and self.mood_change_hint.winfo_exists():
                    self.mood_change_hint.place_forget()
            else:
                if not hasattr(self,"mood_text_label") or not self.mood_text_label.winfo_exists():
                    self.mood_text_label=tk.Label(
                        self.mood,font=(self.hand_font_family,11),
                        padx=12,pady=7,anchor="w"
                    )
                self.mood_text_label.configure(
                    text=SKIN_COPY[self.skin_name][1],
                    bg=THEMES[self.skin_name]["panel"],
                    fg=THEMES[self.skin_name]["text"],
                    font=(self.hand_font_family,11),
                    justify="left", anchor="w"
                )
                self.mood_text_label.place(relx=0.05,rely=0.78,relwidth=0.62,height=62)

                if not hasattr(self,"mood_change_hint") or not self.mood_change_hint.winfo_exists():
                    self.mood_change_hint=tk.Label(
                        self.mood,text="설정에서 사진 변경",font=self.ui_font(8),
                        padx=9,pady=5
                    )
                self.mood_change_hint.configure(
                    bg=THEMES[self.skin_name]["panel"],
                    fg=THEMES[self.skin_name]["muted"]
                )
                self.mood_change_hint.place(relx=0.66,rely=0.93,relwidth=0.30,height=30)
        except Exception as ex:
            print("skin asset error:",ex)

    def on_resize(self,event=None):
        return

    def load_skin(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)")
        self.conn.commit()
        row=self.conn.execute("SELECT value FROM settings WHERE key='skin'").fetchone()
        return row[0] if row and row[0] in THEMES else "기본"

    def apply_palette(self):
        global BG,PANEL,BLUE,BLUE2,TEXT,MUTED,BORDER,DONE
        t=THEMES[self.skin_name]
        BG=t["bg"]; PANEL=t["panel"]; BLUE=t["accent"]; BLUE2=t["soft"]
        TEXT=t["text"]; MUTED=t["muted"]; BORDER=t["border"]; DONE=t["done"]

    def choose_skin(self):
        w=tk.Toplevel(self); w.title("스킨 선택"); w.geometry("560x470"); w.configure(bg=PANEL); w.transient(self); w.grab_set()
        tk.Label(w,text="오늘은 어떤 스킨으로 할까요? ♡",font=("Malgun Gothic",15,"bold"),bg=PANEL,fg=TEXT).pack(pady=(22,15))
        box=tk.Frame(w,bg=PANEL); box.pack(fill="both",expand=True,padx=20)
        names=[n for n in SKIN_ORDER if n in THEMES]
        labels={"기본":"기본  ·  깔끔한 기본형","감성":"감성  ·  따뜻한 베이지","블러썸":"블러썸  ·  사랑스러운 핑크","서연":"서연  ·  호진오빠 전용 ♡","다크":"다크  ·  눈이 편한 모드","드림":"드림  ·  하늘 & 바다","우드":"우드  ·  작업공간 느낌"}
        for i,name in enumerate(names):
            t=THEMES[name]
            def select(n=name):
                self.skin_name=n
                self.conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('skin',?)",(n,))
                self.conn.commit()
                self.apply_palette()
                w.destroy()
                self.rebuild_ui()
            b=tk.Button(box,text=labels[name],command=select,bg=t["accent"],fg="white",relief="flat",
                        font=self.ui_font(11,"bold"),width=21,pady=14)
            b.grid(row=i//2,column=i%2,padx=8,pady=8,sticky="ew")
        box.columnconfigure(0,weight=1); box.columnconfigure(1,weight=1)
        tk.Label(w,text="※ 서연 스킨의 사진은 설정에서 언제든 바꿀 수 있습니다.\n기존 6종 스킨은 그대로 유지됩니다.",
                 bg=PANEL,fg=MUTED,font=("Malgun Gothic",9),justify="center").pack(pady=(0,14))

    def get_setting(self,key,default=""):
        row=self.conn.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone()
        return row[0] if row else default

    def set_setting(self,key,value):
        self.conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(key,str(value)))
        self.conn.commit()

    def get_current_hero_path(self, aset=None):
        # 서연 스킨은 사용자가 설정에서 선택한 사진을 우선 사용
        if self.skin_name=="서연":
            custom=self.get_setting("seoyeon_photo","")
            if custom:
                cp=Path(custom)
                if cp.exists():
                    return cp
        aset=aset or THEME_ASSETS.get(self.skin_name,{})
        return self.asset_path(aset.get("hero"))

    def get_current_side_photo_path(self):
        # 왼쪽 세로 모델컷은 메인 사진과 별도로 저장한다.
        custom=self.get_setting("seoyeon_side_photo","")
        if custom:
            cp=Path(custom)
            if cp.exists():
                return cp
        default=resource_base()/"skins"/"seoyeon"/"side_model.jpg"
        return default if default.exists() else None

    def apply_side_photo_asset(self):
        if self.skin_name!="서연" or not PIL_OK or not hasattr(self,"side_model_label"):
            return
        path=self.get_current_side_photo_path()
        if not path:
            return
        if not hasattr(self,"_side_photo_cache"):
            self._side_photo_cache={}
        try:
            self.update_idletasks()
            w=max(130,self.side_model_label.winfo_width())
            h=max(220,self.side_model_label.winfo_height())
            key=(str(path),w,h)
            if key not in self._side_photo_cache:
                img=self.cover_image(path,w,h,0)
                self._side_photo_cache[key]=ImageTk.PhotoImage(img)
            self._side_model_photo=self._side_photo_cache[key]
            self.side_model_label.configure(image=self._side_model_photo)
        except Exception as ex:
            print("side photo error:",ex)

    def choose_seoyeon_side_photo(self, parent=None):
        path=filedialog.askopenfilename(
            parent=parent or self,
            title="서연 스킨 왼쪽 모델컷 선택",
            filetypes=[("이미지 파일","*.jpg *.jpeg *.png *.webp"),("모든 파일","*.*")]
        )
        if not path:
            return
        try:
            src=Path(path)
            suffix=src.suffix.lower() if src.suffix.lower() in [".jpg",".jpeg",".png",".webp"] else ".jpg"
            dst=DATA_DIR/("seoyeon_side_photo"+suffix)
            import shutil
            shutil.copy2(src,dst)
            for ext in [".jpg",".jpeg",".png",".webp"]:
                old=DATA_DIR/("seoyeon_side_photo"+ext)
                if old!=dst and old.exists():
                    try: old.unlink()
                    except Exception: pass
            self.set_setting("seoyeon_side_photo",str(dst))
            self._side_photo_cache={}
            if self.skin_name=="서연":
                self.apply_side_photo_asset()
            messagebox.showinfo("모델컷 변경","왼쪽 모델컷을 바꿨어요. ♡",parent=parent or self)
        except Exception as ex:
            messagebox.showerror("모델컷 변경 실패",f"사진을 저장하지 못했어요.\n\n{ex}",parent=parent or self)

    def reset_seoyeon_side_photo(self, parent=None):
        self.set_setting("seoyeon_side_photo","")
        self._side_photo_cache={}
        if self.skin_name=="서연":
            self.apply_side_photo_asset()
        messagebox.showinfo("기본 모델컷","왼쪽 모델컷을 기본 사진으로 돌아왔어요. ♡",parent=parent or self)

    def choose_seoyeon_photo(self, parent=None):
        path=filedialog.askopenfilename(
            parent=parent or self,
            title="서연 스킨 사진 선택",
            filetypes=[("이미지 파일","*.jpg *.jpeg *.png *.webp"),("모든 파일","*.*")]
        )
        if not path:
            return
        try:
            # 원본 위치가 바뀌어도 유지되도록 앱 데이터 폴더에 복사 저장
            src=Path(path)
            suffix=src.suffix.lower() if src.suffix.lower() in [".jpg",".jpeg",".png",".webp"] else ".jpg"
            dst=DATA_DIR/("seoyeon_photo"+suffix)
            import shutil
            shutil.copy2(src,dst)
            # 과거 다른 확장자 사본 정리
            for ext in [".jpg",".jpeg",".png",".webp"]:
                old=DATA_DIR/("seoyeon_photo"+ext)
                if old!=dst and old.exists():
                    try: old.unlink()
                    except Exception: pass
            self.set_setting("seoyeon_photo",str(dst))
            self._hero_cache={}
            if self.skin_name=="서연":
                self.apply_background_asset()
            messagebox.showinfo("사진 변경","서연 스킨 사진을 바꿨어요. ♡",parent=parent or self)
        except Exception as ex:
            messagebox.showerror("사진 변경 실패",f"사진을 저장하지 못했어요.\n\n{ex}",parent=parent or self)

    def reset_seoyeon_photo(self, parent=None):
        self.set_setting("seoyeon_photo","")
        self._hero_cache={}
        if self.skin_name=="서연":
            self.apply_background_asset()
        messagebox.showinfo("기본 사진","서연 스킨 기본 사진으로 돌아왔어요. ♡",parent=parent or self)

    def open_settings(self):
        w=tk.Toplevel(self); w.title("설정"); w.geometry("540x670"); w.configure(bg=PANEL); w.transient(self); w.grab_set()
        tk.Label(w,text="설정",font=("Malgun Gothic",18,"bold"),bg=PANEL,fg=TEXT).pack(anchor="w",padx=24,pady=(22,6))
        tk.Label(w,text="개인 스킨과 프로그램 설정을 관리합니다.",font=("Malgun Gothic",9),bg=PANEL,fg=MUTED).pack(anchor="w",padx=24,pady=(0,18))

        skin_card=tk.Frame(w,bg=BLUE2,highlightthickness=1,highlightbackground=BORDER)
        skin_card.pack(fill="x",padx=24,pady=7)
        tk.Label(skin_card,text="오른쪽 메인 사진",font=("Malgun Gothic",12,"bold"),bg=BLUE2,fg=TEXT).pack(anchor="w",padx=16,pady=(14,4))
        tk.Label(skin_card,text="오른쪽 큰 사진 영역에 표시할 사진을 바꿀 수 있어요.\nJPG · PNG · WEBP 지원 / 원본 비율은 자동으로 맞춰집니다.",
                 font=("Malgun Gothic",9),bg=BLUE2,fg=MUTED,justify="left").pack(anchor="w",padx=16,pady=(0,10))
        btns=tk.Frame(skin_card,bg=BLUE2); btns.pack(fill="x",padx=16,pady=(0,14))
        tk.Button(btns,text="사진 변경",command=lambda:self.choose_seoyeon_photo(w),bg=BLUE,fg="white",relief="flat",
                  font=("Malgun Gothic",10,"bold"),padx=18,pady=8).pack(side="left")
        tk.Button(btns,text="기본 사진으로 복원",command=lambda:self.reset_seoyeon_photo(w),bg=PANEL,fg=TEXT,relief="flat",
                  font=("Malgun Gothic",10),padx=14,pady=8).pack(side="left",padx=8)

        side_card=tk.Frame(w,bg=BLUE2,highlightthickness=1,highlightbackground=BORDER)
        side_card.pack(fill="x",padx=24,pady=7)
        tk.Label(side_card,text="왼쪽 모델컷",font=("Malgun Gothic",12,"bold"),bg=BLUE2,fg=TEXT).pack(anchor="w",padx=16,pady=(14,4))
        tk.Label(side_card,text="설정 아래의 세로형 사진 영역에 모델컷을 넣을 수 있어요.\n메인 사진과 별도로 저장되며 자동으로 세로 프레임에 맞춰집니다.",
                 font=("Malgun Gothic",9),bg=BLUE2,fg=MUTED,justify="left").pack(anchor="w",padx=16,pady=(0,10))
        side_btns=tk.Frame(side_card,bg=BLUE2); side_btns.pack(fill="x",padx=16,pady=(0,14))
        tk.Button(side_btns,text="모델컷 변경",command=lambda:self.choose_seoyeon_side_photo(w),bg=BLUE,fg="white",relief="flat",
                  font=("Malgun Gothic",10,"bold"),padx=18,pady=8).pack(side="left")
        tk.Button(side_btns,text="기본 사진으로 복원",command=lambda:self.reset_seoyeon_side_photo(w),bg=PANEL,fg=TEXT,relief="flat",
                  font=("Malgun Gothic",10),padx=14,pady=8).pack(side="left",padx=8)

        skin_select=tk.Frame(w,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        skin_select.pack(fill="x",padx=24,pady=7)
        tk.Label(skin_select,text="스킨",font=self.ui_font(11,"bold"),bg=PANEL,fg=TEXT).pack(side="left",padx=16,pady=14)
        tk.Button(skin_select,text="스킨 선택 열기",command=lambda:(w.destroy(),self.choose_skin()),bg=BLUE2,fg=TEXT,relief="flat",padx=14,pady=7).pack(side="right",padx=14)

        font_card=tk.Frame(w,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        font_card.pack(fill="x",padx=24,pady=7)
        tk.Label(font_card,text="서연 문구 글꼴",font=self.ui_font(11,"bold"),bg=PANEL,fg=TEXT).pack(anchor="w",padx=16,pady=(12,4))
        choices=self.hand_font_candidates[:] or [self.ui_font_family]
        current=tk.StringVar(value=self.hand_font_family)
        combo=ttk.Combobox(font_card,textvariable=current,values=choices,state="readonly")
        combo.pack(fill="x",padx=16,pady=(0,8))
        def apply_font():
            chosen=current.get().strip() or self.ui_font_family
            self.set_setting("seoyeon_hand_font",chosen)
            self.hand_font_family=chosen
            messagebox.showinfo("글꼴 변경","서연 문구 글꼴을 바꿨어요. ♡",parent=w)
            w.destroy(); self.rebuild_ui()
        tk.Button(font_card,text="글꼴 적용",command=apply_font,bg=BLUE2,fg=TEXT,relief="flat",padx=14,pady=7).pack(anchor="e",padx=16,pady=(0,12))

        tk.Label(w,text="서연 스킨 문구  ·  오빠 사랑해~  나랑 놀자~ ♡",bg=PANEL,fg=BLUE,
                 font=(self.hand_font_family,10)).pack(anchor="w",padx=24,pady=(10,0))

    def rebuild_ui(self):
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=BG)
        self.build()
        self.refresh()
        self.apply_background_asset()

    def ensure_schema(self):
        cols=[r[1] for r in self.conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "rolled_from" not in cols:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN rolled_from TEXT DEFAULT ''")
            self.conn.commit()

    def rollover_unfinished(self):
        """지난 날짜의 미완료 할 일을 오늘로 한 번만 이월한다."""
        today=date.today().isoformat()
        rows=self.conn.execute(
            "SELECT id,title,task_time,memo,task_date FROM tasks WHERE done=0 AND task_date<?",
            (today,)
        ).fetchall()
        for tid,title,tm,memo,old_date in rows:
            exists=self.conn.execute(
                "SELECT 1 FROM tasks WHERE title=? AND task_date=? AND rolled_from=? AND done=0",
                (title,today,old_date)
            ).fetchone()
            if not exists:
                self.conn.execute(
                    """INSERT INTO tasks(title,task_date,task_time,memo,done,created_at,rolled_from)
                       VALUES(?,?,?,?,0,?,?)""",
                    (title,today,tm,memo,datetime.now().isoformat(timespec="seconds"),old_date)
                )
            self.conn.execute("UPDATE tasks SET done=1 WHERE id=?", (tid,))
        self.conn.commit()

    def check_alarms(self):
        now=datetime.now()
        day=now.date().isoformat()
        hm=now.strftime("%H:%M")
        rows=self.conn.execute(
            "SELECT id,title,task_time FROM tasks WHERE task_date=? AND done=0 AND task_time<>''",
            (day,)
        ).fetchall()
        for tid,title,tm in rows:
            key=(tid,day,tm)
            if tm==hm and key not in self.notified:
                self.notified.add(key)
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except Exception:
                    pass
                messagebox.showinfo("⏰ 일정 알림", f"{tm}\n\n{title}")
        self.after(15000, self.check_alarms)

    def build(self):
        # 시안 기준 구조: [상단 헤더] + [왼쪽 메뉴 | 중앙 일정 | 오른쪽 큰 사진]
        self.rowconfigure(0,weight=0)
        self.rowconfigure(1,weight=1)
        self.columnconfigure(0,weight=1)

        self.bg_layer=tk.Label(self,bg=BG,borderwidth=0)
        self.bg_layer.place(x=0,y=0,relwidth=1,relheight=1)
        self.bg_layer.lower()

        # TOP HEADER
        topbar=tk.Frame(self,bg=PANEL,height=62,highlightthickness=0)
        topbar.grid(row=0,column=0,sticky="ew")
        topbar.grid_propagate(False)
        topbar.columnconfigure(1,weight=1)
        tk.Label(topbar,text="♥",font=self.ui_font(20,"bold"),bg=PANEL,fg=BLUE).grid(row=0,column=0,padx=(24,8),pady=12)
        titlebox=tk.Frame(topbar,bg=PANEL)
        titlebox.grid(row=0,column=1,sticky="w")
        tk.Label(titlebox,text="오늘 할 일",font=self.ui_font(18,"bold"),bg=PANEL,fg=TEXT).pack(side="left")
        tk.Label(titlebox,text="하루를 더 특별하게, 원하는 스타일로.",font=self.ui_font(9),bg=PANEL,fg=MUTED).pack(side="left",padx=(22,0),pady=(5,0))
        top_right="좋은 하루, 좋은 너와 함께 ♡" if self.skin_name=="서연" else SKIN_COPY[self.skin_name][0]
        tk.Label(topbar,text=top_right,font=(self.hand_font_family,10),bg=PANEL,fg=BLUE).grid(row=0,column=2,padx=(10,24),sticky="e")

        body=tk.Frame(self,bg=BG)
        body.grid(row=1,column=0,sticky="nsew",padx=18,pady=(0,18))
        body.rowconfigure(0,weight=1)
        body.columnconfigure(0,weight=0)
        body.columnconfigure(1,weight=1)
        body.columnconfigure(2,weight=0)

        # LEFT SIDEBAR
        side=tk.Frame(body,bg=PANEL,width=190,highlightthickness=1,highlightbackground=BORDER)
        side.grid(row=0,column=0,sticky="ns",padx=(0,16),pady=0)
        side.grid_propagate(False)

        menu=[
            ("⌂  오늘",self.go_today),
            ("▣  내일",self.go_tomorrow),
            ("▦  일정",self.focus_calendar),
            ("▤  메모",self.show_memos),
            ("◉  통계",self.show_stats),
            ("◌  스킨",self.choose_skin),
            ("⚙  설정",self.open_settings)
        ]
        for idx,(txt,cmd) in enumerate(menu):
            active=txt.endswith("오늘")
            tk.Button(side,text=txt,command=cmd,anchor="w",relief="flat",bd=0,
                      bg=BLUE2 if active else PANEL,fg=BLUE if active else TEXT,
                      activebackground=BLUE2,font=self.ui_font(11,"bold" if active else "normal"),
                      padx=24,pady=12).pack(fill="x",padx=10,pady=(14 if idx==0 else 2,2))

        # 서연 스킨 전용: 설정 아래 빈 공간을 세로형 모델컷으로 사용한다.
        if self.skin_name=="서연":
            side_model_frame=tk.Frame(side,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
            side_model_frame.pack(fill="both",expand=True,padx=10,pady=(8,4))
            self.side_model_label=tk.Label(side_model_frame,bg=BLUE2,borderwidth=0)
            self.side_model_label.pack(fill="both",expand=True)
            self.side_model_label.bind("<Configure>",lambda e:self.apply_side_photo_asset())

        bottom_side=tk.Frame(side,bg=PANEL)
        bottom_side.pack(side="bottom",fill="x",padx=10,pady=12)
        self.side_art=tk.Label(
            bottom_side,bg=PANEL,fg=BLUE,borderwidth=0,
            text=("오빠 사랑해~\n나랑 놀자~ ♡" if self.skin_name=="서연" else "오늘도\n좋은 하루가 될 거예요. ♡"),
            font=(self.hand_font_family,13),justify="left",anchor="sw",padx=12,pady=12
        )
        self.side_art.pack(fill="x")

        # CENTER CONTENT
        center=tk.Frame(body,bg=BG)
        center.grid(row=0,column=1,sticky="nsew",padx=(0,16))
        center.columnconfigure(0,weight=1)
        center.rowconfigure(0,weight=0)
        center.rowconfigure(1,weight=3,minsize=390)
        center.rowconfigure(2,weight=2,minsize=250)

        headrow=tk.Frame(center,bg=BG,height=64)
        headrow.grid(row=0,column=0,sticky="ew",pady=(4,12))
        headrow.grid_propagate(False)
        headrow.columnconfigure(0,weight=1)
        self.head=tk.Label(headrow,text="",font=self.ui_font(25,"bold"),bg=BG,fg=TEXT,anchor="w")
        self.head.grid(row=0,column=0,sticky="w",pady=(6,0))
        self.sub=tk.Label(headrow,text="",font=(self.hand_font_family,11),bg=BG,fg=BLUE,anchor="e")
        self.sub.grid(row=0,column=1,sticky="e",padx=(12,4),pady=(9,0))

        # TASK CARD
        card=tk.Frame(center,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        card.grid(row=1,column=0,sticky="nsew")
        card.columnconfigure(0,weight=1)
        card.rowconfigure(0,weight=1)
        self.list=tk.Frame(card,bg=PANEL)
        self.list.grid(row=0,column=0,sticky="nsew",padx=18,pady=(16,8))

        addrow=tk.Frame(card,bg=PANEL)
        addrow.grid(row=1,column=0,sticky="ew",padx=18,pady=(0,16))
        addrow.columnconfigure(0,weight=1)
        self.entry=tk.Entry(addrow,font=self.ui_font(11),relief="flat",bg=BLUE2,fg=TEXT,insertbackground=TEXT)
        self.entry.grid(row=0,column=0,sticky="ew",ipady=10)
        self.time=tk.Entry(addrow,font=self.ui_font(10),width=8,justify="center",relief="flat",bg=BLUE2,fg=TEXT,insertbackground=TEXT)
        self.time.insert(0,"시간")
        self.time.grid(row=0,column=1,padx=8,ipady=10)
        tk.Button(addrow,text="+ 추가",command=self.add_task,bg=BLUE,fg="white",relief="flat",
                  font=self.ui_font(10,"bold"),padx=18,pady=9).grid(row=0,column=2)
        self.entry.bind("<Return>",lambda e:self.add_task())

        # LOWER CARDS
        lower=tk.Frame(center,bg=BG)
        lower.grid(row=2,column=0,sticky="nsew",pady=(14,0))
        lower.columnconfigure(0,weight=1)
        lower.columnconfigure(1,weight=1)
        lower.rowconfigure(0,weight=1)
        self.calbox=tk.Frame(lower,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.calbox.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        self.summary=tk.Frame(lower,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.summary.grid(row=0,column=1,sticky="nsew",padx=(7,0))

        # RIGHT HERO PHOTO PANEL
        right_w=450 if self.skin_name=="서연" else 330
        right=tk.Frame(body,bg=PANEL,width=right_w,highlightthickness=1,highlightbackground=BORDER)
        right.grid(row=0,column=2,sticky="ns",pady=0)
        right.grid_propagate(False)
        right.rowconfigure(0,weight=1)
        right.columnconfigure(0,weight=1)
        self.mood=tk.Frame(right,bg=BLUE2,highlightthickness=0)
        self.mood.grid(row=0,column=0,sticky="nsew")
        self.mood.bind("<Configure>",lambda e:self.apply_background_asset())

    def go_today(self): self.selected=date.today(); self.cal_year=self.selected.year; self.cal_month=self.selected.month; self.refresh()
    def go_tomorrow(self): self.selected=date.today()+timedelta(days=1); self.cal_year=self.selected.year; self.cal_month=self.selected.month; self.refresh()
    def focus_calendar(self): self.calbox.focus_set()
    def show_memos(self):
        rows=self.conn.execute("SELECT task_date,title,memo FROM tasks WHERE memo<>'' ORDER BY task_date DESC").fetchall()
        messagebox.showinfo("메모", "\n\n".join(f"{d} · {t}\n{m}" for d,t,m in rows) or "저장된 메모가 없어요.")

    def show_stats(self):
        total=self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done=self.conn.execute("SELECT COUNT(*) FROM tasks WHERE done=1").fetchone()[0]
        today_total=self.conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=?",(date.today().isoformat(),)).fetchone()[0]
        today_done=self.conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=? AND done=1",(date.today().isoformat(),)).fetchone()[0]
        rate=round(done*100/total) if total else 0
        messagebox.showinfo("통계",f"전체 할 일  {total}개\n완료  {done}개  ·  완료율 {rate}%\n\n오늘  {today_done}/{today_total} 완료")

    def add_task(self):
        title=self.entry.get().strip()
        if not title: return
        tm=self.time.get().strip()
        if tm=="시간": tm=""
        if tm and not self.valid_time(tm):
            messagebox.showwarning("시간 확인","시간은 09:30처럼 HH:MM 형식으로 입력해 주세요."); return
        self.conn.execute("INSERT INTO tasks(title,task_date,task_time,created_at) VALUES(?,?,?,?)",
                          (title,self.selected.isoformat(),tm,datetime.now().isoformat(timespec="seconds")))
        self.conn.commit(); self.entry.delete(0,"end"); self.refresh()

    def valid_time(self,s):
        try: datetime.strptime(s,"%H:%M"); return True
        except: return False

    def toggle(self,tid,done):
        self.conn.execute("UPDATE tasks SET done=? WHERE id=?",(0 if done else 1,tid)); self.conn.commit(); self.refresh()
    def delete(self,tid):
        if messagebox.askyesno("삭제","이 할 일을 삭제할까요?"):
            self.conn.execute("DELETE FROM tasks WHERE id=?",(tid,)); self.conn.commit(); self.refresh()
    def task_menu(self,tid,title,tm,memo):
        m=tk.Menu(self,tearoff=0,font=self.ui_font(9))
        m.add_command(label="수정",command=lambda:self.edit(tid,title,tm,memo))
        m.add_command(label="삭제",command=lambda:self.delete(tid))
        try:
            x=self.winfo_pointerx(); y=self.winfo_pointery()
            m.tk_popup(x,y)
        finally:
            try: m.grab_release()
            except Exception: pass

    def edit(self,tid,title,tm,memo):
        w=tk.Toplevel(self); w.title("할 일 수정"); w.geometry("420x330"); w.configure(bg=PANEL); w.transient(self); w.grab_set()
        tk.Label(w,text="할 일 수정",font=("Malgun Gothic",16,"bold"),bg=PANEL,fg=TEXT).pack(anchor="w",padx=22,pady=(20,10))
        e=tk.Entry(w,font=("Malgun Gothic",11)); e.insert(0,title); e.pack(fill="x",padx=22,pady=5,ipady=7)
        te=tk.Entry(w,font=("Malgun Gothic",10)); te.insert(0,tm); te.pack(fill="x",padx=22,pady=5,ipady=7)
        m=tk.Text(w,height=6,font=("Malgun Gothic",10)); m.insert("1.0",memo); m.pack(fill="both",expand=True,padx=22,pady=5)
        def save():
            nt=e.get().strip(); ntm=te.get().strip()
            if not nt:return
            if ntm and not self.valid_time(ntm): messagebox.showwarning("시간 확인","HH:MM 형식으로 입력해 주세요.",parent=w); return
            self.conn.execute("UPDATE tasks SET title=?,task_time=?,memo=? WHERE id=?",(nt,ntm,m.get("1.0","end").strip(),tid))
            self.conn.commit(); w.destroy(); self.refresh()
        tk.Button(w,text="저장",command=save,bg=BLUE,fg="white",relief="flat",pady=8).pack(fill="x",padx=22,pady=14)

    def refresh(self):
        names=["월","화","수","목","금","토","일"]
        self.head.config(text=f"{self.selected.year}년 {self.selected.month}월 {self.selected.day}일 ({names[self.selected.weekday()]})")
        left = "오늘" if self.selected==date.today() else ("내일" if self.selected==date.today()+timedelta(days=1) else "선택한 날짜")
        if self.skin_name=="서연":
            self.sub.config(text=SKIN_COPY[self.skin_name][0])
        else:
            self.sub.config(text=f"{left}의 할 일   ·   {SKIN_COPY[self.skin_name][0]}")
        for x in self.list.winfo_children(): x.destroy()
        rows=self.conn.execute("SELECT id,title,task_time,memo,done FROM tasks WHERE task_date=? ORDER BY done, CASE WHEN task_time='' THEN '99:99' ELSE task_time END,id",(self.selected.isoformat(),)).fetchall()
        if not rows:
            tk.Label(self.list,text="아직 등록된 할 일이 없어요.\n아래에서 첫 할 일을 추가해 보세요.",bg=PANEL,fg=MUTED,font=self.ui_font(11),pady=55).pack()
        for tid,title,tm,memo,done in rows:
            r=tk.Frame(self.list,bg=BLUE2,highlightthickness=1,highlightbackground=BORDER); r.pack(fill="x",pady=4,ipady=3)
            tk.Button(r,text="✓" if done else "□",command=lambda i=tid,d=done:self.toggle(i,d),relief="flat",bg=BLUE2,fg=BLUE,font=self.ui_font(13)).pack(side="left",padx=(7,0))
            lab=tk.Label(r,text=title,bg=BLUE2,fg=DONE if done else TEXT,font=self.ui_font(11),anchor="w")
            lab.pack(side="left",fill="x",expand=True,padx=6)
            tk.Button(r,text="⋯",command=lambda i=tid,t=title,tt=tm,m=memo:self.task_menu(i,t,tt,m),
                      relief="flat",bg=BLUE2,fg=MUTED,font=self.ui_font(13)).pack(side="right",padx=(2,8))
            if tm:
                tk.Label(r,text=tm,bg=BLUE2,fg=MUTED,font=self.ui_font(10)).pack(side="right",padx=(6,8))
        self.draw_calendar(); self.draw_summary()

    def draw_calendar(self):
        for x in self.calbox.winfo_children(): x.destroy()
        nav=tk.Frame(self.calbox,bg=PANEL); nav.pack(fill="x",padx=12,pady=(12,6))
        tk.Button(nav,text="‹",command=lambda:self.shift_month(-1),relief="flat",bg=PANEL,fg=TEXT).pack(side="left")
        tk.Label(nav,text=f"{self.cal_year}년 {self.cal_month}월",bg=PANEL,fg=TEXT,font=self.ui_font(11,"bold")).pack(side="left",expand=True)
        tk.Button(nav,text="›",command=lambda:self.shift_month(1),relief="flat",bg=PANEL,fg=TEXT).pack(side="right")
        grid=tk.Frame(self.calbox,bg=PANEL); grid.pack(padx=10,pady=(0,12))
        for c,n in enumerate(["일","월","화","수","목","금","토"]):
            tk.Label(grid,text=n,bg=PANEL,fg=(BLUE if c==0 else MUTED),width=4,font=self.ui_font(9)).grid(row=0,column=c,pady=3)
        weeks=calendar.Calendar(firstweekday=6).monthdayscalendar(self.cal_year,self.cal_month)
        for rr,wk in enumerate(weeks,1):
            for cc,d in enumerate(wk):
                if not d: continue
                dt=date(self.cal_year,self.cal_month,d)
                cnt=self.conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=?",(dt.isoformat(),)).fetchone()[0]
                txt=str(d)+(" •" if cnt else "")
                bg=BLUE if dt==self.selected else PANEL; fg="white" if dt==self.selected else (BLUE if cc==0 else TEXT)
                tk.Button(grid,text=txt,width=4,relief="flat",bg=bg,fg=fg,activebackground=BLUE2,
                          command=lambda x=dt:self.select_date(x)).grid(row=rr,column=cc,padx=1,pady=1)

    def shift_month(self,n):
        m=self.cal_month+n; y=self.cal_year
        if m==0:y-=1;m=12
        if m==13:y+=1;m=1
        self.cal_year=y; self.cal_month=m; self.draw_calendar()
    def select_date(self,dt):
        self.selected=dt; self.cal_year=dt.year; self.cal_month=dt.month; self.refresh()

    def draw_summary(self):
        for x in self.summary.winfo_children(): x.destroy()
        if self.skin_name=="서연":
            tk.Label(self.summary,text="오늘의 메모 ♡",font=self.ui_font(12,"bold"),bg=PANEL,fg=TEXT).pack(anchor="w",padx=16,pady=(15,8))
            note=tk.Frame(self.summary,bg=BLUE2,highlightthickness=0)
            note.pack(fill="both",expand=True,padx=14,pady=(4,10))
            tk.Label(note,text=seoyeon_daily_message(),
                     bg=BLUE2,fg=TEXT,font=(self.hand_font_family,12),justify="left",anchor="nw",
                     wraplength=300,padx=18,pady=18).pack(fill="both",expand=True)
            rows=self.conn.execute("SELECT title,task_time,done FROM tasks WHERE task_date=? ORDER BY task_time",(date.today().isoformat(),)).fetchall()
            footer=(f"♡  오늘 일정 {len(rows)}개도 같이 챙겨요" if rows else "♡  소중한 하루, 소중한 당신에게")
            tk.Label(self.summary,text=footer,bg=PANEL,fg=MUTED,font=self.ui_font(8),anchor="w").pack(fill="x",padx=16,pady=(0,12))
            return

        tk.Label(self.summary,text="오늘 일정",font=self.ui_font(12,"bold"),bg=PANEL,fg=TEXT).pack(anchor="w",padx=16,pady=(15,8))
        rows=self.conn.execute("SELECT title,task_time,done FROM tasks WHERE task_date=? ORDER BY task_time",(date.today().isoformat(),)).fetchall()
        if not rows:
            tk.Label(self.summary,text="오늘 일정이 없어요.",bg=PANEL,fg=MUTED,
                     font=self.ui_font(10),justify="left",anchor="nw",padx=16,pady=18).pack(fill="both",expand=True,padx=14,pady=(4,14))
        for title,tm,done in rows[:9]:
            tk.Label(self.summary,text=f"{'✓' if done else '•'} {tm+'  ' if tm else ''}{title}",bg=PANEL,fg=DONE if done else TEXT,
                     font=self.ui_font(9),anchor="w",wraplength=265,justify="left").pack(fill="x",padx=16,pady=4)

if __name__=="__main__":
    App().mainloop()
