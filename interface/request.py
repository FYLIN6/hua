import numpy as np
from interface.route import Route
import random


class Request:
    deadlock_place = {}
    def __init__(self, vehicle, vehicle_df, grid_df):
        self.__vehicle = vehicle
        self.__vehicle_df = vehicle_df
        self.__grid_df = grid_df
        self.__partial_route_length = 1  # An integer greater than 0 and can be adjusted according to the specific situation of the system
        self.__block_unit = set()
        xm = ym = 0
        for (y, x) in self.__grid_df['SquareUnitIndex']:
            xm = max(x, xm)
            ym = max(y, ym)
        self.__dim = [xm, ym]

    def default_algo_to_get_partial_route(self):
        """
        An algorithm to get a partial route of the remaining route for the next move

        Use __partial_route_length as the length of the partial route;
        Get the dynamic_route which means the remaining route;
        Get the reservation_to_release which represents the partial route that has been reserved before, waiting to be released after use;
        If the reservation_to_release is empty,
            temp_route is equal to dynamic_route;
        else
            After removing reservation_to_release from dynamic_route to get temp_route;

        If the length of temp_route is greater than __partial_route_length
            then get a partial route of length __partial_route_length starting from the head of temp_route;
        else
            the partial route to be obtained is equal to temp_route;

        @return partial_route (<List<Tuple<int, int>, Tuple<int, int>, ...>>)
                (For example: [(0, 1), (0, 2), (0, 3)])
        """
        temp_route = []
        partial_route = []
        dynamic_route = self.__vehicle_df.loc[self.__vehicle.id, 'DynamicRoute']
        reservation_to_release = self.__vehicle_df.loc[self.__vehicle.id, 'ReservationToRelease']
        if not isinstance(reservation_to_release, list) and np.isnan(reservation_to_release):
            temp_route += dynamic_route
        else:
            temp_route += dynamic_route[len(reservation_to_release) - len(dynamic_route):]

        if len(temp_route) > self.__partial_route_length:
            for i in range(self.__partial_route_length):
                partial_route.append(temp_route[i])
        else:
            partial_route = temp_route

        return partial_route

    def user_algo(self):
        """
        User defines a new algorithm to get a partial route of the remaining route for the next move

        @return partial_route (<List<Tuple<int, int>, Tuple<int, int>, ...>>)
                (For example: [(0, 1), (0, 2), (0, 3)])
        """
        # return NoneD

        self.update_deadlock_place()
        temp_route = []
        partial_route = []
        dynamic_route = self.__vehicle_df.loc[self.__vehicle.id, 'DynamicRoute']
        reservation_to_release = self.__vehicle_df.loc[self.__vehicle.id, 'ReservationToRelease']
        # start_position = None
        if not isinstance(reservation_to_release, list) and np.isnan(reservation_to_release):
            # partial_route_first_request
            temp_route += dynamic_route
            start_position = self.__vehicle_df.loc[self.__vehicle.id, 'StartPosition']
        else:
            # partial_route_request
            temp_route += dynamic_route[len(reservation_to_release) - len(dynamic_route):]
            start_position = reservation_to_release[-1]

        # requesting more grids as possible until it may cause deadlock
        # if can't request any grid, reroute the path
        for step in range(1, self.__partial_route_length + 1):
            if len(temp_route) < step:
                break

            square_unit = temp_route[step - 1]
            occupied_vehicle_id = self.last_zone_occupied_vehicle(square_unit)

            if occupied_vehicle_id is not None:
                # deadlock avoidance
                if self.check_circle_deadlock(square_unit):
                    if len(partial_route) < 1:
                        # solve deadlock
                        self.__block_unit.add(temp_route[0])
                        Request.deadlock_place[temp_route[0]] = start_position
                        route_list = self.reroute(start_position, dynamic_route[-1])
                        if not route_list:
                            break
                            # if dynamic_route[-1] in self.__block_unit:
                            #     # random walk
                            #     self.__block_unit.remove(dynamic_route[-1])
                            #     cnt = 0
                            #     while cnt < 50 and not route_list:
                            #         route_list = self.random_walk(start_position, dynamic_route[-1])
                            #         cnt += 1
                            #     if not route_list:
                            #         print("random walk failed")
                            #         break
                            # else:
                            #     break
                        self.__vehicle.static_route[-len(temp_route):] = route_list[1:]
                        self.__vehicle_df.loc[self.__vehicle.id, 'DynamicRoute'][-len(temp_route):] = route_list[1:]
                        partial_route = self.user_algo()
                        return partial_route

                    # partial_route.pop() # avoid one step further
                break

            partial_route.append(square_unit)

        if not partial_route:
            partial_route.append(temp_route[0])
        return partial_route

    def check_circle_deadlock(self, zone_to_check):
        restrictive = True
        checked_zones = []
        occupied_vehicle_id = self.last_zone_occupied_vehicle(zone_to_check)
        deadlock_predicted = False
        while zone_to_check is not None and occupied_vehicle_id is not None:
            if zone_to_check in checked_zones:
                deadlock_predicted = True
                break
            else:
                checked_zones.append(zone_to_check)
                zone_to_check = self.next_zone_of_vehicle(occupied_vehicle_id)
                if zone_to_check is None:
                    break
                occupied_vehicle_id = self.last_zone_occupied_vehicle(zone_to_check)

        return deadlock_predicted or (zone_to_check is None and restrictive)

    def last_zone_occupied_vehicle(self, zone):
        occupied_vehicle = self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] ==
                                              zone, 'OccupiedVehicle'].tolist()[0]
        if occupied_vehicle is np.nan:
            return None
        reservation_to_release = self.__vehicle_df.loc[occupied_vehicle.id, 'ReservationToRelease']
        if not isinstance(reservation_to_release, list) and np.isnan(reservation_to_release):
            return occupied_vehicle.id
        if reservation_to_release[-1] == zone:
            return occupied_vehicle.id
        return None

    def next_zone_of_vehicle(self, vehicle_id):
        dynamic_route = self.__vehicle_df.loc[vehicle_id, 'DynamicRoute']
        reservation_to_release = self.__vehicle_df.loc[vehicle_id, 'ReservationToRelease']
        if len(dynamic_route) == 0:
            return None
        if not isinstance(reservation_to_release, list) and np.isnan(reservation_to_release):
            # partial_route_first_request
            return dynamic_route[0]
        else:
            # partial_route_request
            return dynamic_route[len(reservation_to_release) - len(dynamic_route)]

    def reroute(self, start_position, end_position):
        # find another road by routing and blocking the path leading deadlock
        route = Route(None, self.__vehicle, start_position, end_position, self.__block_unit)
        route_list = route.user_algo()
        if route_list is None:
            route_list = route.default_algo_to_generate_route()
        print("reroute: ")
        print("route_list: ", route_list)
        print("block_unit: ", self.__block_unit)
        if len(route_list) == 0:
            # print("No other paths")
            # print("block unit: ", self.__block_unit)
            return []

        point = self.check_route(route_list)
        if point is not None:
            self.__block_unit.add(point)
            print("add block_unit: ", point)
            route_list = self.reroute(start_position, end_position)
        return route_list

    def check_route(self, route_list):
        pre_point = None
        for point in route_list:
            if Request.deadlock_place.get(point) is not None:
                if Request.deadlock_place.get(point) == pre_point:
                    occupied_vehicle = self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] ==
                                                          point, 'OccupiedVehicle'].tolist()[0]
                    if occupied_vehicle != self.__vehicle:
                        return point
            pre_point = point
        return None

    def update_deadlock_place(self):
        deadlock_place_list = list(Request.deadlock_place.keys())
        for point in deadlock_place_list:
            print("deadlock_place_list: ", point)
            occupied_vehicle = self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] ==
                                                  point, 'OccupiedVehicle'].tolist()[0]
            if occupied_vehicle is np.nan:
                Request.deadlock_place.pop(point)
                print("remove: ", point)

    def random_walk(self, start_position, end_position):
        # prevent blocking destination
        # find an intermediate point randomly
        walk_range = 2
        candidate_grid = []
        xl = max(0, start_position[1] - walk_range)
        xr = min(start_position[1] + walk_range, self.__dim[0])
        yl = max(0, start_position[0] - walk_range)
        yr = min(start_position[0] + walk_range, self.__dim[1])
        for x in range(xl, xr + 1):
            for y in range(yl, yr + 1):
                if y == yl or y == yr or x == xl or x == xr:
                    candidate_grid.append((y, x))
        # print(candidate_grid)
        intermediate = random.choice(candidate_grid)

        route_list_pre = self.reroute(start_position, intermediate)
        route_list_post = self.reroute(intermediate, end_position)
        if len(route_list_pre) < 2 or len(route_list_post) < 2:
            return []
        route_list_pre[-1:] = route_list_post[:]
        return route_list_pre
