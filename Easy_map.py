import logging

from Config import *
from Message import *
from Model import *
import random

logger = logging.getLogger(__name__)


def x(ez_cell):
    return ez_cell[0]


def y(ez_cell):
    return ez_cell[1]


class EasyMap():
    def __init__(self):
        self.game: Game = None
        self.last_health = None
        self.last_last_cell = None
        self.last_cell = None

        self.local_view = set()
        self.walls = set()
        self.traps = set()
        self.swamps = set()
        self.bread = dict()
        self.grass = dict()

        self.unknown_res = set()
        self.defence_cells = set()
        self.visited_cells = set()
        self.to_invalid_res = set()
        self.invalidated_res = set()
        self.seen_cells = set()

        self.enemy_base = None
        self.zero_around_enemy_base = set()
        self.first_around_enemy_base = set()
        self.second_around_enemy_base = set()

        self.around_enemy_sarbaz_count = 0
        self.around_friend_sarbaz_count = 0

    @staticmethod
    def get_distance(source_cell, dest_cell):
        return abs(x(source_cell) - x(dest_cell)) + abs(y(source_cell) - y(dest_cell))

    def update(self, game: Game):
        self.game = game
        self._update_from_messages()
        self._update_from_local_view()
        self.am_i_near_enemy_base()

    def _update_from_messages(self):
        self.unknown_res = set()
        self.invalidated_res = set()
        self.to_invalid_res = set()
        for chat in self.game.chatBox.allChats:
            message_str = chat.text
            messages = EasyMessage.unpack_message(message_str)

            self.defence_cells.update(
                messages.get(MessageType.MY_POS_on_RES, []))
            self.unknown_res.update(messages.get(MessageType.RESOURCE, []))
            if messages.get(MessageType.ENEMY_BASE_FOUND):
                self.enemy_base = messages.get(MessageType.ENEMY_BASE_FOUND)[0]

            self.zero_around_enemy_base.update(messages.get(
                MessageType.ZERO_ATTACK_BY_ENEMY_BASE, []))
            self.first_around_enemy_base.update(messages.get(
                MessageType.FIRST_ATTACK_BY_ENEMY_BASE, []))
            self.second_around_enemy_base.update(messages.get(
                MessageType.SECOND_ATTACK_BY_ENEMY_BASE, []))

            self.invalidated_res.update(messages.get(
                MessageType.INVALIDATE_RESOURCE, []))

            self.unknown_res = self.unknown_res.difference(
                self.invalidated_res)
            self.defence_cells = self.defence_cells.difference(
                self.invalidated_res)

    def _update_from_local_view(self):
        my_base = (self.game.baseX, self.game.baseY)

        self.local_view = set()
        self.to_invalid_res = set()
        self.around_enemy_sarbaz_count = 0
        self.around_friend_sarbaz_count = 0

        for i in range(-1 * self.game.viewDistance, self.game.viewDistance + 1):
            for j in range(-1 * self.game.viewDistance, self.game.viewDistance + 1):
                cell = self.game.ant.getNeightbourCell(i, j)
                if cell is None:
                    continue

                easy_cell = (cell.x, cell.y)
                self.local_view.add(easy_cell)
                self.seen_cells.add(easy_cell)

                for ant in cell.ants:
                    if ant.antType == AntType.SARBAAZ.value:
                        if ant.antTeam != self.game.ant.antTeam:
                            self.around_enemy_sarbaz_count += 1
                        elif easy_cell in self.zero_around_enemy_base:
                            self.around_friend_sarbaz_count += 1

                if cell.type == CellType.WALL.value:
                    self.walls.add(easy_cell)
                elif cell.type == CellType.TRAP.value:
                    self.traps.add(easy_cell)
                elif cell.type == CellType.SWAMP.value:
                    self.swamps.add(easy_cell)
                elif cell.type == CellType.BASE.value and easy_cell != my_base:
                    self.enemy_base = easy_cell
                elif cell.resource_value > 0:
                    if cell.resource_type == ResourceType.BREAD.value:
                        self.bread[easy_cell] = cell.resource_value
                    else:
                        self.grass[easy_cell] = cell.resource_value
                else:
                    if easy_cell in self.unknown_res:
                        self.to_invalid_res.add(easy_cell)
                    self.bread.pop(easy_cell, None)
                    self.grass.pop(easy_cell, None)
                    self.unknown_res.discard(easy_cell)
                    self.defence_cells.discard(easy_cell)

        # if self.enemy_base:
        #     zero_range = base_range + 1
        #     for dx in range(-1 * zero_range, zero_range + 1):
        #         dy = zero_range - abs(dx)
        #         zero_cell = self.get_easy_neighbor(self.enemy_base, dx, dy)
        #         self.zero_around_enemy_base.add(zero_cell)

    def am_i_near_enemy_base(self):
        my_pos = (self.game.ant.currentX, self.game.ant.currentY)

        if self.last_health is None:
            if self.game.ant.antType == AntType.KARGAR.value:
                self.last_health = self.game.healthKargar
            else:
                self.last_health = self.game.healthSarbaaz

        damage_given = self.last_health - self.game.ant.health
        logger.info(
            f"Last health: {self.last_health}, Now health: {self.game.ant.health}")
        if damage_given % 2 != 0:
            if self.last_cell not in self.first_around_enemy_base and self.last_cell not in self.second_around_enemy_base:
                if self.last_last_cell in self.first_around_enemy_base:
                    self.second_around_enemy_base.add(self.last_cell)
                elif self.last_last_cell in self.second_around_enemy_base:
                    self.first_around_enemy_base.add(self.last_cell)
                else:
                    self.zero_around_enemy_base.add(self.last_last_cell)
                    self.first_around_enemy_base.add(self.last_cell)
        else:
            if self.last_last_cell in self.first_around_enemy_base:
                self.zero_around_enemy_base.add(self.last_cell)

        self.last_health = self.game.ant.health

    def get_easy_neighbor(self, source_cell, dx, dy):
        cell_x = (x(source_cell) + dx) % self.game.mapWidth
        cell_y = (y(source_cell) + dy) % self.game.mapHeight
        return (cell_x, cell_y)

    def is_wall(self, cell):
        return cell in self.walls

    def is_trap(self, cell):
        return cell in self.traps

    def is_swamp(self, cell):
        return cell in self.swamps

    def get_shortest_path(self, source_cell, dest_cell, only_seen=False, dont_die=True, have_resource=False):
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
            if cell == dest_cell:
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
                    if only_seen and cell not in self.seen_cells:
                        continue
                    if dont_die and cell in self.first_around_enemy_base:
                        continue
                    if have_resource and self.is_trap(cell):
                        continue
                    next_moves = moves + [cdir]
                    if self.is_swamp(cell):
                        next_moves.extend([Direction.CENTER.value, Direction.CENTER.value, Direction.CENTER.value])
                    visited.append(cell)
                    index = len(moves_list)
                    for move in moves_list:
                        if len(next_moves) < len(move):
                            index = moves_list.index(move)
                            break
                    queue.insert(index, cell)
                    moves_list.insert(index, next_moves)

    def find_best_resource(self, source_cell):
        # TODO: maybe check outside of local too
        min_dist = map_size
        best_cell = None
        best_move = None
        my_base = (self.game.baseX, self.game.baseY)
        # TODO: decide res_type
        for res_cell, res_val in {**self.bread, **self.grass}.items():
            # TODO: check res_value too
            moves = self.get_shortest_path(source_cell, res_cell)
            back_moves = self.get_shortest_path(res_cell, my_base, have_resource=True)
            dist = len(moves)
            if dist > 0 and dist < min_dist and len(back_moves) > 0:
                logger.info("&&&&")
                logger.info(back_moves)
                logger.info("&&&&")
                min_dist = dist
                best_cell = res_cell
                best_move = moves[0]

        if best_cell is None:
            for res_cell in self.unknown_res:
                moves = self.get_shortest_path(source_cell, res_cell)
                back_moves = self.get_shortest_path(res_cell, my_base, have_resource=True)
                dist = len(moves)
                if dist > 0 and dist < min_dist and len(back_moves) > 0:
                    min_dist = dist
                    best_cell = res_cell
                    best_move = moves[0]
        return best_cell, best_move

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

    def get_all_unvisited_cells_with_dist(self, dist):
        unvisited_cells = []
        my_pos = (self.game.ant.currentX, self.game.ant.currentY)
        for x in range(-1 * dist, dist + 1):
            y = dist - abs(x)
            pos = self.get_easy_neighbor(my_pos, x, y)
            if pos not in self.seen_cells and not self.is_wall(pos):
                unvisited_cells.append(pos)
        return unvisited_cells

    def find_defend_pos(self, source_cell):
        min_dist = map_size
        best_cell = None
        best_move = None

        for def_cell in self.defence_cells:
            moves = self.get_shortest_path(source_cell, def_cell)
            dist = len(moves)
            if dist > 0 and dist < min_dist:
                min_dist = dist
                best_cell = def_cell
                best_move = moves[0]

        if best_cell is None:
            best_cell, best_move = self.find_best_resource(source_cell)
        return best_cell, best_move

    def find_attack_pos(self, source_cell):  # TODO: check enemies for attack
        min_dist = map_size
        best_cell = None
        best_move = None

        if source_cell in self.second_around_enemy_base or source_cell in self.first_around_enemy_base \
                or (self.enemy_base and self.get_distance(source_cell, self.enemy_base) <= self.game.ant.attackDistance) \
                or self.last_cell in self.first_around_enemy_base:
            return self.attack_base(source_cell)
        if source_cell in self.zero_around_enemy_base:
            if self.around_friend_sarbaz_count < 3:
                logger.info(f"wait in ZERO around base: {source_cell}")
                return source_cell, Direction.CENTER.value
            return self.attack_base(source_cell)
        else:
            logger.info(f"going to zero: {source_cell}")
            for att_cell in self.zero_around_enemy_base:
                moves = self.get_shortest_path(source_cell, att_cell)
                dist = len(moves)
                if dist > 0 and dist < min_dist:
                    min_dist = dist
                    best_cell = att_cell
                    best_move = moves[0]
            return best_cell, best_move
        return best_cell, best_move

    def attack_base(self, source_cell):
        if self.enemy_base:
            return self.enemy_base, self.get_shortest_path(source_cell, self.enemy_base, dont_die=False)[0]

        if source_cell in self.zero_around_enemy_base:
            for cell in self.first_around_enemy_base:
                if self.get_distance(source_cell, cell) == 1:
                    return cell, self.get_shortest_path(source_cell, cell, dont_die=False)[0]

        dir_to_cell = {
            Direction.UP.value: self.get_easy_neighbor(source_cell, 0, -1),
            Direction.DOWN.value: self.get_easy_neighbor(source_cell, 0, 1),
            Direction.RIGHT.value: self.get_easy_neighbor(source_cell, 1, 0),
            Direction.LEFT.value: self.get_easy_neighbor(source_cell, -1, 0),
        }

        good_cells = []
        for cdir, cell in dir_to_cell.items():
            if not self.is_wall(cell):
                if source_cell in self.second_around_enemy_base:
                    if cell not in self.first_around_enemy_base and cell not in self.visited_cells:
                        good_cells.append(cell)

                elif source_cell in self.first_around_enemy_base:
                    if cell not in self.zero_around_enemy_base:
                        good_cells.append(cell)

                else:
                    if cell not in self.visited_cells:
                        good_cells.append(cell)

        if good_cells:
            logger.info(f"good cells: {good_cells}")
            random_good_cell = random.choice(good_cells)
            return random_good_cell, self.get_shortest_path(source_cell, random_good_cell, dont_die=False)[0]
        return None, None
