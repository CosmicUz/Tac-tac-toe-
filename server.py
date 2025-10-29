import socket
import threading
import time
import random
from game import Game

class Server:
    def __init__(self, win, shared_game=None):
        self.game = shared_game if shared_game else Game(win)
        self.server_socket = None
        self.conn = None
        self.sock = None
        self.is_host = False
        self.players = []
        self.my_ip = socket.gethostbyname(socket.gethostname())
        self.active = False
        self.disconnect_callback = None
        print(f"[SERVER] Lokal IP: {self.my_ip}")

    def start_server(self, move_callback, disconnect_callback):
        self.is_host = True
        self.active = True
        self.disconnect_callback = disconnect_callback
        print("[SERVER] Server ishga tushmoqda...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.my_ip, 5555))
        self.server_socket.listen()
        print(f"[SERVER] Tinglanmoqda: {self.my_ip}:5555")
        time.sleep(0.1)
        threading.Thread(
            target=self.accept_connection,
            args=(move_callback,),
            daemon=True
        ).start()

    def accept_connection(self, move_callback):
        if not self.active:
            return
        try:
            conn, addr = self.server_socket.accept()
            if not self.active:
                return
            print(f"[SERVER] Client ulandi: {addr}")
            self.conn = conn
            self.players = [f"Host (Siz): {self.my_ip}", f"Client: {addr[0]}"]

            def start_game_callback():

                state = "lan_game"

            threading.Thread(
                target=self.listen,
                args=(conn, move_callback, None),
                daemon=True
            ).start()
        except OSError:
            print("[SERVER] Accept to‘xtatildi (socket yopilgan).")

    def join_server(self, ip, move_callback, disconnect_callback):
        print(f"[CLIENT] {ip} ga ulanmoqda...")
        self.active = True
        self.is_host = False
        self.disconnect_callback = disconnect_callback
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(0.2)
        self.conn.connect((ip, 5555))
        self.players = [f"Host: {ip}", f"Client (Siz): {self.my_ip}"]
        print("[CLIENT] Serverga muvaffaqiyatli ulandi!")

    def send_move(self, index):
        if self.conn:
            try:
                msg = f"MOVE:{index}"
                self.conn.send(msg.encode())
                print(f"[NET] Yuborildi: {msg}")
            except Exception as e:
                print("[NET SEND ERROR]:", e)
                self.disconnect()

    def send_ready(self):
        if self.conn:
            try:
                self.conn.send("READY".encode())
                print("[NET] READY yuborildi.")
            except Exception as e:
                print("[READY SEND ERROR]", e)

    def send_chat(self, text):
        if self.conn:
            try:
                msg = f"CHAT:{text}"
                self.conn.send(msg.encode())
            except Exception as e:
                print("[CHAT SEND ERROR]", e)

    def send_restart_request(self):
        if self.conn:
            try:
                self.conn.send("RESTART_REQUEST".encode())
            except Exception as e:
                print("[RESTART SEND ERROR]", e)

    def send_start_game(self):
        if self.conn:
            try:
                self.game.reset()

                if random.choice([True, False]):
                    self.game.my_symbol = "X"
                    self.game.enemy_symbol = "O"
                else:
                    self.game.my_symbol = "O"
                    self.game.enemy_symbol = "X"

                self.game.in_lan_game = True
                self.game.can_move = (self.game.my_symbol == "X")

                self.conn.send("GAME_START".encode())
                time.sleep(0.1)
                self.conn.send(f"ROLE:{self.game.enemy_symbol}".encode())
                self.game.in_lan_game = True
                print(f"[SERVER] GAME_START yuborildi. Host: {self.game.my_symbol}, Client: {self.game.enemy_symbol}")

            except Exception as e:
                print("[GAME_START ERROR]", e)

    def listen(self, conn, move_callback, game_start_callback=None):
        while self.active:
            try:
                data = conn.recv(1024).decode()
                if not data:
                    break

                if data.startswith("MOVE:"):
                    _, idx = data.split(":")
                    self.game.grid[int(idx)] = self.game.enemy_symbol
                    print(f"[NET] {self.game.enemy_symbol} joy tanladi: {idx}")
                    self.game.winner = self.game.check_winner()
                    self.game.turn = self.game.my_symbol
                    self.game.can_move = True

                elif data.startswith("CHAT:"):
                    text = data[5:]
                    sender = "P2" if self.is_host else "P1"
                    print(f"[CHAT RECEIVE] {sender}: {text}")
                    self.game.add_message(sender, text)

                elif data.startswith("ROLE:"):
                    symbol = data.split(":")[1]
                    self.game.my_symbol = symbol
                    self.game.enemy_symbol = "O" if symbol == "X" else "X"
                    self.game.can_move = (symbol == "X")
                    print(f"[CLIENT] Belgim: {symbol}")

                elif data == "GAME_START":
                    print("[CLIENT] O‘yin boshlandi! LAN o‘yin rejimi ishga tushdi.")
                    self.game.reset()
                    self.game.assign_symbols()
                    self.game.in_lan_game = True
                    if game_start_callback:
                        game_start_callback()

                elif data == "RESTART_REQUEST":
                    sender = "P2" if self.is_host else "P1"
                    self.game.restart_requests.add(sender)
                    print(f"[RESTART] {sender} qayta boshlashni so‘radi.")

                elif data == "READY":
                    print("[NET] Qarshi tomon tayyor!")
                    self.game.ready = True

            except Exception as e:
                print("[NET ERROR]", e)
                break

        self.disconnect()


    def disconnect(self):

        print("[SERVER] Disconnect chaqirildi.")
        try:
            self.active = False

            time.sleep(0.3)

            if self.server_socket:
                try:
                    self.server_socket.close()
                    print("[SERVER] Server soketi yopildi.")
                except Exception as e:
                    print("[SERVER SOCKET CLOSE ERROR]", e)
                self.server_socket = None

            if self.conn:
                try:
                    self.conn.close()
                    print("[SERVER] Connection yopildi.")
                except Exception as e:
                    print("[CONNECTION CLOSE ERROR]", e)
                self.conn = None

            if self.sock:
                try:
                    self.sock.close()
                    print("[SERVER] Sock yopildi.")
                except Exception as e:
                    print("[SOCK CLOSE ERROR]", e)
                self.sock = None
            time.sleep(0.3)
            print("[SERVER] Aloqa to‘liq yopildi.")

        except Exception as e:
            print("[DISCONNECT ERROR]", e)
