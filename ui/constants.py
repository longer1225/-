# UI相关的常量定义
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
ZONE_WIDTH = 200
ZONE_HEIGHT = 90
ZONE_MARGIN = 20

# 分区独立高度（让手牌略小、孤立略大，总高度与原来接近）
HAND_HEIGHT = 80
BATTLE_HEIGHT = 90
ISO_HEIGHT = 100

# 颜色常量
COLOR_BG = (30, 30, 30)
COLOR_ZONE = (60, 60, 60)
COLOR_TEXT = (220, 220, 220)
COLOR_HIGHLIGHT = (100, 100, 200)
COLOR_CURRENT = (200, 200, 100)

# 游戏事件类型
END_TURN = "END_TURN"
PLAY_CARD = "PLAY_CARD"
SELECT_TARGET = "SELECT_TARGET"

# 为了类型提示
from typing import TYPE_CHECKING, Optional, Type
if TYPE_CHECKING:
    from game.game_manager import GameManager
    GameManagerType = Type[GameManager]
else:
    GameManagerType = object
