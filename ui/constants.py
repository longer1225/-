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
# 卡面文字使用更高对比度的颜色（更接近纯白，保证可读性）
COLOR_CARD_TEXT = (0, 0, 0) #白色
COLOR_HIGHLIGHT = (100, 100, 200)
COLOR_CURRENT = (200, 200, 100)
COLOR_BTN_TEXT = (0, 0, 0)  # 按钮文字颜色：黑色

# 分区可视化增强（半透明色块与边框颜色）
# 使用 RGBA（最后一位为 alpha，仅在采用带透明度的 Surface 时生效）
COLOR_HAND_TINT = (70, 120, 200, 70)       # 手牌：淡蓝
COLOR_BATTLE_TINT = (90, 160, 90, 70)      # 战场：淡绿
COLOR_ISO_TINT = (170, 120, 60, 70)        # 孤立：琥珀
COLOR_HAND_TINT_HDR = (70, 120, 200, 110)
COLOR_BATTLE_TINT_HDR = (90, 160, 90, 110)
COLOR_ISO_TINT_HDR = (170, 120, 60, 110)
COLOR_HAND_BORDER = (110, 170, 230)
COLOR_BATTLE_BORDER = (120, 200, 120)
COLOR_ISO_BORDER = (220, 170, 100)

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
