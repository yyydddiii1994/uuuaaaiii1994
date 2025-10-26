import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk, ImageGrab
import io
import turtle
import sys # For command-line arguments

SIMULATION_DATA = [
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
        "image_url": "" # Fallback to turtle
    },
    # ... (rest of the data remains the same)
    {
        "card": "【専門競技対決】キプトゥム（マラソン王者） vs ソロキン（24時間走王者）",
        "winner": "キプトゥム（マラソン王者）",
        "reason": "土俵がマラソン（スピード）のため、専門家であるキプトゥム氏が圧勝。",
        "image_url": "" # Fallback to turtle
    }
]

class SimulationApp(tk.Tk):
    def __init__(self, test_mode=False):
        super().__init__()
        self.title("対戦シミュレーション")
        self.geometry("1000x600")

        self.sim_data = SIMULATION_DATA
        self.photo_image = None # To prevent garbage collection

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
            return

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

        if "F1" in card_text or "GT-R" in card_text:
            self.draw_race_car(pen)
        elif "アンパンマン号" in card_text:
            self.draw_anpanman_car(pen)
        elif "自転車" in card_text:
            self.draw_bicycle(pen)
        elif "徒歩" in card_text or "ボルト" in card_text or "キプトゥム" in card_text or "ソロキン" in card_text:
            self.draw_runner(pen)
        else:
            pen.penup()
            pen.goto(0, -10)
            pen.write("画像がありません", align="center", font=("Yu Gothic UI", 20, "normal"))

    def draw_race_car(self, pen):
        # (Drawing functions remain the same)
        pen.penup()
        pen.goto(-150, -30)
        pen.setheading(0)
        pen.pendown()
        pen.fillcolor("red")
        pen.begin_fill()
        # Body
        pen.forward(300)
        pen.left(90)
        pen.forward(50)
        pen.left(90)
        pen.forward(300)
        pen.left(90)
        pen.forward(50)
        pen.end_fill()
        # Cockpit
        pen.penup()
        pen.goto(-50, 20)
        pen.pendown()
        pen.fillcolor("white")
        pen.begin_fill()
        pen.circle(30)
        pen.end_fill()
        # Wheels
        for i in [-100, 100]:
            pen.penup()
            pen.goto(i, -50)
            pen.pendown()
            pen.fillcolor("black")
            pen.begin_fill()
            pen.circle(20)
            pen.end_fill()

    def draw_anpanman_car(self, pen):
        # (Drawing functions remain the same)
        pen.penup()
        pen.goto(0, -100)
        pen.pendown()
        pen.fillcolor("#FAD5A5")
        pen.begin_fill()
        pen.circle(100)
        pen.end_fill()
        # Cheeks
        for i in [-60, 60]:
            pen.penup()
            pen.goto(i, 20)
            pen.pendown()
            pen.fillcolor("#E84A5F")
            pen.begin_fill()
            pen.circle(25)
            pen.end_fill()
        # Nose (center)
        pen.penup()
        pen.goto(0, 40)
        pen.pendown()
        pen.dot(50, "#E84A5F")
        # Eyes
        for i in [-40, 40]:
            pen.penup()
            pen.goto(i, 80)
            pen.pendown()
            pen.dot(15, "black")

    def draw_bicycle(self, pen):
        # (Drawing functions remain the same)
        pen.penup()
        # Wheels
        pen.goto(-50, -50)
        pen.pendown()
        pen.circle(30)
        pen.penup()
        pen.goto(50, -50)
        pen.pendown()
        pen.circle(30)
        # Frame
        pen.penup()
        pen.goto(-50, -20)
        pen.pendown()
        pen.goto(0, 30)
        pen.goto(50, -20)
        pen.goto(-20, -20)
        # Handlebars and seat
        pen.goto(0, 30)
        pen.goto(10, 40)
        pen.penup()
        pen.goto(-30, 20)
        pen.pendown()
        pen.forward(20)

    def draw_runner(self, pen):
        # (Drawing functions remain the same)
        pen.penup()
        pen.goto(0, 50)
        pen.pendown()
        pen.begin_fill()
        pen.circle(20)
        pen.end_fill()
        # Body
        pen.penup()
        pen.goto(0, 50)
        pen.pendown()
        pen.goto(0, -20)
        # Legs
        pen.goto(-30, -70)
        pen.penup()
        pen.goto(0, -20)
        pen.pendown()
        pen.goto(30, -70)
        # Arms
        pen.penup()
        pen.goto(0, 30)
        pen.pendown()
        pen.goto(-40, 10)
        pen.penup()
        pen.goto(0, 30)
        pen.pendown()
        pen.goto(40, 10)

if __name__ == "__main__":
    test_mode = "--test" in sys.argv
    app = SimulationApp(test_mode=test_mode)
    if not test_mode:
        app.mainloop()
