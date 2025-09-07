import pygame
import os
from game.game_manager import GameManager
from game.player import Player
from ui_manager import UIManager

CARD_WIDTH, CARD_HEIGHT = 100, 150
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
IMAGES_PATH = os.path.join(os.path.dirname(__file__), '..', 'images')

# 加载图片，图片名为'1.png', '2.png', '3.png', '4.png'，与卡牌编号对应
CARD_IMAGE_NAMES = ['1', '2', '3', '4']

def load_card_images():
    images = {}
    for name in CARD_IMAGE_NAMES:
        fname = f"{name}.png"
        path = os.path.join(IMAGES_PATH, fname)
        if os.path.exists(path):
            img = pygame.image.load(path)
            images[name] = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
    return images

def draw_hand(screen, hand, images, y, selected_idx=None):
    for idx, card in enumerate(hand):
        # 假设card有number属性，否则用name
        card_id = str(getattr(card, 'number', getattr(card, 'name', '1')))
        x = 100 + idx * (CARD_WIDTH + 20)
        img = images.get(card_id, None)
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        if img:
            screen.blit(img, rect)
        pygame.draw.rect(screen, (0,255,0) if idx==selected_idx else (0,0,0), rect, 3)
    return

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Carrot Card Game")
    clock = pygame.time.Clock()
    images = load_card_images()

    # 初始化游戏
    players = [Player("Alice"), Player("Bob")]
    game = GameManager(players)
    game.setup_board()
    ui = UIManager(players, game.board)

    running = True
    selected_card_idx = None

    while running:
        screen.fill((200, 200, 200))
        # 绘制玩家1手牌
        draw_hand(screen, players[0].hand, images, SCREEN_HEIGHT-200, selected_card_idx)
        # 可扩展：绘制玩家2手牌、战场牌等

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for idx, card in enumerate(players[0].hand):
                    x = 100 + idx * (CARD_WIDTH + 20)
                    rect = pygame.Rect(x, SCREEN_HEIGHT-200, CARD_WIDTH, CARD_HEIGHT)
                    if rect.collidepoint(mx, my):
                        selected_card_idx = idx
                        # 这里可以扩展：触发出牌、选目标等

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()