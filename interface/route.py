import sys

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cost = sys.maxsize


class Route:
    default_transportation_network = None
    def __init__(self, transportation_network, vehicle, start_square_unit, end_square_unit, block_unit = None):
        if transportation_network is None:
            self.__transportation_network = Route.default_transportation_network
        else:
            self.__transportation_network = transportation_network
            Route.default_transportation_network = self.__transportation_network

        self.__vehicle = vehicle
        self.__start_square_unit = start_square_unit
        self.__end_square_unit = end_square_unit
        self.__obstacle_set = []
        self.__open_set = []
        self.__close_set = []
        self.__dimension_length = self.__transportation_network.dimension[0]
        self.__dimension_width = self.__transportation_network.dimension[1]
        self.__grid_df = self.__transportation_network.grid_df
        self.__vehicle_df = self.__transportation_network.vehicle_df
        self.__block_unit = block_unit

    def default_algo_to_generate_route(self):
        """
        Call __astar_path() to create a full route of vehicle

        Here, the parking positions of other vehicles are also used as obstacles and the vehicle is not allowed to pass.
        The user does not need to do the same.

        @return self.__astar_path() (a path: <List<Tuple<int, int>, Tuple<int, int>, ...>>)
        """
        self.__obstacle_set = set(self.__grid_df.loc[self.__grid_df['IsObstacle'] == True]['SquareUnitIndex'])
        for row_vehicle in self.__vehicle_df.itertuples():
            current_vehicle = getattr(row_vehicle, "Vehicle")
            if current_vehicle is not self.__vehicle:
                self.__obstacle_set.add(current_vehicle.park_position)

        return self.__astar_path()

    def __astar_path(self):
        """
        Use A* algorithm to create a full route of the vehicle

        @return self.__build_path(p) (a path: <List<Tuple<int, int>, Tuple<int, int>, ...>>)
        """
        start_point = Point(self.__start_square_unit[0], self.__start_square_unit[1])
        start_point.cost = 0
        self.__open_set.append(start_point)
        while True:
            index = self.__select_point_in_open_set()
            if index < 0:
                print('No path found')
                return []
            p = self.__open_set[index]

            if self.__is_end_point(p):
                return self.__build_path(p)

            del self.__open_set[index]
            self.__close_set.append(p)

            x = p.x
            y = p.y
            self.__process_point(x - 1, y, p)
            self.__process_point(x, y - 1, p)
            self.__process_point(x + 1, y, p)
            self.__process_point(x, y + 1, p)

    def __base_cost(self, p):
        """Distance to start point"""
        x_dis = abs(p.x - self.__start_square_unit[0])
        y_dis = abs(p.y - self.__start_square_unit[1])
        return x_dis + y_dis

    def __heuristic_cost(self, p):
        """Distance to end point"""
        x_dis = abs(self.__end_square_unit[0] - p.x)
        y_dis = abs(self.__end_square_unit[1] - p.y)
        return x_dis + y_dis

    def __total_cost(self, p):
        return self.__base_cost(p) + self.__heuristic_cost(p)

    def __is_valid_point(self, x, y):
        if x < 0 or y < 0:
            return False
        if x >= self.__dimension_length or y >= self.__dimension_width:
            return False
        return not self.__is_obstacle(x, y)

    def __is_obstacle(self, x, y):
        for point in self.__obstacle_set:
            if point[0] == x and point[1] == y:
                return True
        return False

    def __is_in_point_set(self, p, point_set):
        for point in point_set:
            if point.x == p.x and point.y == p.y:
                return True
        return False

    def __is_in_open_set(self, p):
        return self.__is_in_point_set(p, self.__open_set)

    def __is_in_close_set(self, p):
        return self.__is_in_point_set(p, self.__close_set)

    def __is_start_point(self, p):
        return p.x == self.__start_square_unit[0] and p.y == self.__start_square_unit[1]

    def __is_end_point(self, p):
        return p.x == self.__end_square_unit[0] and p.y == self.__end_square_unit[1]

    def __process_point(self, x, y, parent):
        if not self.__is_valid_point(x, y):
            return  # Do nothing for invalid point

        p = Point(x, y)

        if self.__is_in_close_set(p):
            return  # Do nothing for visited point

        if not self.__is_in_open_set(p):
            p.parent = parent
            p.cost = self.__total_cost(p)
            self.__open_set.append(p)

    def __select_point_in_open_set(self):
        index = 0
        selected_index = -1
        min_cost = sys.maxsize
        for p in self.__open_set:
            cost = p.cost
            if cost < min_cost:
                min_cost = cost
                selected_index = index
            index += 1
        return selected_index

    def __build_path(self, p):
        path = []
        while True:
            path.insert(0, (p.x, p.y))
            if self.__is_start_point(p):
                break
            else:
                p = p.parent
        return path

    def user_algo(self):
        """
        User defines a new routing algorithm to create a full route of the vehicle

        @return path (<List<Tuple<int, int>, Tuple<int, int>, ...>>)
                (For example: [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)])
        """
        self.__obstacle_set = set(self.__grid_df.loc[self.__grid_df['IsObstacle'] == True]['SquareUnitIndex'])
        if self.__block_unit is not None:
            self.__obstacle_set.update(self.__block_unit)
        for row_vehicle in self.__vehicle_df.itertuples():
            current_vehicle = getattr(row_vehicle, "Vehicle")
            if current_vehicle is not self.__vehicle:
                self.__obstacle_set.add(current_vehicle.park_position)

        return self.__astar_path()
        return path


