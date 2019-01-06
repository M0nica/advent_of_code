import heapq
import re
from typing import NamedTuple, List, Union, Tuple, Iterable


class Point3D(NamedTuple):
    x: int
    y: int
    z: int

    def __add__(self, other: Union['Point3D', Tuple[int, int, int]]) -> 'Point3D':
        x1, y1, z1 = self
        x2, y2, z2 = other
        return Point3D(x1+x2, y1+y2, z1+z2)

    def manhattan_distance_to(self, other: Union['Point3D', Tuple[int, int, int]]) -> int:
        x1, y1, z1 = self
        x2, y2, z2 = other
        return abs(x2-x1) + abs(y2-y1) + abs(z2-z1)


class Sphere(NamedTuple):
    center: Point3D
    radius: int


class Cube(NamedTuple):
    corner: Point3D
    width: int

    @property
    def corners(self):
        width = self.width - 1
        deltas = [
            (    0,     0,     0),
            (width,     0,     0),
            (    0, width,     0),
            (    0,     0, width),
            (width, width,     0),
            (width,     0, width),
            (    0, width, width),
            (width, width, width),
        ]
        for delta in deltas:
            yield self.corner + delta


class Extremes(NamedTuple):
    minx: int
    maxx: int
    miny: int
    maxy: int
    minz: int
    maxz: int

    @staticmethod
    def create_from(points: Iterable[Point3D]) -> 'Extremes':
        xs, ys, zs = zip(*points)
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        minz, maxz = min(zs), max(zs)
        return Extremes(minx, maxx, miny, maxy, minz, maxz)


class SearchSpace:
    def __init__(self, corner: Point3D, width: int, bots: List[Sphere]) -> None:
        self.cube = Cube(corner, width)
        self.all_bots = bots
        self._bot_count = None
        self.distance_from_origin = corner.manhattan_distance_to((0,0,0))

    def __repr__(self) -> str:
        return str(self.cube)

    def __lt__(self, other: 'SearchSpace') -> bool:
        return self.distance_from_origin < other.distance_from_origin

    def __le__(self, other: 'SearchSpace') -> bool:
        return self.distance_from_origin <= other.distance_from_origin

    def __eq__(self, other: 'SearchSpace') -> bool:
        return self.distance_from_origin == other.distance_from_origin

    @property
    def bot_count(self) -> int:
        if self._bot_count is None:
            minx, maxx, miny, maxy, minz, maxz = Extremes.create_from(self.cube.corners)
            count = 0
            for bot_center, bot_radius in self.all_bots:
                bx, by, bz = bot_center
                dx = 0 if minx <= bx and bx <= maxx else min(abs(minx-bx), abs(maxx-bx))
                dy = 0 if miny <= by and by <= maxy else min(abs(miny-by), abs(maxy-by))
                dz = 0 if minz <= bz and bz <= maxz else min(abs(minz-bz), abs(maxz-bz))
                if (dx + dy + dz) <= bot_radius:
                    count += 1
            self._bot_count = count

        return self._bot_count

    def is_better_than(self, other: 'SearchSpace') -> bool:
        if self.bot_count < other.bot_count:
            return False

        elif self.bot_count > other.bot_count:
            return True

        return self < other

    def split(self) -> List['SearchSpace']:
        start, width = self.cube
        next_width = width // 2
        deltas_to_next_corners_shallow = [
            (0, 0, 0),
            (next_width, 0, 0),
            (0, next_width, 0),
            (next_width, next_width, 0),
        ]
        deltas_to_next_corners_deep = [
            (0, 0, next_width),
            (next_width, 0, next_width),
            (0, next_width, next_width),
            (next_width, next_width, next_width),
        ]
        shallow_search_spaces = [SearchSpace(start+delta, next_width, self.all_bots)
                                 for delta in deltas_to_next_corners_shallow]
        deep_search_spaces = [SearchSpace(start+delta, next_width + (width%2), self.all_bots)
                              for delta in deltas_to_next_corners_deep]
        return shallow_search_spaces + deep_search_spaces


def get_bots():
    def read_file(filepath):
        with open(filepath) as f:
            for line in f.readlines():
                yield line.rstrip()
        # Test Data
        # for line in [
        #     "pos=<10,12,12>, r=2",
        #     "pos=<12,14,12>, r=2",
        #     "pos=<16,12,12>, r=4",
        #     "pos=<14,14,14>, r=6",
        #     "pos=<50,50,50>, r=200",
        #     "pos=<10,10,10>, r=5",
        # ]:
        #     yield line

    bots = []
    pattern = re.compile(r'^pos=<([-\d]+),([-\d]+),([-\d]+)>, r=(\d+)$')
    for line in read_file('input.txt'):
        x, y, z, r = map(int, pattern.match(line).groups())
        bots.append(Sphere(center=Point3D(x, y, z), radius=r))
    return bots


def solution():
    bots = get_bots()
    bot_with_largest_r = max(bots, key=lambda bot: bot.radius)
    bcenter, bradius = bot_with_largest_r
    part1 = sum(bcenter.manhattan_distance_to(bot.center) <= bradius for bot in bots)

    minx, maxx, miny, maxy, minz, maxz = Extremes.create_from([bot.center for bot in bots])
    search_space = SearchSpace(Point3D(minx, miny, minz),
                               max(maxx-minx, maxy-miny, maxz-minz),
                               bots)

    part2 = None
    heap = [(1000, search_space)]
    while heap:
        _, current_space = heapq.heappop(heap)
        if current_space.cube.width == 1:
            if part2 is None or current_space.is_better_than(part2):
                part2 = current_space
            continue

        for smaller_space in current_space.split():
            if smaller_space.bot_count == 0:
                continue

            if part2 is not None and part2.is_better_than(smaller_space):
                continue

            priority = -smaller_space.bot_count
            heapq.heappush(heap, (priority, smaller_space))

    return (part1, part2.cube.corner.manhattan_distance_to((0,0,0)))


print(', '.join(f'Part {i+1}: {answer}' for i, answer in enumerate(solution())))
