# game/board.py

class Board:
    def __init__(self, players):
        """
        初始化战场
        :param players: 玩家列表（Player 对象）
        """
        self.players = players  # 保存玩家对象列表

    # ------------------ 查询方法 ------------------
    def get_player_by_name(self, name):
        """
        根据玩家名字获取玩家对象
        """
        for player in self.players:
            if player.name == name:
                return player
        return None

    def get_player_zone(self, player, zone_type):
        """
        获取玩家指定牌区
        :param player: Player 对象
        :param zone_type: "hand" / "battlefield" / "isolated"
        :return: 对应牌区列表
        """
        if zone_type == "hand":
            return player.hand
        elif zone_type == "battlefield":
            return player.battlefield_cards
        elif zone_type == "isolated":
            return player.isolated_cards
        else:
            raise ValueError(f"未知牌区类型: {zone_type}")

    def all_cards_on_board(self):
        """
        获取所有玩家的战场牌和孤立牌
        :return: 卡牌列表
        """
        cards = []
        for player in self.players:
            cards.extend(player.battlefield_cards + player.isolated_cards)
        return cards

    def show_board(self):
        """
        打印所有玩家的手牌、战场牌和孤立牌状态，用于调试
        """
        for player in self.players:
            print(f"玩家 {player.name} 手牌: {[c.name for c in player.hand]}")
            print(f"玩家 {player.name} 战场牌: {[c.name for c in player.battlefield_cards]}")
            print(f"玩家 {player.name} 孤立牌: {[c.name for c in player.isolated_cards]}")

