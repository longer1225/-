
# ui/ui_main.py
"""
文本交互式 UI 主入口，结合 UIManager、PlayAction 和 GameManager。
"""
from ui.ui_manager import UIManager
from ui.play_action import PlayAction
from game.game_manager import GameManager
from game.player import Player

# 假设 Card、create_card_by_number 已在 card_factory、player 等实现

def main():
    # 初始化玩家和游戏
    players = [Player("Alice"), Player("Bob")]
    game = GameManager(players)
    game.setup_board()
    ui = UIManager(players, game.board)

    # 游戏主循环
    while not game_over(game):
        for player in players:
            print(f"\n{player.name} 的回合：")
            action = player_turn_ui(ui, player)
            if action:
                # 这里可以扩展：比如 action 传给 game 统一处理
                action.card.play(owner=player, board=game.board, targets=action.targets)
        # 结算、下一轮等
        game.play_small_round()


def player_turn_ui(ui, player):
    card = ui.select_card_from_hand(player)
    if not card:
        print("没有可用手牌")
        return None
    if not ui.confirm_action(player, f"是否打出 {card.name}"):
        return None
    action = PlayAction(player, card,game.board,game)
    # 技能目标收集
    for skill in getattr(card, "skills", []):
        if getattr(skill, "needs_target", False):
            target = ui.select_target_card(player, skill)
            if target:
                action.add_target(target)
        elif getattr(skill, "needs_targets", False):
            targets = ui.select_target_cards(player, skill)
            for t in targets:
                action.add_target(t)
    return action


def game_over(game):
    # 可根据 game.small_rounds_won 或其他条件判断
    return max(game.small_rounds_won.values()) >= (game.total_rounds // 2 + 1)


if __name__ == "__main__":
    main()
