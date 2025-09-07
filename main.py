from game.player import Player
from game.game_manager import GameManager
from ui.PygameUI import PygameUI
import sys
sys.stdout.reconfigure(encoding='utf-8')


    # ------------------ 启动 ------------------
if __name__ == "__main__":
    gm = GameManager([])  # 初始空玩家
    ui = PygameUI(gm)
    ui.run()
