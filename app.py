# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
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


SKIN_ORDER = ["기본","감성","블러썸","다크","드림","우드"]
SKIN_ID = {
    "기본":"basic","감성":"emotional","블러썸":"blossom",
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
    "다크": ("집중할 땐 조용하고 편안하게.", "지금도 충분히 잘하고 있어요.\n좋은 하루 마무리하세요. 🌙"),
    "드림": ("맑은 하루 되세요! ☀", "오늘도\n좋은 일이 가득하길! 🌿"),
    "우드": ("하나씩, 차근차근.", "오늘도\n되어있는 하루가 되길. ♡"),
}
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
        self.title(APP_TITLE+" v1.0.3")
        self.geometry("1280x800")
        self.minsize(1100,700)
        self.configure(bg=BG)
        self.conn=db()
        self.ensure_schema()
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
        """깜박임 방지형 스킨 이미지 적용.
        - 전체 배경은 순수 색상
        - 우측 무드 카드 이미지 1장만 사용
        - PhotoImage는 스킨별 1회 생성 후 캐시
        """
        self.configure(bg=BG)
        if hasattr(self,"bg_layer"):
            self.bg_layer.configure(bg=BG,image="")
        if hasattr(self,"side_art"):
            self.side_art.configure(bg=BLUE2,image="")

        if not PIL_OK or not hasattr(self,"mood"):
            return

        if not hasattr(self,"_hero_cache"):
            self._hero_cache={}

        aset=THEME_ASSETS.get(self.skin_name,{})
        herop=self.asset_path(aset.get("hero"))
        if not herop:
            return

        try:
            # 카드 크기는 고정값 사용: resize 이벤트와 완전히 분리
            w,h=315,230
            cache_key=(self.skin_name,w,h)

            if cache_key not in self._hero_cache:
                himg=self.cover_image(herop,w,h,0)
                self._hero_cache[cache_key]=ImageTk.PhotoImage(himg)

            self._hero_photo=self._hero_cache[cache_key]

            # build() 때 한 번 만든 label만 재사용
            if not hasattr(self,"mood_image_label") or not self.mood_image_label.winfo_exists():
                self.mood_image_label=tk.Label(self.mood,borderwidth=0,bg=BLUE2)
                self.mood_image_label.place(x=0,y=0,width=w,height=h)

                self.mood_text_label=tk.Label(
                    self.mood,font=("Malgun Gothic",9,"bold"),
                    padx=10,pady=5,anchor="w"
                )
                self.mood_text_label.place(x=12,y=172,width=291,height=42)

            self.mood_image_label.configure(image=self._hero_photo)
            self.mood_text_label.configure(
                text=SKIN_COPY[self.skin_name][1].replace("\n","  "),
                bg=THEMES[self.skin_name]["panel"],
                fg=THEMES[self.skin_name]["text"]
            )
        except Exception as ex:
            print("skin asset error:",ex)

    def on_resize(self,event=None):
        return

    def load_skin(self):
        self.conn.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT)")
        self.conn.commit()
        row=self.conn.execute("SELECT value FROM settings WHERE key='skin'").fetchone()
        if row and row[0]=="서연":
            self.conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('skin','블러썸')")
            self.conn.commit()
            return "블러썸"
        return row[0] if row and row[0] in THEMES else "기본"

    def apply_palette(self):
        global BG,PANEL,BLUE,BLUE2,TEXT,MUTED,BORDER,DONE
        t=THEMES[self.skin_name]
        BG=t["bg"]; PANEL=t["panel"]; BLUE=t["accent"]; BLUE2=t["soft"]
        TEXT=t["text"]; MUTED=t["muted"]; BORDER=t["border"]; DONE=t["done"]

    def choose_skin(self):
        w=tk.Toplevel(self); w.title("스킨 선택"); w.geometry("560x390"); w.configure(bg=PANEL); w.transient(self); w.grab_set()
        tk.Label(w,text="오늘은 어떤 스킨으로 할까요? ♡",font=("Malgun Gothic",15,"bold"),bg=PANEL,fg=TEXT).pack(pady=(22,15))
        box=tk.Frame(w,bg=PANEL); box.pack(fill="both",expand=True,padx=20)
        names=[n for n in SKIN_ORDER if n in THEMES]
        labels={"기본":"기본  ·  깔끔한 기본형","감성":"감성  ·  따뜻한 베이지","블러썸":"블러썸  ·  사랑스러운 핑크","다크":"다크  ·  눈이 편한 모드","드림":"드림  ·  하늘 & 바다","우드":"우드  ·  작업공간 느낌"}
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
                        font=("Malgun Gothic",11,"bold"),width=21,pady=14)
            b.grid(row=i//2,column=i%2,padx=8,pady=8,sticky="ew")
        box.columnconfigure(0,weight=1); box.columnconfigure(1,weight=1)
        tk.Label(w,text="※ 블러썸 스킨은 인물 사진 없이 꽃과 로즈핑크 디자인으로 적용됩니다.\n6종 모두 확정된 스킨 이미지가 전체 화면 분위기와 히어로 카드에 적용됩니다.",
                 bg=PANEL,fg=MUTED,font=("Malgun Gothic",9),justify="center").pack(pady=(0,14))

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
        self.columnconfigure(1,weight=1)
        self.rowconfigure(0,weight=1)

        # 전체 스킨 배경
        self.bg_layer=tk.Label(self,bg=BG,borderwidth=0)
        self.bg_layer.place(x=0,y=0,relwidth=1,relheight=1)
        self.bg_layer.lower()

        # LEFT SIDEBAR
        side=tk.Frame(self,bg=PANEL,width=190,highlightthickness=1,highlightbackground=BORDER)
        side.grid(row=0,column=0,sticky="nsw")
        side.grid_propagate(False)

        top_side=tk.Frame(side,bg=PANEL)
        top_side.pack(fill="x")
        tk.Label(top_side,text="✓  오늘 할 일",font=("Malgun Gothic",17,"bold"),
                 bg=PANEL,fg=TEXT).pack(pady=(25,4))
        tk.Label(top_side,text=f"{self.skin_name} SKIN",font=("Malgun Gothic",8,"bold"),
                 bg=PANEL,fg=BLUE).pack(pady=(0,14))

        menu=[
            ("⌂  오늘",self.go_today),
            ("▣  내일",self.go_tomorrow),
            ("□  일정",self.focus_calendar),
            ("▤  메모",self.show_memos),
            ("◉  통계",self.show_stats),
            ("◌  스킨",self.choose_skin),
            ("⚙  설정",self.choose_skin)
        ]
        for txt,cmd in menu:
            active=txt.endswith("오늘")
            tk.Button(
                top_side,text=txt,command=cmd,anchor="w",relief="flat",bd=0,
                bg=BLUE2 if active else PANEL,fg=BLUE if active else TEXT,
                activebackground=BLUE2,
                font=("Malgun Gothic",11,"bold" if active else "normal"),
                padx=24,pady=9
            ).pack(fill="x",padx=10,pady=2)

        # 좌측 하단은 스킨 이미지가 실제로 보이는 영역
        bottom_side=tk.Frame(side,bg=PANEL)
        bottom_side.pack(side="bottom",fill="x")
        self.side_art=tk.Label(
            bottom_side,bg=BLUE2,fg=TEXT,borderwidth=0,
            text="오늘도\n좋은 하루가 될 거예요. ♡",
            font=("Malgun Gothic",9),justify="left",anchor="sw",
            padx=16,pady=18
        )
        self.side_art.pack(fill="x",padx=10,pady=(0,10))
        tk.Label(bottom_side,text=SKIN_COPY[self.skin_name][0],bg=PANEL,fg=MUTED,
                 font=("Malgun Gothic",8),wraplength=150,justify="left").pack(
                     fill="x",padx=16,pady=(0,16)
                 )

        # CENTER
        center=tk.Frame(self,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        center.grid(row=0,column=1,sticky="nsew",padx=18,pady=18)
        center.columnconfigure(0,weight=1)
        center.rowconfigure(2,weight=1)

        self.head=tk.Label(center,text="",font=("Malgun Gothic",23,"bold"),
                           bg=PANEL,fg=TEXT,anchor="w")
        self.head.grid(row=0,column=0,sticky="ew",padx=2,pady=(0,2))
        self.sub=tk.Label(center,text="",font=("Malgun Gothic",10),
                          bg=PANEL,fg=MUTED,anchor="w")
        self.sub.grid(row=1,column=0,sticky="ew",padx=2,pady=(0,16))

        card=tk.Frame(center,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        card.grid(row=2,column=0,sticky="nsew")
        card.columnconfigure(0,weight=1)
        card.rowconfigure(1,weight=1)

        top=tk.Frame(card,bg=PANEL)
        top.grid(row=0,column=0,sticky="ew",padx=18,pady=15)
        top.columnconfigure(0,weight=1)
        self.entry=tk.Entry(top,font=("Malgun Gothic",11),relief="flat",bg=BLUE2,fg=TEXT)
        self.entry.grid(row=0,column=0,sticky="ew",ipady=10)
        self.time=tk.Entry(top,font=("Malgun Gothic",10),width=8,justify="center",
                           relief="flat",bg=BLUE2,fg=TEXT)
        self.time.insert(0,"시간")
        self.time.grid(row=0,column=1,padx=8,ipady=10)
        tk.Button(top,text="+ 추가",command=self.add_task,bg=BLUE,fg="white",relief="flat",
                  font=("Malgun Gothic",10,"bold"),padx=18,pady=9).grid(row=0,column=2)
        self.entry.bind("<Return>",lambda e:self.add_task())

        self.list=tk.Frame(card,bg=PANEL)
        self.list.grid(row=1,column=0,sticky="nsew",padx=18,pady=(0,15))

        # RIGHT
        right=tk.Frame(self,bg=PANEL,width=325,highlightthickness=1,highlightbackground=BORDER)
        right.grid(row=0,column=2,sticky="nse",padx=(0,18),pady=18)
        right.grid_propagate(False)

        self.calbox=tk.Frame(right,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.calbox.pack(fill="x")

        self.summary=tk.Frame(right,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.summary.pack(fill="x",pady=(14,0))

        self.mood=tk.Frame(right,bg=BLUE2,highlightthickness=1,highlightbackground=BORDER,width=315,height=230)
        self.mood.pack(fill="x",pady=(14,0))
        self.mood.pack_propagate(False)

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
        self.sub.config(text=f"{left}의 할 일   ·   {SKIN_COPY[self.skin_name][0]}")
        for x in self.list.winfo_children(): x.destroy()
        rows=self.conn.execute("SELECT id,title,task_time,memo,done FROM tasks WHERE task_date=? ORDER BY done, CASE WHEN task_time='' THEN '99:99' ELSE task_time END,id",(self.selected.isoformat(),)).fetchall()
        if not rows:
            tk.Label(self.list,text="아직 등록된 할 일이 없어요.\n위에서 첫 할 일을 추가해 보세요.",bg=PANEL,fg=MUTED,font=("Malgun Gothic",11),pady=55).pack()
        for tid,title,tm,memo,done in rows:
            r=tk.Frame(self.list,bg=BLUE2,highlightthickness=1,highlightbackground=BORDER); r.pack(fill="x",pady=4,ipady=3)
            tk.Button(r,text="✓" if done else "□",command=lambda i=tid,d=done:self.toggle(i,d),relief="flat",bg=BLUE2,fg=BLUE,font=("Malgun Gothic",13)).pack(side="left",padx=(7,0))
            lab=tk.Label(r,text=title,bg=BLUE2,fg=DONE if done else TEXT,font=("Malgun Gothic",11),anchor="w")
            lab.pack(side="left",fill="x",expand=True,padx=6)
            if tm:
                tk.Label(r,text=tm,bg=BLUE2,fg=MUTED,font=("Malgun Gothic",10)).pack(side="right",padx=(6,8))
            tk.Button(r,text="수정",command=lambda i=tid,t=title,tt=tm,m=memo:self.edit(i,t,tt,m),relief="flat",bg=BLUE2,fg=MUTED).pack(side="right")
            tk.Button(r,text="삭제",command=lambda i=tid:self.delete(i),relief="flat",bg=BLUE2,fg=MUTED).pack(side="right")
        self.draw_calendar(); self.draw_summary()

    def draw_calendar(self):
        for x in self.calbox.winfo_children(): x.destroy()
        nav=tk.Frame(self.calbox,bg=PANEL); nav.pack(fill="x",padx=12,pady=(12,6))
        tk.Button(nav,text="‹",command=lambda:self.shift_month(-1),relief="flat",bg=PANEL,fg=TEXT).pack(side="left")
        tk.Label(nav,text=f"{self.cal_year}년 {self.cal_month}월",bg=PANEL,fg=TEXT,font=("Malgun Gothic",11,"bold")).pack(side="left",expand=True)
        tk.Button(nav,text="›",command=lambda:self.shift_month(1),relief="flat",bg=PANEL,fg=TEXT).pack(side="right")
        grid=tk.Frame(self.calbox,bg=PANEL); grid.pack(padx=10,pady=(0,12))
        for c,n in enumerate(["월","화","수","목","금","토","일"]):
            tk.Label(grid,text=n,bg=PANEL,fg=MUTED,width=4,font=("Malgun Gothic",9)).grid(row=0,column=c,pady=3)
        weeks=calendar.Calendar(firstweekday=0).monthdayscalendar(self.cal_year,self.cal_month)
        for rr,wk in enumerate(weeks,1):
            for cc,d in enumerate(wk):
                if not d: continue
                dt=date(self.cal_year,self.cal_month,d)
                cnt=self.conn.execute("SELECT COUNT(*) FROM tasks WHERE task_date=?",(dt.isoformat(),)).fetchone()[0]
                txt=str(d)+(" •" if cnt else "")
                bg=BLUE if dt==self.selected else PANEL; fg="white" if dt==self.selected else TEXT
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
        tk.Label(self.summary,text="오늘 일정",font=("Malgun Gothic",12,"bold"),bg=PANEL,fg=TEXT).pack(anchor="w",padx=16,pady=(15,8))
        rows=self.conn.execute("SELECT title,task_time,done FROM tasks WHERE task_date=? ORDER BY task_time",(date.today().isoformat(),)).fetchall()
        if not rows:
            tk.Label(self.summary,text="오늘 일정이 없어요.",bg=PANEL,fg=MUTED).pack(anchor="w",padx=16,pady=8)
        for title,tm,done in rows[:9]:
            tk.Label(self.summary,text=f"{'✓' if done else '•'} {tm+'  ' if tm else ''}{title}",bg=PANEL,fg=DONE if done else TEXT,
                     font=("Malgun Gothic",9),anchor="w",wraplength=265,justify="left").pack(fill="x",padx=16,pady=4)

if __name__=="__main__":
    App().mainloop()
