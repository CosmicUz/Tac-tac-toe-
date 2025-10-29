import pygame

def draw_text(win, text, x, y, font, color=(0, 0, 0)):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y))
    win.blit(surf, rect)
    return rect
