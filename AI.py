import logging
import os
import random
import time

from Easy_map import EasyMap
from Message import MessageType, EasyMessage
from Model import Game, AntType, AntTeam, Direction

if not os.path.exists('ezlog'):
    os.makedirs('ezlog')

time_seed = int(time.time())
random.seed(time_seed)

logging.basicConfig(filename=f'ezlog/ant{time_seed}.log',
                    filemode='w',
                    format='%(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


class AI:
    turn_num = 0
    easy_map = EasyMap()

    def __init__(self):
        # Current Game State
        self.game = Game()
        AI.turn_num += 1

        # Answer
        self.message: str = ""
        self.direction: int = Direction.CENTER.value
        self.value: int = 0

    def print_all_map(self):
        for j in range(self.game.mapHeight):
            line = ""
            for i in range(self.game.mapWidth):
                if self.game.ant.visibleMap.cells[i] is None:
                    return
                cell = self.game.ant.visibleMap.cells[i][j]
                if cell:
                    line = line + f"({cell.x},{cell.y})"
                else:
                    line = line + "(   )"
            logger.info(line)

    def am_i_allowed_to_tell(self, cell):
        me = self.game.ant
        for ant in cell.ants:
            if ant.antType == AntType.SARBAAZ.value and ant.antTeam == AntTeam.ALLIED.value:
                if me.antType == AntType.KARGAR:
                    return False
                elif random.random() < 0.4:
                    return False
        return True

    def send_message(self):
        all_messages = []

        if AI.easy_map.new_enemy_queen_pos:
            message = (MessageType.ENEMY_QUEEN_FOUND, AI.easy_map.new_enemy_queen_pos, 0)
            all_messages.append(message)

        if self.game.ant.antType == AntType.QUEEN.value:
            message = (MessageType.OUR_QUEEN_MOVING_TO, AI.easy_map.our_queens_next_pos, 0)
            all_messages.append(message)

        if len(all_messages) == 0:
            return None, 0
        return EasyMessage.pack_messages(all_messages)

    def queen_decide(self, me):
        my_pos = (me.currentX, me.currentY)
        AI.easy_map.visited_cells.add(my_pos)

        queen_next_pos, move = AI.easy_map.get_queen_next_pos(my_pos)
        logger.info(f"queen next pos: {queen_next_pos}")
        self.direction = move

        if self.direction is None:
            rand_pos, move = AI.easy_map.random_walk(my_pos)
            logger.info(f"queen random destination {rand_pos}")
            self.direction = move

        message, value = self.send_message()
        if value != 0:
            self.message = message
            self.value = value

    def scorpion_decide(self, me):
        my_pos = (me.currentX, me.currentY)
        AI.easy_map.visited_cells.add(my_pos)

        scorpion_next_pos, move = AI.easy_map.get_scorpion_next_pos(my_pos)
        logger.info(f"scorpion next pos: {scorpion_next_pos}")
        self.direction = move

        if self.direction is None:
            rand_pos, move = AI.easy_map.random_walk(my_pos)
            logger.info(f"scorpion random destination {rand_pos}")
            self.direction = move

        message, value = self.send_message()
        if value != 0:
            self.message = message
            self.value = value

    def log_stuff(self):
        self.print_all_map()
        me = self.game.ant
        logger.info(f"Turn: {AI.turn_num}")
        logger.info(f"duty_pos: {AI.easy_map.duty_pos}")
        logger.info(f"my pos: {(me.currentX, me.currentY)}")
        logger.info(f"walls: {AI.easy_map.walls}")
        logger.info(f"enemy base: {AI.easy_map.last_enemy_queen_pos_in_messages}")
        logger.info(f"Last pos: {AI.easy_map.last_cell}")
        logger.info(f"our_queen_pos: {AI.easy_map.our_queen_pos}")
        logger.info(f"our_queens_next_pos: {AI.easy_map.our_queens_next_pos}")
        logger.info(f"filled_duty_poses: {AI.easy_map.filled_duty_poses}")
        logger.info(f"enemy_scorpion_in_local_view: {AI.easy_map.enemy_scorpion_in_local_view}")
        logger.info(f"new_enemy_queen_pos: {AI.easy_map.new_enemy_queen_pos}")
        logger.info(f"enemy_scorpion_in_local_view: {AI.easy_map.enemy_scorpion_in_local_view}")

    def turn(self) -> (str, int, int):
        AI.easy_map.update(self.game)
        me = self.game.ant
        ant_type = me.antType

        self.log_stuff()

        if ant_type == AntType.QUEEN.value:
            self.queen_decide(me)
        else:
            self.scorpion_decide(me)

        AI.easy_map.last_last_cell = AI.easy_map.last_cell
        AI.easy_map.last_cell = (me.currentX, me.currentY)
        logger.info(
            f"decide: {self.direction} - message: {self.message} - value: {self.value}")
        logger.info("")
    
        return self.message, self.value, self.direction
