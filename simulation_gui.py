import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk, ImageGrab
import io
import turtle
import sys

SIMULATION_DATA = [
    # --- Original Data ---
    {
        "card": "F1（プロ） vs 軽乗用車（プロ）",
        "winner": "軽乗用車（プロ）",
        "reason": "F1マシンは素人には発進すら困難。プロが扱う軽自動車に勝てない。",
        "image_url": "https://media.formula1.com/image/upload/f_auto,c_limit,w_960,q_auto/f_public/content/dam/fom-website/2024/Races/R01-Bahrain/GettyImages-2086053321"
    },
    {
        "card": "アンパンマン号（F1レーサー） vs 徒歩（素人）",
        "winner": "徒歩（素人）",
        "reason": "アンパンマン号のリミッター（時速8km程度）が、人間の走力（時速10km以上）より遅いため。",
        "image_url": ""
    },
    {
        "card": "アンパンマン号（F1レーサーA） vs アンパンマン号（F1レーサーB）",
        "winner": "引き分け（または僅差）",
        "reason": "全車リミッターで速度が同じ。駆け引きとライン取り勝負。",
        "image_url": ""
    },
    {
        "card": "シルバーカー（手押し車）（F1レーサー） vs シルバーカー（手押し車）（熟練高齢者）",
        "winner": "F1レーサー",
        "reason": "動力がないため純粋な徒競走。アスリート（F1）が高齢者に圧勝。",
        "image_url": "https://2.bp.blogspot.com/-_6Gf_s-I5Ww/U3s0-e-t-sI/AAAAAAAAgsE/T2Q9v0qbv5M/s800/car_senior.png"
    },
    {
        "card": "【軽乗用車 ル・マン24時間】軽乗用車（F1レーサー） vs GT-R（素人）",
        "winner": "軽乗用車（F1レーサー）",
        "reason": "素人はGT-Rの性能に耐えられず、夜間に疲労でクラッシュ（リタイア）する可能性が極めて高い。",
        "image_url": "https://www.motortrend.com/uploads/2022/10/2024-Nissan-GT-R-JDM-front-three-quarters-in-motion-1.jpg"
    },
    {
        "card": "【100km走 自転車対決】ママチャリ（プロレーサー） vs Trek Madone（小学生）",
        "winner": "ママチャリ（プロレーサー）",
        "reason": "100kmという距離では、機材の差より「プロと子供の体力差」が圧倒的。プロが圧勝。",
        "image_url": "https://www.cb-asahi.co.jp/lp/product/ownbrand/always/img/main.png"
    },
    {
        "card": "シニアカー（F1） vs 自力走行（キプトゥム/万全）",
        "winner": "自力走行（キプトゥム）",
        "reason": "マラソン王者の持久力（平均時速5.8km以上を維持）が、シニアカーの平均速度（ピットロス込で約5.79km）を上回る。",
        "image_url": ""
    },
    # --- Expanded Data ---
    {
        "card": "【究極のチャーハン対決】中華の達人 vs 家庭用自動調理器",
        "winner": "中華の達人",
        "reason": "プロの火力と絶妙な鍋振りは、現在の家庭用調理器では再現不可能。食感と香りが段違い。",
        "image_url": ""
    },
    {
        "card": "【おにぎり早握り対決】熟練パートタイマー vs 寿司ロボット",
        "winner": "寿司ロボット",
        "reason": "品質の安定性と、休憩なしで稼働し続けられる持久力でロボットが圧勝する。",
        "image_url": ""
    },
    {
        "card": "【エベレスト登頂】プロ登山家 vs スーパー大鷲（荷物運搬役）",
        "winner": "プロ登山家",
        "reason": "鷲は高地の低酸素環境に適応できず、荷物を運べても人間本体の登頂は不可能。",
        "image_url": ""
    },
    {
        "card": "【無人島サバイバル対決】元特殊部隊員 vs チンパンジー",
        "winner": "チンパンジー",
        "reason": "森林環境への適応力、身体能力、食料確保の知識でチンパンジーが圧倒的に有利。",
        "image_url": ""
    },
    {
        "card": "【将棋対決】藤井聡太 vs 最強将棋AI",
        "winner": "最強将棋AI",
        "reason": "AIの膨大な計算力とミスをしない正確性は、人間のトップ棋士をも凌駕する。",
        "image_url": ""
    },
    {
        "card": "【作曲対決】ベートーヴェン vs 最新作曲AI",
        "winner": "ベートーヴェン",
        "reason": "AIは既存曲のパターン学習は得意だが、時代を創造する革新的な芸術性は人間にしか生み出せない。",
        "image_url": ""
    },
    {
        "card": "【かくれんぼ対決】忍者 vs カメレオン",
        "winner": "カメレオン",
        "reason": "忍者の技術も達人の域だが、カメレオンの保護色は生物として究極の隠蔽能力。",
        "image_url": ""
    },
    {
        "card": "【大食い対決】ジャイアント白田 vs シロナガスクジラ",
        "winner": "シロナガスクジラ",
        "reason": "一度に数トンのオキアミを丸呑みするクジラの捕食量は、人間の大食い王とは比較にならない。",
        "image_url": ""
    },
    {
        "card": "【長距離移動】アフリカゾウ vs 路線バス",
        "winner": "路線バス",
        "reason": "舗装路を一定速度で走り続け、燃料補給も容易なバスの効率と速度には、生物では太刀打ちできない。",
        "image_url": ""
    }
]


