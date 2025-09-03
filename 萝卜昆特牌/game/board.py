# game/board.py

class Board:
    def __init__(self, players):
        """
        初始化战场
        :param players: 玩家列表（Player 对象）
        """
        self.players = players

        # 每个玩家对应的牌区
        # 格式：{player_name: [Card, Card, ...]}
        self.board_zone = {player.name: [] for player in players}      # 战场牌
        self.isolated_zone = {player.name: [] for player in players}   # 孤立牌

    def add_to_board(self, player, card):
        """
        将非孤立牌放入战场区
        """
        self.board_zone[player.name].append(card)
        print(f"{player.name} 将 {card.name} 放入战场")

    def add_to_isolated(self, player, card):
        """
        将孤立牌放入孤立区
        """
        self.isolated_zone[player.name].append(card)
        print(f"{player.name} 将 {card.name} 放入孤立区")

    def get_player_board(self, player):
        """
        获取玩家的战场牌
        """
        return self.board_zone.get(player.name, [])

    def get_player_isolated(self, player):
        """
        获取玩家的孤立牌
        """
        return self.isolated_zone.get(player.name, [])

    def show_board(self):
        """
        打印所有玩家的战场和孤立区状态
        """
        for player in self.players:
            print(f"{player.name} 战场牌: {[card.name for card in self.board_zone[player.name]]}")
            print(f"{player.name} 孤立牌: {[card.name for card in self.isolated_zone[player.name]]}")
