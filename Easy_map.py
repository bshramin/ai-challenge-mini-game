import logging
import random

from Message import EasyMessage, MessageType
from Model import Game, AntType, CellType, ResourceType, Direction

logger = logging.getLogger(__name__)


def x(ez_cell):
    return ez_cell[0]


def y(ez_cell):
    return ez_cell[1]


class EasyMap:
    duty_poses = [
        (1, 1), (-1, -1), (1, -1), (-1, 1),
        (-2, 0), (2, 0), (0, 2), (0, -2)
    ]

    def __init__(self):
        self.game: Game = Game()
        self.last_health = None
        self.last_cell = None
        self.duty_pos = None
        self.our_queens_next_pos = None
        self.last_enemy_queen_pos_in_messages = None
        self.new_enemy_queen_pos = None
        self.walls = set()
        self.visited_cells = set()
        self.seen_cells = set()
        self.our_queen_pos = None
        self.filled_duty_poses = set()
        self.enemy_scorpion_in_local_view = set()

    @staticmethod
    def get_distance(source_cell, destination_cell):
        return abs(x(source_cell) - x(destination_cell)) + abs(y(source_cell) - y(destination_cell))

    def update(self, game: Game):
        self.game = game
        self._update_from_messages()
        self._update_from_local_view()

    def _update_from_messages(self):
        self.queen_moves_messages = []
        self.seen_swamps_messages = set()
        self.scorpion_in_position_messages = set()
        self.scorpion_got_attacked_messages = set()
        self.scorpion_died_in_position_messages = set()
        self.enemy_queen_found_messages = set()

        for chat in self.game.chatBox.allChats:
            message_str = chat.text
            messages = EasyMessage.unpack_message(message_str)

            self.queen_moves_messages.append(messages.get(MessageType.OUR_QUEEN_MOVING_TO, []))
            self.seen_swamps_messages.update(messages.get(MessageType.SEEN_SWAMPS, []))
            self.scorpion_in_position_messages.update(messages.get(MessageType.SCORPION_IN_POSITION, []))
            self.scorpion_got_attacked_messages.update(messages.get(MessageType.SCORPION_GOT_ATTACKED, []))
            self.scorpion_died_in_position_messages.update(messages.get(MessageType.SCORPION_DIED_IN_POSITION, []))
            self.enemy_queen_found_messages.update(messages.get(MessageType.ENEMY_QUEEN_FOUND, []))

        self.extract_info_from_messages()

    def extract_info_from_messages(self):
        for msg in self.queen_moves_messages:
            if msg:
                self.our_queen_pos = [msg[0][0], msg[0][1]]

    def _update_from_local_view(self):
        self.new_enemy_queen_pos = set()
        self.enemy_scorpion_in_local_view = set()
        for i in range(-1 * self.game.viewDistance, self.game.viewDistance + 1):
            for j in range(-1 * self.game.viewDistance, self.game.viewDistance + 1):
                cell = self.game.ant.getNeightbourCell(i, j)
                if cell is None:
                    continue

                easy_cell = (cell.x, cell.y)
                self.seen_cells.add(easy_cell)

                if cell.type == CellType.WALL.value:
                    self.walls.add(easy_cell)

                for ant in cell.ants:
                    if ant.antTeam != self.game.ant.antTeam:
                        if ant.antType == AntType.QUEEN:
                            if not self.last_enemy_queen_pos_in_messages or (cell.x != self.last_enemy_queen_pos_in_messages[0] or cell.y != self.last_enemy_queen_pos_in_messages[1]):
                                self.new_enemy_queen_pos = easy_cell
                        if ant.antType == AntType.SCORPION:
                            self.enemy_scorpion_in_local_view.add(easy_cell)

    def is_wall(self, cell):
        return cell in self.walls

    def get_easy_neighbor(self, source_cell, dx, dy):
        cell_x = (x(source_cell) + dx) % self.game.mapWidth
        cell_y = (y(source_cell) + dy) % self.game.mapHeight
        return cell_x, cell_y

    def get_all_unvisited_cells_with_dist(self, dist):
        unvisited_cells = []
        my_pos = (self.game.ant.currentX, self.game.ant.currentY)
        for x in range(-1 * dist, dist + 1):
            y = dist - abs(x)
            pos = self.get_easy_neighbor(my_pos, x, y)
            if pos not in self.visited_cells and not self.is_wall(pos):
                unvisited_cells.append(pos)
        return unvisited_cells

    def get_shortest_path(self, source_cell, destination_cell):
        queue = [source_cell]
        visited = []
        moves_list = [[]]

        visited.append(source_cell)
        while True:
            if len(queue) == 0:
                return []

            cell = queue[0]
            moves = moves_list[0]
            del queue[0]
            del moves_list[0]
            if cell == destination_cell:
                if len(moves) > 0:
                    return moves
                else:
                    return [Direction.CENTER.value]

            dir_to_cell = {
                Direction.UP.value: self.get_easy_neighbor(cell, 0, -1),
                Direction.DOWN.value: self.get_easy_neighbor(cell, 0, 1),
                Direction.RIGHT.value: self.get_easy_neighbor(cell, 1, 0),
                Direction.LEFT.value: self.get_easy_neighbor(cell, -1, 0),
            }

            for cdir, cell in dir_to_cell.items():
                if cell not in visited and not self.is_wall(cell):
                    next_moves = moves + [cdir]
                    visited.append(cell)
                    index = len(moves_list)
                    for move in moves_list:
                        if len(next_moves) < len(move):
                            index = moves_list.index(move)
                            break
                    queue.insert(index, cell)
                    moves_list.insert(index, next_moves)

    def random_walk(self, source_cell):
        best_cell = None
        best_moves = 99999
        best_move = None
        min_dist = 0
        while True:
            unvisited_min_dist = self.get_all_unvisited_cells_with_dist(
                min_dist)
            unvisited_min_dist += self.get_all_unvisited_cells_with_dist(
                min_dist + 1)
            if unvisited_min_dist:
                while unvisited_min_dist:
                    random_cell = random.choice(unvisited_min_dist)
                    unvisited_min_dist.remove(random_cell)
                    moves = self.get_shortest_path(source_cell, random_cell)
                    if 0 < len(moves) < best_moves:
                        best_moves = len(moves)
                        best_move = moves[0]
                        best_cell = random_cell
                if best_move:
                    return best_cell, best_move
            min_dist += 1

    def find_scorpion_duty_pos(self):
        if self.duty_pos:
            return self.duty_pos
        available_duty_cells = []
        for pos in EasyMap.duty_poses:
            if pos not in self.filled_duty_poses:
                available_duty_cells.append(pos)

        return available_duty_cells[0]

    def get_queen_next_pos(self, source_cell):
        if not self.enemy_scorpion_in_local_view:
            cell, move = self.random_walk(source_cell)
            self.our_queens_next_pos = cell
            return self.random_walk(source_cell)
        else:
            mean_x = 0
            mean_y = 0
            for enemy_scorpion in self.enemy_scorpion_in_local_view:
                mean_x += enemy_scorpion[0] - source_cell[0]
                mean_y += enemy_scorpion[1] - source_cell[1]

            if abs(mean_x) > abs(mean_y):
                x_diff = 1 if mean_x < 0 else -1 if mean_x > 0 else 0
                y_diff = 0
                move = Direction.DOWN.value if mean_y < 0 else Direction.UP.value if mean_y > 0 else Direction.CENTER.value
            else:
                y_diff = 1 if mean_y < 0 else -1 if mean_y > 0 else 0
                x_diff = 0
                move = Direction.DOWN.value if mean_y < 0 else Direction.UP.value if mean_y > 0 else Direction.CENTER.value

            next_cell = (source_cell[0]+x_diff, source_cell[1]+y_diff)
            self.our_queens_next_pos = next_cell
            return next_cell, move

    def get_scorpion_next_pos(self, source_cell):
        if not self.duty_pos:
            self.duty_pos = self.find_scorpion_duty_pos()

        # if not self.our_queen_pos:
        return source_cell, Direction.CENTER.value

        # to_be_in_cell = (
        #     self.duty_pos[0] + self.our_queen_pos[0],
        #     self.duty_pos[1] + self.our_queen_pos[1],
        # )

        # if to_be_in_cell in self.walls:
        # return (self.our_queen_pos[0], self.our_queen_pos[1]), self.get_shortest_path(source_cell, (self.our_queen_pos[0], self.our_queen_pos[1]))

        # return to_be_in_cell, self.get_shortest_path(source_cell, to_be_in_cell)

    def attack_enemy_queen(self, source_cell):
        return self.last_enemy_queen_pos_in_messages, self.get_shortest_path(source_cell, self.last_enemy_queen_pos_in_messages)[0]
