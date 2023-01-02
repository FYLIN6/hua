import numpy as np


class Request:
    def __init__(self, vehicle, vehicle_df, grid_df):
        self.__vehicle = vehicle
        self.__vehicle_df = vehicle_df
        self.__grid_df = grid_df
        self.__partial_route_length = 3  # An interger greater than 0 and can be adjusted according to the specific situation of the system

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
        partial_route = None
        return partial_route
