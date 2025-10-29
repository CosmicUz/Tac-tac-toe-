import pygame, sys, threading
from game import Game
from server import Server
from ui import draw_text

pygame.init()
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TicTacToe LAN")
FONT = pygame.font.Font(None, 40)
SMALL = pygame.font.Font(None, 30)
WHITE, GRAY = (255, 255, 255), (200, 200, 200)

def main():
    clock = pygame.time.Clock()
    state = "menu"
    input_ip = ""
    game = Game(WIN)
    server = Server(WIN, shared_game=game)
    running = True
    pause_menu = False
    chat_input = ""
    chat_active = False

    def move_received(idx):
        symbol = "O" if server.is_host else "X"
        game.grid[idx] = symbol
        game.winner = game.check_winner()
        game.turn = "O" if game.turn == "X" else "X"
        game.can_move = True

    def on_disconnect():
        nonlocal state
        game.reset()
        state = "lobby"

    while running:
        WIN.fill(GRAY)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                if state == "menu":
                    if draw_text(WIN, "Play", 400, 200, FONT).collidepoint(mx, my):
                        game.reset()
                        state = "bot"
                    elif draw_text(WIN, "LAN", 400, 300, FONT).collidepoint(mx, my):
                        state = "lan"
                    elif draw_text(WIN, "Quit", 400, 400, FONT).collidepoint(mx, my):
                        running = False

                elif state == "lan":
                    if draw_text(WIN, "Create", 400, 200, FONT).collidepoint(mx, my):
                        threading.Thread(target=server.start_server, args=(move_received, on_disconnect),
                                         daemon=True).start()
                        state = "lobby"
                    elif draw_text(WIN, "Join", 400, 300, FONT).collidepoint(mx, my):
                        state = "join"
                    elif draw_text(WIN, "Back", 400, 400, FONT).collidepoint(mx, my):
                        state = "menu"


                elif state == "lobby":
                    create_rect = draw_text(WIN, "Create Game", 400, 500, FONT)
                    if server.is_host and create_rect.collidepoint(mx, my):
                        game.reset()
                        server.send_start_game()
                        state = "lan_game"
                elif state == "join":
                    def start_game_callback():
                        nonlocal state
                        state = "lan_game"

                    if draw_text(WIN, "Join", 400, 500, FONT).collidepoint(mx, my):
                        try:
                            server.join_server(input_ip, move_received, on_disconnect)
                            threading.Thread(
                                target=server.listen,
                                args=(server.conn, move_received, start_game_callback),
                                daemon=True
                            ).start()
                            state = "lobby"
                        except Exception as ex:
                            print("[JOIN ERROR]", ex)
                    elif draw_text(WIN, "Back", 100, 550, FONT).collidepoint(mx, my):
                        input_ip = ""
                        state = "lan"

                elif state == "bot":
                    if not game.winner and game.turn == "X":
                        game.handle_click((mx, my))
                        if not game.winner and game.turn == "O":
                            threading.Timer(0.5, game.bot_move).start()
                    if pause_menu:
                        if exit_rect.collidepoint(mx, my):
                            print("[PAUSE] Exit bosildi.")
                            if state == "lan_game":
                                server.disconnect()
                                state = "lobby"
                            game.reset()
                            pause_menu = False

                        elif restart_rect.collidepoint(mx, my):
                            print("[PAUSE] Restart bosildi.")
                            game.reset()
                            pause_menu = False

                        elif menu_rect.collidepoint(mx, my):
                            print("[PAUSE] Menu bosildi.")
                            if state == "lan_game":
                                server.disconnect()
                            game.reset()
                            state = "menu"
                            pause_menu = False

                    restart_rect = pygame.Rect(700, 530, 80, 35)
                    menu_rect = pygame.Rect(700, 570, 80, 35)

                    if restart_rect.collidepoint(mx, my):
                        print("[BOT] Restart bosildi")
                        game.reset()
                    elif menu_rect.collidepoint(mx, my):
                        print("[BOT] Menu bosildi")
                        game.reset()
                        state = "menu"


                elif state == "lan_game":
                    if not game.winner and game.can_move:
                        game.handle_click((mx, my), send_move=server.send_move)
                    if pause_menu:
                        if exit_rect.collidepoint(mx, my):
                            print("[PAUSE] Exit bosildi.")
                            if state == "lan_game":
                                server.disconnect()
                                state = "lobby"
                            game.reset()
                            pause_menu = False


                        elif restart_rect.collidepoint(mx, my):
                            sender = "P1" if server.is_host else "P2"
                            game.restart_requests.add(sender)
                            server.send_restart_request()
                            if len(game.restart_requests) == 2:
                                print("[RESTART] Ikkalasi ham bosdi, o'yin qayta boshlandi.")
                                game.reset()
                                game.restart_requests.clear()

                        elif menu_rect.collidepoint(mx, my):
                            print("[PAUSE] Menu bosildi.")
                            if state == "lan_game":
                                server.disconnect()
                            game.reset()
                            state = "menu"
                            pause_menu = False

                    exit_rect = pygame.Rect(700, 510, 80, 35)
                    restart_rect = pygame.Rect(700, 530, 80, 35)
                    menu_rect = pygame.Rect(700, 570, 80, 35)

                    if exit_rect.collidepoint(mx, my):
                        print("[LAN] Exit bosildi.")
                        server.disconnect()
                        game.reset()
                        state = "lobby"
                    elif restart_rect.collidepoint(mx, my):
                        sender = "P1" if server.is_host else "P2"
                        game.restart_requests.add(sender)
                        server.send_restart_request()
                        if len(game.restart_requests) == 2:
                            print("[RESTART] Ikkalasi ham bosdi, o'yin qayta boshlandi.")
                            game.reset()
                            game.restart_requests.clear()
                    elif menu_rect.collidepoint(mx, my):
                        print("[LAN] Menu bosildi.")
                        server.disconnect()
                        game.reset()
                        state = "menu"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE and state in ("bot", "lan_game"):
                    pause_menu = not pause_menu

            if e.type == pygame.KEYDOWN and state == "lan_game":
                if e.key == pygame.K_RETURN:
                    if chat_active and chat_input.strip():
                        sender = "P1" if server.is_host else "P2"
                        game.add_message(sender, chat_input)
                        server.send_chat(chat_input)
                        chat_input = ""
                    chat_active = not chat_active
                elif chat_active:
                    if e.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    else:
                        chat_input += e.unicode

            if e.type == pygame.KEYDOWN and state == "join":
                if e.key == pygame.K_BACKSPACE:
                    input_ip = input_ip[:-1]
                elif e.key == pygame.K_RETURN:
                    pass
                else:
                    input_ip += e.unicode

        if state == "menu":
            draw_text(WIN, "Play", 400, 200, FONT)
            draw_text(WIN, "LAN", 400, 300, FONT)
            draw_text(WIN, "Quit", 400, 400, FONT)

        elif state == "lan":
            draw_text(WIN, "Create", 400, 200, FONT)
            draw_text(WIN, "Join", 400, 300, FONT)
            draw_text(WIN, "Back", 400, 400, FONT)

        elif state == "lobby":
            draw_text(WIN, f"Sizning IP: {server.my_ip}", 400, 60, SMALL, color=(0, 100, 255))
            back_rect = draw_text(WIN, "Back", 100, 550, FONT)
            mx, my = pygame.mouse.get_pos()
            if back_rect.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
                print("[LOBBY] Back bosildi. LAN menyusiga qaytildi.")
                server.disconnect()
                state = "lan"
            if server.is_host:
                if not server.conn:
                    draw_text(WIN, "Client ulanadi deb kutyapmiz...", 400, 200, SMALL, color=(255, 255, 0))
                else:
                    draw_text(WIN, f"Client ulandi: {server.conn.getpeername()[0]}", 400, 200, SMALL, color=(0, 255, 0))
                    create_rect = draw_text(WIN, "Create Game", 400, 500, FONT)
                    if create_rect.collidepoint(mx, my) and pygame.mouse.get_pressed()[0]:
                        print("[HOST] O‘yin boshlanmoqda...")
                        server.send_start_game()
            else:
                draw_text(WIN, "Host o‘yinni boshlashini kutyapmiz...", 400, 300, SMALL, color=(255, 255, 0))

        elif state == "join":
            draw_text(WIN, "Enter IP:", 400, 200, FONT)
            pygame.draw.rect(WIN, WHITE, (250, 250, 300, 40))
            draw_text(WIN, input_ip, 400, 270, SMALL)
            draw_text(WIN, "Join", 400, 500, FONT)
            draw_text(WIN, "Back", 100, 550, FONT)

        elif state in ("bot", "lan_game"):
            game.draw_board()
            if state == "lan_game" and "P1" in game.restart_requests or "P2" in game.restart_requests:
                msg = "Restart bosildi, ikkinchi o'yinchini kutyapmiz..."
                draw_text(WIN, msg, 400, 450, SMALL, color=(255, 255, 0))

            if state == "lan_game":
                game.draw_chat()
                chat_y = 450
                if chat_active:
                    pygame.draw.rect(WIN, WHITE, (610, chat_y - 15, 180, 30))
                    draw_text(WIN, chat_input, 700, chat_y + 15, SMALL)
                else:
                    draw_text(WIN, "Enter chat", 700, chat_y + 15, SMALL, color=(150, 150, 150))
            if game.winner:
                restart_rect = pygame.Rect(360, 280, 80, 40)
                menu_rect = pygame.Rect(360, 330, 80, 40)

                if restart_rect.collidepoint(mx, my):
                    print("[WINNER] Restart bosildi.")
                    game.reset()
                    if state == "lan_game":
                        server.send_restart_request()
                    game.restart_requests.clear()

                elif menu_rect.collidepoint(mx, my):
                    print("[WINNER] Menu bosildi.")
                    if state == "lan_game":
                        server.disconnect()
                    game.reset()
                    state = "menu"

            if pause_menu:
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(180)
                overlay.fill((50, 50, 50))
                WIN.blit(overlay, (0, 0))
                draw_text(WIN, "Paused", 400, 200, FONT, color=(255, 255, 255))
                exit_rect = draw_text(WIN, "Exit", 400, 300, FONT)
                restart_rect = draw_text(WIN, "Restart", 400, 350, FONT)
                menu_rect = draw_text(WIN, "Menu", 400, 400, FONT)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
