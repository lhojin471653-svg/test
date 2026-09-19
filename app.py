# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, calendar
import winsound
import sys
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

THEMES = {
    "기본": {"bg":"#F5F8FC","panel":"#FFFFFF","accent":"#4D9BE6","soft":"#EAF4FF","text":"#243447","muted":"#7A8A9A","border":"#DCE6F0","done":"#A8B2BC"},
    "감성": {"bg":"#F8F0E6","panel":"#FFF9F2","accent":"#C98E68","soft":"#F5E5D6","text":"#4A382E","muted":"#9A8172","border":"#E8D4C2","done":"#B8A79C"},
    "블러썸": {"bg":"#FFF1F5","panel":"#FFF9FB","accent":"#ED7597","soft":"#FFE0E9","text":"#55343E","muted":"#A77A87","border":"#F2CAD6","done":"#C5A6AF"},
    "다크": {"bg":"#101B28","panel":"#172536","accent":"#4D91D9","soft":"#203A55","text":"#F1F5F9","muted":"#9DB0C3","border":"#294058","done":"#718399"},
    "드림": {"bg":"#EAF7FF","panel":"#F8FCFF","accent":"#46A5EE","soft":"#D8F0FF","text":"#174B76","muted":"#6992B2","border":"#BFE3F7","done":"#8DB3CB"},
    "우드": {"bg":"#3A281B","panel":"#513722","accent":"#8DB55B","soft":"#684A31","text":"#FFF6E9","muted":"#D1B99C","border":"#75573A","done":"#AE9A83"}
}
THEME_ASSETS = {
    "기본": "assets/basic_bg.jpg",
    "감성": "assets/emotional_bg.jpg",
    "블러썸": "assets/blossom_bg.jpg",
    "다크": "assets/dark_bg.jpg",
    "드림": "assets/dream_bg.jpg",
    "우드": "assets/wood_bg.jpg",
}
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
        self.title(APP_TITLE+" v0.9")
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
        self.apply_background_asset()
        self.refresh()
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
        # 개발 실행 / PyInstaller onefile 실행 모두 지원
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base=Path(sys._MEIPASS)
        else:
            base=Path(__file__).resolve().parent
        p=base / rel
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
        """확정 시안처럼 스킨 이미지를 전체 앱 분위기에 적용한다."""
        rel=THEME_ASSETS.get(self.skin_name,"")
        p=self.asset_path(rel)
        self._bg_photo=None
        self._hero_photo=None
        if not p or not PIL_OK:
            return
        try:
            self.update_idletasks()

            # 1. 창 전체에 스킨 배경 적용
            w=max(self.winfo_width(),1100)
            h=max(self.winfo_height(),700)
            bg=self.cover_image(p,w,h,0.10 if self.skin_name!="다크" else 0.02)
            # 본문 가독성을 위해 부드러운 밝은/어두운 베일
            from PIL import ImageDraw
            veil=Image.new("RGBA",(w,h),(0,0,0,0))
            vd=ImageDraw.Draw(veil)
            if self.skin_name in ("다크","우드"):
                vd.rectangle((0,0,w,h),fill=(5,10,18,70))
            else:
                vd.rectangle((0,0,w,h),fill=(255,255,255,105))
            bg=Image.alpha_composite(bg.convert("RGBA"),veil)
            self._bg_photo=ImageTk.PhotoImage(bg)
            self.bg_layer.configure(image=self._bg_photo)

            # 2. 우측 하단 히어로 카드에는 이미지 원색을 더 강하게 표시
            hw=max(self.mood.winfo_width(),315)
            hh=max(self.mood.winfo_height(),150)
            hero=self.cover_image(p,hw,hh,0)
            shade=Image.new("RGBA",(hw,hh),(0,0,0,0))
            sd=ImageDraw.Draw(shade)
            for y in range(hh):
                if y>hh*0.42:
                    a=int(145*((y-hh*0.42)/(hh*0.58)))
                    sd.line((0,y,hw,y),fill=(0,0,0,a))
            hero=Image.alpha_composite(hero.convert("RGBA"),shade)
            self._hero_photo=ImageTk.PhotoImage(hero)
            for child in self.mood.winfo_children():
                child.destroy()
            tk.Label(self.mood,image=self._hero_photo,borderwidth=0).place(x=0,y=0,relwidth=1,relheight=1)
            msg=SKIN_COPY[self.skin_name][1].replace("\n","  ")
            tk.Label(self.mood,text=msg,bg="#202833",fg="white",
                     font=("Malgun Gothic",9,"bold"),anchor="w",
                     padx=10,pady=5).place(relx=.04,rely=.70,relwidth=.92)
        except Exception as e:
            print("skin asset error:",e)

    def on_resize(self,event=None):
        if getattr(self,"_resize_job",None):
            try:self.after_cancel(self._resize_job)
            except:pass
        self._resize_job=self.after(180,self.apply_background_asset)

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
        names=list(THEMES.keys())
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
        self.apply_background_asset()
        self.refresh()

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
        self.columnconfigure(1,weight=1); self.rowconfigure(0,weight=1)

        # 스킨 전체 배경 레이어
        self.bg_layer=tk.Label(self,bg=BG,borderwidth=0)
        self.bg_layer.place(x=0,y=0,relwidth=1,relheight=1)
        self.bg_layer.lower()
        self.bind("<Configure>",self.on_resize)

        side=tk.Frame(self,bg=PANEL,width=180,highlightthickness=1,highlightbackground=BORDER)
        side.grid(row=0,column=0,sticky="nsw"); side.grid_propagate(False)
        tk.Label(side,text="✓  오늘 할 일",font=("Malgun Gothic",17,"bold"),bg=PANEL,fg=TEXT).pack(pady=(28,6))
        tk.Label(side,text=f"{self.skin_name} SKIN",font=("Malgun Gothic",8,"bold"),bg=PANEL,fg=BLUE).pack(pady=(0,20))
        for txt,cmd in [("⌂  오늘",self.go_today),("▣  내일",self.go_tomorrow),("□  일정",self.focus_calendar),("▤  메모",self.show_memos),("⚙  설정",self.choose_skin)]:
            active = txt.endswith("오늘")
            tk.Button(side,text=txt,command=cmd,anchor="w",relief="flat",bd=0,
                      bg=BLUE2 if active else PANEL,fg=BLUE if active else TEXT,
                      activebackground=BLUE2,font=("Malgun Gothic",11,"bold" if active else "normal"),
                      padx=24,pady=12).pack(fill="x",padx=10,pady=2)
        tk.Label(side,text=f"{self.skin_name} 스킨\n오늘도 좋은 하루 되세요! :)",bg=PANEL,fg=MUTED,
                 font=("Malgun Gothic",9),justify="left").pack(side="bottom",pady=20,padx=18,anchor="w")

        center=tk.Frame(self,bg=PANEL,highlightthickness=1,highlightbackground=BORDER); center.grid(row=0,column=1,sticky="nsew",padx=22,pady=22)
        center.columnconfigure(0,weight=1); center.rowconfigure(2,weight=1)
        self.head=tk.Label(center,text="",font=("Malgun Gothic",23,"bold"),bg=PANEL,fg=TEXT,anchor="w")
        self.head.grid(row=0,column=0,sticky="ew")
        self.sub=tk.Label(center,text="",font=("Malgun Gothic",10),bg=PANEL,fg=MUTED,anchor="w")
        self.sub.grid(row=1,column=0,sticky="ew",pady=(2,18))

        card=tk.Frame(center,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        card.grid(row=2,column=0,sticky="nsew"); card.columnconfigure(0,weight=1); card.rowconfigure(1,weight=1)
        top=tk.Frame(card,bg=PANEL); top.grid(row=0,column=0,sticky="ew",padx=18,pady=15); top.columnconfigure(0,weight=1)
        self.entry=tk.Entry(top,font=("Malgun Gothic",11),relief="flat",bg=BLUE2,fg=TEXT)
        self.entry.grid(row=0,column=0,sticky="ew",ipady=10)
        self.time=tk.Entry(top,font=("Malgun Gothic",10),width=8,justify="center",relief="flat",bg=BLUE2,fg=TEXT)
        self.time.insert(0,"시간")
        self.time.grid(row=0,column=1,padx=8,ipady=10)
        tk.Button(top,text="+ 추가",command=self.add_task,bg=BLUE,fg="white",relief="flat",
                  font=("Malgun Gothic",10,"bold"),padx=18,pady=9).grid(row=0,column=2)
        self.entry.bind("<Return>",lambda e:self.add_task())

        self.list=tk.Frame(card,bg=PANEL)
        self.list.grid(row=1,column=0,sticky="nsew",padx=18,pady=(0,15))

        right=tk.Frame(self,bg=PANEL,width=315,highlightthickness=1,highlightbackground=BORDER)
        right.grid(row=0,column=2,sticky="nse",padx=(0,22),pady=22); right.grid_propagate(False)
        self.calbox=tk.Frame(right,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.calbox.pack(fill="x")
        self.summary=tk.Frame(right,bg=PANEL,highlightthickness=1,highlightbackground=BORDER)
        self.summary.pack(fill="both",expand=True,pady=(16,0))
        self.mood=tk.Frame(right,bg=BLUE2,highlightthickness=1,highlightbackground=BORDER,height=165)
        self.mood.pack(fill="x",pady=(16,0))
        self.mood.pack_propagate(False)
        tk.Label(self.mood,text=SKIN_COPY[self.skin_name][1],bg=BLUE2,fg=TEXT,
                 font=("Malgun Gothic",10),justify="left",anchor="w").pack(fill="both",expand=True,padx=18,pady=14)

    def go_today(self): self.selected=date.today(); self.cal_year=self.selected.year; self.cal_month=self.selected.month; self.refresh()
    def go_tomorrow(self): self.selected=date.today()+timedelta(days=1); self.cal_year=self.selected.year; self.cal_month=self.selected.month; self.refresh()
    def focus_calendar(self): self.calbox.focus_set()
    def show_memos(self):
        rows=self.conn.execute("SELECT task_date,title,memo FROM tasks WHERE memo<>'' ORDER BY task_date DESC").fetchall()
        messagebox.showinfo("메모", "\n\n".join(f"{d} · {t}\n{m}" for d,t,m in rows) or "저장된 메모가 없어요.")

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
