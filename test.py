#!/usr/bin/env python3
"""
Reversi (黑白棋) GUI with special "return one piece" rule and per‑turn timing
----------------------------------------------------------------------
- 規則：標準 8×8 Reversi，X 先手。
- 特殊：若本手翻轉對手 >=3 子，隨機返還其中 1 子。
- 時間：每回合 60 秒；若超時且延長次數剩餘，
        自動或手動延長一次再 +60 秒 (每方 3 次)。
- 操作：滑鼠點擊合法落點；* 號標示可下點。
- 文字輸出：於右側 LOG 與終端顯示走法 (含返還或 PASS)。
"""

import tkinter as tk
from tkinter import messagebox
import random

CELL_SIZE = 60          # 單格像素尺寸
BOARD_SIZE = 8          # 8×8 棋盤
BACKGROUND_COLOR = "#006400"  # 深綠色


class ReversiGame:
    """核心棋局邏輯：棋盤資料、合法步、翻轉與返還、終局判定。"""

    def __init__(self):
        self.board = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = "X"
        self.extensions = {"X": 3, "O": 3}  # 每方延長次數
        self.init_board()

    # --- 基本工具 --------------------------------------------------
    @staticmethod
    def opponent(player: str) -> str:
        return "O" if player == "X" else "X"

    @staticmethod
    def inside(r: int, c: int) -> bool:
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    # --- 初始化與合法步 --------------------------------------------
    def init_board(self):
        self.board[3][3] = self.board[4][4] = "X"
        self.board[3][4] = self.board[4][3] = "O"

    def get_flips(self, player: str, r: int, c: int):
        """回傳此處落子可翻轉的座標 list；若為空表示非法。"""
        opp = self.opponent(player)
        flips_total = []
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        ]
        for dr, dc in directions:
            flips = []
            x, y = r + dr, c + dc
            if not self.inside(x, y) or self.board[x][y] != opp:
                continue
            while self.inside(x, y) and self.board[x][y] == opp:
                flips.append((x, y))
                x += dr
                y += dc
            if self.inside(x, y) and self.board[x][y] == player and flips:
                flips_total.extend(flips)
        return flips_total

    def get_valid_moves(self, player: str):
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == "." and self.get_flips(player, r, c):
                    moves.append((r, c))
        return moves

    # --- 落子、翻轉、返還 ------------------------------------------
    def make_move(self, player: str, r: int, c: int):
        flips = self.get_flips(player, r, c)
        if not flips:
            return None, None  # 不合法 (應不會發生)
        self.board[r][c] = player
        for fx, fy in flips:
            self.board[fx][fy] = player

        return_pos = None
        if len(flips) >= 3:  # 觸發返還規則
            return_pos = random.choice(flips)
            rx, ry = return_pos
            self.board[rx][ry] = self.opponent(player)
        return flips, return_pos

    # --- 計算比分與終局 -------------------------------------------
    def count_pieces(self):
        x_cnt = sum(row.count("X") for row in self.board)
        o_cnt = sum(row.count("O") for row in self.board)
        return x_cnt, o_cnt

    def game_over(self):
        full = all(cell != "." for row in self.board for cell in row)
        if full:
            return True
        x_cnt, o_cnt = self.count_pieces()
        if x_cnt == 0 or o_cnt == 0:
            return True
        if not self.get_valid_moves("X") and not self.get_valid_moves("O"):
            return True
        return False


