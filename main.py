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
    
    # 如果音乐加载成功，则开始播放
    if ui.music_loaded:
        pygame.mixer.music.play(-1)  # -1表示循环播放

    # 游戏主循环
    while ui.running:
        # ---------------- 菜单逻辑 ----------------
        if ui.state == "menu":
            # 仅在菜单态处理事件与绘制
            ui.handle_events()
            ui.draw_game()
            ui.clock.tick(30)

        # ---------------- 游戏逻辑 ----------------
        elif ui.state == "game":
            # 游戏中降低音乐音量
            if ui.music_loaded:
                pygame.mixer.music.set_volume(0.7)
            
            # 将事件消费与界面刷新交给 GameManager/UI 的内部等待循环，避免重复消费事件
            if gm.current_round < gm.total_rounds:
                winners = gm.play_small_round(ui)
                if winners:
                    ui.add_log(f"小局胜者: {', '.join(p.name for p in winners)}")

                # 检查是否有大局胜利者（例如先至2胜）
                overall_winners = gm.show_winner()
                if any(gm.small_rounds_won[p.name] >= 2 for p in gm.players):
                    # 展示游戏结束界面
                    ui.show_game_over(overall_winners)
            else:
                # 到达预设小局数上限时，直接根据当前比分展示结束界面
                overall_winners = gm.show_winner()
                ui.show_game_over(overall_winners)
        
        # ---------------- 结束界面逻辑 ----------------
        elif ui.state == "game_over":
            # 结束界面恢复音乐音量
            if ui.music_loaded:
                pygame.mixer.music.set_volume(1.0)
                
            ui.handle_events()
            ui.draw_game()
            ui.clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()