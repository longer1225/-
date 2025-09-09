

import pygame
import sys
from game.game_manager import GameManager
from ui.PygameUI import PygameUI


def main():
    pygame.init()

    # 创建 UI 和游戏管理器
    ui = PygameUI()
    gm = GameManager(players=[])
    ui.set_manager(gm)

    clock = pygame.time.Clock()
    FPS = 30

    # 游戏主循环
    running = True
    while running:
        ui.handle_events()

        # ---------------- 菜单逻辑 ----------------
        if ui.state == "menu":
            ui.draw()

        # ---------------- 游戏逻辑 ----------------
        elif ui.state == "game":
            # 确保玩家同步
            ui.players = gm.players
            ui.current_player_index = gm.current_player_index

            ui.draw()

            # 在这里让 GameManager 驱动小局逻辑
            if gm.current_round < gm.total_rounds:
                winners = gm.play_small_round(ui)
                print("小局胜者:", [p.name for p in winners])

                # 检查是否有大局胜利者
                overall_winners = gm.show_winner()
                if any(gm.small_rounds_won[p.name] >= 2 for p in gm.players):
                    print("大局胜者:", overall_winners)
                    running = False

        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
