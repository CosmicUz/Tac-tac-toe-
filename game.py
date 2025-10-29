import pygame
from ui import draw_text

pygame.init()
WHITE, BLACK, BLUE, RED = (255, 255, 255), (0, 0, 0), (0, 0, 255), (255, 0, 0)
FONT = pygame.font.Font(None, 40)
SMALL = pygame.font.Font(None, 30)

class Game:
    def __init__(self, win):
        self.WIN = win
        self.grid = [""] * 9
        self.turn = "X"
        self.winner = None
        self.chat_message = []
        self.ready = False
        self.restart_requests = set()
        self.my_symbol = None
        self.can_move = False
        print("[GAME] Yangi o'yin yaratildi")

    def reset(self):
        self.grid = [""] * 9
        self.turn = "X"
        self.winner = None
        print("[GAME] O'yin qayta boshlandi")

    def bot_move(self):
        import random
        empty = [i for i in range(9) if self.grid[i] == ""]
        if empty:
            i = random.choice(empty)
            self.grid[i] = "O"
            print(f"[BOT] O joy tanladi: {i}")
            self.winner = self.check_winner()
            self.turn = "X"

    def draw_board(self):
        self.WIN.fill(WHITE)
        for i in range(1, 3):
            pygame.draw.line(self.WIN, BLACK, (0, i * 200), (600, i * 200), 3)
            pygame.draw.line(self.WIN, BLACK, (i * 200, 0), (i * 200, 600), 3)
        for i, mark in enumerate(self.grid):
            x, y = (i % 3) * 200 + 100, (i // 3) * 200 + 100
            draw_text(self.WIN, mark, x, y, FONT, color=BLUE if mark == "X" else RED)
        draw_text(self.WIN, f"Turn: {self.turn}", 700, 50, FONT)
        if self.winner:
            draw_text(self.WIN, f"Winner: {self.winner}", 700, 100, FONT)
        pygame.display.update()

    def handle_click(self, pos, send_move=None):
        if not self.can_move or self.winner:
            return

        mx, my = pos
        for i in range(9):
            x, y = (i % 3) * 200, (i // 3) * 200
            if x < mx < x + 200 and y < my < y + 200 and self.grid[i] == "":
                self.grid[i] = self.my_symbol
                print(f"[GAME] {self.my_symbol} joy tanladi: {i}")

                if send_move:
                    send_move(i)

                self.winner = self.check_winner()
                self.turn = self.enemy_symbol
                self.can_move = False
                return

    def check_winner(self):
        combos = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in combos:
            if self.grid[a] == self.grid[b] == self.grid[c] and self.grid[a] != "":
                print(f"[GAME] G'olib: {self.grid[a]}")
                return self.grid[a]
        if "" not in self.grid:
            print("[GAME] Durang!")
            return "Draw"
        return None

    def assign_symbols(self):
        import random
        if random.choice([True, False]):
            self.my_symbol = "X"
            self.enemy_symbol = "O"
        else:
            self.my_symbol = "O"
            self.enemy_symbol = "X"
        self.turn = "X"
        self.can_move = (self.my_symbol == self.turn)
        print(
            f"[SYMBOL] Siz: {self.my_symbol}, Raqib: {self.enemy_symbol}, Siz {'boshlaysiz' if self.can_move else 'kutasiz'}")

    def start_from_network(self):
        print("[GAME] LAN orqali o‘yin boshlandi.")
        self.reset()
        self.in_lan_game = True
        self.winner = None
        self.can_move = self.my_symbol == "X"

    def add_message(self, sender, text):
        msg = f"{sender}: {text}"
        self.chat_message.append(msg)
        if len(self.chat_message) > 10:
            self.chat_message.pop(0)
        print(f"[CHAT] {msg}")

    def draw_chat(self):
        x, y = 620, 190
        pygame.draw.rect(self.WIN, (240, 240, 240), (600, 100, 200, 400))
        for i, msg in enumerate(self.chat_message[-10:]):
            draw_text(self.WIN, msg, x + 80, y + i * 30, font=SMALL)
        draw_text(self.WIN, "Chat", 700, 160, font=SMALL, color=BLUE)