class SimulationApp(tk.Tk):
    def __init__(self, test_mode=False):
        super().__init__()
        self.title("対戦シミュレーション")
        self.geometry("1000x600")

        self.sim_data = SIMULATION_DATA
        self.photo_image = None

        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_pane, width=300, height=600)
        main_pane.add(left_frame, weight=1)

        right_frame = ttk.Frame(main_pane, width=700, height=600)
        main_pane.add(right_frame, weight=3)

        list_label = ttk.Label(left_frame, text="対戦カード一覧")
        list_label.pack(pady=5)

        self.sim_listbox = tk.Listbox(left_frame, font=("Yu Gothic UI", 12))
        self.sim_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.sim_listbox.bind("<<ListboxSelect>>", self.show_details)

        scrollbar = ttk.Scrollbar(self.sim_listbox, orient=tk.VERTICAL, command=self.sim_listbox.yview)
        self.sim_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        details_frame = ttk.Frame(right_frame)
        details_frame.pack(fill=tk.X, padx=10, pady=10)

        self.title_label = ttk.Label(details_frame, text="対戦カード: ", font=("Yu Gothic UI", 16, "bold"))
        self.title_label.pack(anchor="w")

        self.winner_label = ttk.Label(details_frame, text="勝利予想: ", font=("Yu Gothic UI", 12))
        self.winner_label.pack(anchor="w", pady=5)

        self.reason_label = ttk.Label(details_frame, text="勝因: ", font=("Yu Gothic UI", 12), wraplength=650, justify=tk.LEFT)
        self.reason_label.pack(anchor="w")

        self.image_canvas = tk.Canvas(right_frame, bg="white", width=680, height=400)
        self.image_canvas.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.turtle_screen = turtle.TurtleScreen(self.image_canvas)
        self.turtle_pen = turtle.RawTurtle(self.turtle_screen)
        self.turtle_pen.hideturtle()

        self.populate_listbox()
        self.show_details(None)

        if test_mode:
            self.after(2000, self.take_screenshot_and_exit)

    def take_screenshot_and_exit(self):
        x = self.winfo_rootx()
        y = self.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save("simulation_gui.png")
        self.destroy()

    def populate_listbox(self):
        for item in self.sim_data:
            self.sim_listbox.insert(tk.END, item["card"])
        self.sim_listbox.selection_set(0)

    def show_details(self, event):
        selected_indices = self.sim_listbox.curselection()
        if not selected_indices:
            if not self.sim_listbox.get(0): return
            self.sim_listbox.selection_set(0)
            selected_indices = (0,)

        selected_index = selected_indices[0]
        selected_sim = self.sim_data[selected_index]

        self.title_label.config(text=f"対戦カード: {selected_sim['card']}")
        self.winner_label.config(text=f"勝利予想: {selected_sim['winner']}")
        self.reason_label.config(text=f"勝因: {selected_sim['reason']}")

        self.update_image(selected_sim)

    def update_image(self, sim_data):
        self.image_canvas.delete("all")
        self.turtle_pen.reset()
        self.turtle_pen.hideturtle()

        url = sim_data.get("image_url")
        if url:
            try:
                response = requests.get(url, stream=True, timeout=5)
                response.raise_for_status()
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))

                self.image_canvas.update_idletasks()
                canvas_width = self.image_canvas.winfo_width()
                canvas_height = self.image_canvas.winfo_height()
                image.thumbnail((canvas_width - 20, canvas_height - 20), Image.Resampling.LANCZOS)

                self.photo_image = ImageTk.PhotoImage(image)
                self.image_canvas.create_image(canvas_width / 2, canvas_height / 2, image=self.photo_image)
                return
            except Exception as e:
                print(f"画像読み込みエラー: {e}")

        self.draw_fallback_image(sim_data["card"])

    def draw_fallback_image(self, card_text):
        pen = self.turtle_pen
        pen.speed(0)

        if "中華の達人" in card_text or "調理器" in card_text: self.draw_chef(pen)
        elif "おにぎり" in card_text: self.draw_onigiri(pen)
        elif "登山家" in card_text or "エベレスト" in card_text: self.draw_mountain(pen)
        elif "サバイバル" in card_text or "チンパンジー" in card_text or "ゾウ" in card_text or "クジラ" in card_text: self.draw_animal(pen, card_text)
        elif "将棋" in card_text or "藤井聡太" in card_text: self.draw_shogi_piece(pen)
        elif "AI" in card_text or "ロボット" in card_text: self.draw_robot(pen)
        elif "F1" in card_text or "GT-R" in card_text: self.draw_race_car(pen)
        elif "アンパンマン号" in card_text: self.draw_anpanman_car(pen)
        elif "自転車" in card_text: self.draw_bicycle(pen)
        elif "徒歩" in card_text or "ボルト" in card_text or "キプトゥム" in card_text: self.draw_runner(pen)
        else:
            pen.penup()
            pen.goto(0, 0)
            pen.write("代替画像なし", align="center", font=("Yu Gothic UI", 20, "normal"))

    def draw_race_car(self, pen):
        pen.penup(); pen.goto(-150, -30); pen.setheading(0); pen.pendown(); pen.fillcolor("red"); pen.begin_fill()
        pen.forward(300); pen.left(90); pen.forward(50); pen.left(90); pen.forward(300); pen.left(90); pen.forward(50); pen.end_fill()
        pen.penup(); pen.goto(-50, 20); pen.pendown(); pen.fillcolor("white"); pen.begin_fill(); pen.circle(30); pen.end_fill()
        for i in [-100, 100]:
            pen.penup(); pen.goto(i, -50); pen.pendown(); pen.fillcolor("black"); pen.begin_fill(); pen.circle(20); pen.end_fill()

    def draw_anpanman_car(self, pen):
        pen.penup(); pen.goto(0, -100); pen.pendown(); pen.fillcolor("#FAD5A5"); pen.begin_fill(); pen.circle(100); pen.end_fill()
        for i in [-60, 60]:
            pen.penup(); pen.goto(i, 20); pen.pendown(); pen.fillcolor("#E84A5F"); pen.begin_fill(); pen.circle(25); pen.end_fill()
        pen.penup(); pen.goto(0, 40); pen.pendown(); pen.dot(50, "#E84A5F")
        for i in [-40, 40]:
            pen.penup(); pen.goto(i, 80); pen.pendown(); pen.dot(15, "black")

    def draw_bicycle(self, pen):
        pen.penup(); pen.goto(-50, -50); pen.pendown(); pen.circle(30); pen.penup(); pen.goto(50, -50); pen.pendown(); pen.circle(30)
        pen.penup(); pen.goto(-50, -20); pen.pendown(); pen.goto(0, 30); pen.goto(50, -20); pen.goto(-20, -20)
        pen.goto(0, 30); pen.goto(10, 40); pen.penup(); pen.goto(-30, 20); pen.pendown(); pen.forward(20)

    def draw_runner(self, pen):
        pen.penup(); pen.goto(0, 50); pen.pendown(); pen.begin_fill(); pen.circle(20); pen.end_fill()
        pen.penup(); pen.goto(0, 50); pen.pendown(); pen.goto(0, -20)
        pen.goto(-30, -70); pen.penup(); pen.goto(0, -20); pen.pendown(); pen.goto(30, -70)
        pen.penup(); pen.goto(0, 30); pen.pendown(); pen.goto(-40, 10); pen.penup(); pen.goto(0, 30); pen.pendown(); pen.goto(40, 10)

    def draw_chef(self, pen):
        pen.penup(); pen.goto(0, 20); pen.pendown(); pen.fillcolor("white"); pen.begin_fill() # Hat
        pen.setheading(90); pen.circle(40, 180); pen.forward(20); pen.circle(40, 180); pen.forward(20); pen.end_fill()
        self.draw_runner(pen)

    def draw_onigiri(self, pen):
        pen.penup(); pen.goto(0, -50); pen.pendown(); pen.fillcolor("white"); pen.begin_fill()
        pen.goto(-60, 20); pen.goto(60, 20); pen.goto(0, -50); pen.end_fill()
        pen.penup(); pen.goto(-30, -50); pen.pendown(); pen.fillcolor("black"); pen.begin_fill()
        pen.goto(30, -50); pen.goto(20, -20); pen.goto(-20, -20); pen.end_fill()

    def draw_mountain(self, pen):
        pen.penup(); pen.goto(-150, -80); pen.pendown(); pen.fillcolor("grey"); pen.begin_fill()
        pen.goto(0, 100); pen.goto(150, -80); pen.goto(-150, -80); pen.end_fill()
        pen.penup(); pen.goto(-50, 20); pen.pendown(); pen.fillcolor("white"); pen.begin_fill()
        pen.goto(0, 100); pen.goto(50, 20); pen.goto(-50, 20); pen.end_fill()

    def draw_robot(self, pen):
        pen.penup(); pen.goto(-50, 0); pen.pendown(); pen.fillcolor("silver"); pen.begin_fill() # Head
        for _ in range(4): pen.forward(100); pen.left(90)
        pen.end_fill()
        pen.penup(); pen.goto(-25, 60); pen.pendown(); pen.dot(15, "red"); pen.penup(); pen.goto(25, 60); pen.pendown(); pen.dot(15, "red")
        pen.penup(); pen.goto(-50, 0); pen.pendown(); pen.goto(-70, -80); pen.penup(); pen.goto(50, 0); pen.pendown(); pen.goto(70, -80)

    def draw_shogi_piece(self, pen):
        pen.penup(); pen.goto(0, -80); pen.pendown(); pen.fillcolor("#F0D28C"); pen.begin_fill()
        pen.goto(-50, -60); pen.goto(-40, 50); pen.goto(40, 50); pen.goto(50, -60); pen.goto(0, -80)
        pen.end_fill()
        pen.penup(); pen.goto(0, -10); pen.write("王", align="center", font=("Yu Gothic UI", 40, "bold"))

    def draw_animal(self, pen, card_text):
        if "チンパンジー" in card_text: pen.fillcolor("brown")
        elif "ゾウ" in card_text: pen.fillcolor("grey")
        elif "クジラ" in card_text: pen.fillcolor("blue")
        else: pen.fillcolor("black")

        pen.penup(); pen.goto(0, -50)
        pen.pendown(); pen.begin_fill(); pen.circle(50); pen.end_fill() # Body
        pen.penup(); pen.goto(0, 0); pen.pendown(); pen.begin_fill(); pen.circle(30); pen.end_fill() # Head
        pen.penup(); pen.goto(-20, 20); pen.dot(10); pen.goto(20, 20); pen.dot(10) # Eyes


if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    app = SimulationApp(test_mode=test_mode)
    if not test_mode:
        app.mainloop()