class ReversiGUI:
    """tkinter 視圖與互動層，包含計時與延長邏輯。"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Reversi with Return Rule")
        self.game = ReversiGame()

        # --- 介面元件 --------------------------------------------
        self.canvas = tk.Canvas(
            root,
            width=CELL_SIZE * BOARD_SIZE,
            height=CELL_SIZE * BOARD_SIZE,
            bg=BACKGROUND_COLOR,
        )
        self.canvas.grid(row=0, column=0, rowspan=20)
        self.canvas.bind("<Button-1>", self.handle_click)

        self.status = tk.Label(root, font=("Helvetica", 14))
        self.status.grid(row=0, column=1, sticky="w")

        self.timer_label = tk.Label(root, font=("Helvetica", 14))
        self.timer_label.grid(row=1, column=1, sticky="w")

        self.extension_label = tk.Label(root, font=("Helvetica", 14))
        self.extension_label.grid(row=2, column=1, sticky="w")

        self.score_label = tk.Label(root, font=("Helvetica", 14))
        self.score_label.grid(row=3, column=1, sticky="w")

        self.log_text = tk.Text(root, width=30, height=15, state="disabled")
        self.log_text.grid(row=4, column=1, rowspan=10, pady=10)

        self.extension_button = tk.Button(
            root, text="使用延長(+60s)", command=self.use_extension
        )
        self.extension_button.grid(row=15, column=1, sticky="we")

        # --- 計時狀態 -------------------------------------------
        self.timer_id = None
        self.time_left = 60

        # --- 畫棋盤 & 開局 --------------------------------------
        self.draw_board()        # 畫網格與初始棋子
        self.start_turn()        # X 先手開始

    # -----------------------------------------------------------------
    # 棋盤繪圖
    # -----------------------------------------------------------------
    def draw_board(self):
        size = CELL_SIZE
        for i in range(BOARD_SIZE + 1):  # 畫格線
            self.canvas.create_line(0, i * size, BOARD_SIZE * size, i * size, fill="black")
            self.canvas.create_line(i * size, 0, i * size, BOARD_SIZE * size, fill="black")
        self.update_board()

    def update_board(self):
        self.canvas.delete("piece")
        self.canvas.delete("star")
        size = CELL_SIZE
        margin = 4
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                val = self.game.board[r][c]
                if val in ("X", "O"):
                    x1 = c * size + margin
                    y1 = r * size + margin
                    x2 = (c + 1) * size - margin
                    y2 = (r + 1) * size - margin
                    color = "black" if val == "X" else "white"
                    self.canvas.create_oval(x1, y1, x2, y2, fill=color, tags="piece")
        self.highlight_moves()

    def highlight_moves(self):
        self.canvas.delete("star")
        moves = self.game.get_valid_moves(self.game.current_player)
        size = CELL_SIZE
        for r, c in moves:
            x = c * size + size // 2
            y = r * size + size // 2
            self.canvas.create_text(
                x, y, text="*", fill="yellow", font=("Helvetica", 16, "bold"), tags="star"
            )

    # -----------------------------------------------------------------
    # 滑鼠事件
    # -----------------------------------------------------------------
    def handle_click(self, event):
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        if (row, col) not in self.game.get_valid_moves(self.game.current_player):
            return  # 非合法

        self.stop_timer()  # 落子前停止計時器
        flips, return_pos = self.game.make_move(self.game.current_player, row, col)
        move_txt = f"{self.game.current_player}({row},{col})"
        if return_pos:
            move_txt += f"({return_pos[0]},{return_pos[1]})"
        self.log_move(move_txt)

        if self.game.game_over():
            self.finish_game()
            return
        self.switch_player()

    # -----------------------------------------------------------------
    # 回合切換 & PASS
    # -----------------------------------------------------------------
    def switch_player(self):
        self.game.current_player = self.game.opponent(self.game.current_player)
        if self.game.get_valid_moves(self.game.current_player):
            self.start_turn()
        else:  # PASS
            self.log_move("PASS")
            self.game.current_player = self.game.opponent(self.game.current_player)
            if not self.game.get_valid_moves(self.game.current_player):
                self.finish_game()
            else:
                self.start_turn()

    # -----------------------------------------------------------------
    # 計時與延長
    # -----------------------------------------------------------------
    def start_turn(self):
        self.update_board()
        self.update_score()
        self.time_left = 60
        self.update_status()
        self.tick()

    def tick(self):
        self.timer_label.config(text=f"剩餘時間: {self.time_left} 秒")
        if self.time_left == 0:
            self.handle_timeout()
            return
        self.time_left -= 1
        self.timer_id = self.root.after(1000, self.tick)

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def handle_timeout(self):
        player = self.game.current_player
        if self.game.extensions[player] > 0:
            # 自動使用延長
            self.game.extensions[player] -= 1
            self.time_left = 60
            self.update_status()
            self.tick()
        else:
            # 無延長，視為 PASS
            self.log_move("PASS")
            self.switch_player()

    def use_extension(self):
        player = self.game.current_player
        if self.game.extensions[player] == 0 or self.time_left >= 120:
            return
        self.game.extensions[player] -= 1
        self.time_left += 60
        if self.time_left > 120:
            self.time_left = 120
        self.update_status()

    # -----------------------------------------------------------------
    # 狀態、比分、日誌
    # -----------------------------------------------------------------
    def update_status(self):
        p = self.game.current_player
        self.status.config(text=f"當前玩家: {p}")
        self.extension_label.config(
            text=f"延長剩餘  X:{self.game.extensions['X']}  O:{self.game.extensions['O']}"
        )

    def update_score(self):
        x_cnt, o_cnt = self.game.count_pieces()
        self.score_label.config(text=f"X={x_cnt}  O={o_cnt}")

    def log_move(self, txt: str):
        self.log_text.config(state="normal")
        self.log_text.insert("end", txt + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        print(txt)  # 同步終端輸出

    # -----------------------------------------------------------------
    # 終局
    # -----------------------------------------------------------------
    def finish_game(self):
        self.stop_timer()
        self.update_board()
        x_cnt, o_cnt = self.game.count_pieces()
        if x_cnt > o_cnt:
            result = "X 獲勝"
        elif o_cnt > x_cnt:
            result = "O 獲勝"
        else:
            result = "平手"
        messagebox.showinfo("遊戲結束", f"X: {x_cnt}  O: {o_cnt}\n{result}")
        self.status.config(text="遊戲已結束")
        self.canvas.unbind("<Button-1>")


# ---------------------------------------------------------------------
# 主程式入口
# ---------------------------------------------------------------------

def main():
    root = tk.Tk()
    app = ReversiGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
