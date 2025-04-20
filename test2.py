#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import random

CELL_SIZE = 60
BOARD_SIZE = 8
BACKGROUND_COLOR = "#006400"


class ReversiGame:
    def __init__(self):
        self.board = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = "X"
        self.extensions = {"X": 3, "O": 3}
        self.init_board()

    @staticmethod
    def opponent(player: str) -> str:
        return "O" if player == "X" else "X"

    @staticmethod
    def inside(r: int, c: int) -> bool:
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def init_board(self):
        self.board[3][3] = self.board[4][4] = "X"
        self.board[3][4] = self.board[4][3] = "O"

    def get_flips(self, player: str, r: int, c: int):
        opp = self.opponent(player)
        flips_total = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
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
        return [(r, c) for r in range(BOARD_SIZE)
                for c in range(BOARD_SIZE)
                if self.board[r][c] == "." and self.get_flips(player, r, c)]

    def make_move(self, player: str, r: int, c: int):
        flips = self.get_flips(player, r, c)
        if not flips:
            return None, None
        self.board[r][c] = player
        for fx, fy in flips:
            self.board[fx][fy] = player
        return flips, None

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
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Reversi with Return Rule")
        self.game = ReversiGame()

        self.canvas = tk.Canvas(root, width=CELL_SIZE * BOARD_SIZE,
                                height=CELL_SIZE * BOARD_SIZE,
                                bg=BACKGROUND_COLOR)
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

        self.extension_button = tk.Button(root, text="使用延長(+60s)", command=self.use_extension)
        self.extension_button.grid(row=15, column=1, sticky="we")

        self.timer_id = None
        self.time_left = 60

        self.pending_return = None
        self.return_origin = None

        self.draw_board()
        self.start_turn()

    def draw_board(self):
        size = CELL_SIZE
        for i in range(BOARD_SIZE + 1):
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

        # 顯示可返還棋子（紅框）
        if hasattr(self, "pending_return") and self.pending_return:
            for r, c in self.pending_return:
                x1 = c * size + margin
                y1 = r * size + margin
                x2 = (c + 1) * size - margin
                y2 = (r + 1) * size - margin
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, outline="red", width=3, tags="piece"
                )

    def highlight_moves(self):
        self.canvas.delete("star")
        moves = self.game.get_valid_moves(self.game.current_player)
        size = CELL_SIZE
        for r, c in moves:
            x = c * size + size // 2
            y = r * size + size // 2
            self.canvas.create_text(x, y, text="*", fill="yellow",
                                    font=("Helvetica", 16, "bold"), tags="star")

    def handle_click(self, event):
        if self.pending_return:
            return  # 等待返還中，忽略一般點擊

        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        if (row, col) not in self.game.get_valid_moves(self.game.current_player):
            return

        self.stop_timer()
        flips, _ = self.game.make_move(self.game.current_player, row, col)

        if len(flips) >= 3:
            self.pending_return = flips
            self.return_origin = (row, col)
            self.update_board()
            self.canvas.bind("<Button-1>", self.handle_return_click)
        else:
            self.log_move(f"{self.game.current_player}({row},{col})")
            if self.game.game_over():
                self.finish_game()
            else:
                self.switch_player()

    def handle_return_click(self, event):
        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if (row, col) not in self.pending_return:
            return
        self.game.board[row][col] = self.game.opponent(self.game.current_player)

        ox, oy = self.return_origin
        move_txt = f"{self.game.current_player}({ox},{oy})返還({row},{col})"
        self.log_move(move_txt)

        self.pending_return = None
        self.return_origin = None
        self.canvas.bind("<Button-1>", self.handle_click)

        if self.game.game_over():
            self.finish_game()
        else:
            self.switch_player()

    def switch_player(self):
        self.game.current_player = self.game.opponent(self.game.current_player)
        if self.game.get_valid_moves(self.game.current_player):
            self.start_turn()
        else:
            self.log_move("PASS")
            self.game.current_player = self.game.opponent(self.game.current_player)
            if not self.game.get_valid_moves(self.game.current_player):
                self.finish_game()
            else:
                self.start_turn()

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
            self.game.extensions[player] -= 1
            self.time_left = 60
            self.update_status()
            self.tick()
        else:
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
        print(txt)

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


def main():
    root = tk.Tk()
    app = ReversiGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
