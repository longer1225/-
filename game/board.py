# game/board.py

class Board:
    def __init__(self, players):
        """
        初始化战场
        :param players: 玩家列表（Player 对象）
        """
        self.players = players  # 只保存玩家对象列表

    def show_board(self):
        """
        打印所有玩家的手牌、战场牌和孤立牌状态
        """
        for player in self.players:
            # 由 Player 自己管理牌区
            player.show_hand()
            player.show_board()
            player.show_isolated()

    def get_player_by_name(self, name):
        """
        根据玩家名字获取玩家对象
        """
        for player in self.players:
            if player.name == name:
                return player
        return None
