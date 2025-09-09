import pygame
from game.player import Player
from game.game_manager import GameManager
from ui.PygameUI import PygameUI

def main():
    pygame.init()

    # 创建 UI 和游戏管理器
    ui = PygameUI()
    gm = GameManager(players=[])
    
    clock = pygame.time.Clock()
    FPS = 30

    while ui.running:
        # ---------------- 事件处理 ----------------
        ui.handle_events()

        # ---------------- 菜单逻辑 ----------------
        if ui.state == "menu":
            # 玩家人数选择并开始游戏
            if ui.selected_num:
                gm.players = [Player(f"玩家{i+1}", i) for i in range(ui.selected_num)]
                gm.setup_board()
                ui.players_done = [False] * len(gm.players)
                ui.state = "game"

        # ---------------- 游戏逻辑 ----------------
        elif ui.state == "game":
            ui.players = gm.players
            ui.current_player_index = gm.current_player_index

            # 如果所有玩家还没走完当前小局，运行小局
            if not all(getattr(p, 'prev_round_won', False) for p in gm.players):
                winners = gm.play_small_round(ui)
                # 小局结束显示胜者
                ui.round_winner = ", ".join([p.name for p in winners])

        # ---------------- 绘制 ----------------
        if ui.state == "menu":
            ui.draw_menu()
        elif ui.state == "game":
            ui.draw_game()

        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
