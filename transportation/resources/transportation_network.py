import pandas as pd
import numpy as np

from transportation.resources.square_unit import SquareUnit


class TransportationNetwork:
    __count = 0

    def __init__(self, start_point, dimension, vehicle_df, id=None, obstacle_list=None):
        TransportationNetwork.__count += 1
        self.__index = TransportationNetwork.__count
        self.__id = id if id is not None else 'TransportationNetwork#' + str(self.__index)
        self.__start_point = start_point
        self.__dimension = dimension
        self.__obstacle_list = obstacle_list
        self.__vehicle_df = vehicle_df
        self.__grid_df = None
        self.generate_grid_df()

    @property
    def start_point(self):
        """Indicate the start point of the network, it is a tuple of int."""
        return self.__start_point

    @start_point.setter
    def start_point(self, value):
        self.__start_point = value

    @property
    def dimension(self):
        """
        Indicate how many rows and columns the network has.

        The first element is row number, second is the column number."""
        return self.__dimension

    @dimension.setter
    def dimension(self, value):
        self.__dimension = value

    @property
    def obstacle_list(self):
        """Record the list of girds that cannot pass through vehicles."""
        return self.__obstacle_list

    @obstacle_list.setter
    def obstacle_list(self, value):
        self.__obstacle_list = value

    @property
    def vehicle_df(self):
        """
        Vehicle dataframe, recording the dynamic properties of vehicles.

        Properties are: 'VehicleId', 'StartPosition', 'DynamicRoute', 'Reservation', 'ReservationPending',

        'RequestTime', 'ReservationToRelease', 'JobList', 'Status'
        """
        return self.__vehicle_df

    @vehicle_df.setter
    def vehicle_df(self, value):
        self.__vehicle_df = value

    @property
    def grid_df(self):
        """
        Square Unit dataframe, recording the dynamic properties of square units.

        Properties are: 'SquareUnitIndex', 'IsObstacle', 'VehicleVia', 'PendingVehicle', 'OccupiedVehicle'
        """
        return self.__grid_df

    @grid_df.setter
    def grid_df(self, value):
        self.__grid_df = value

    def generate_grid_df(self):
        """Transfer square unit dynamic properties into dataframe."""
        grid_df = pd.DataFrame(columns=['SquareUnitIndex', 'IsObstacle', 'VehicleVia', 'OccupiedVehicle'])
        index = 0
        for row in range(self.__dimension[0]):
            for column in range(self.__dimension[1]):
                row_index = self.__start_point[0] + row
                column_index = self.__start_point[1] + column
                new_square_uint = SquareUnit(row_index, column_index)
                square_unit_index = new_square_uint.square_unit_index
                row_value_list = self.__get_row_value_list(square_unit_index)
                grid_df.loc[index] = row_value_list
                index += 1
        self.__grid_df = grid_df

    def __get_row_value_list(self, square_unit_index):
        """Get square unit dynamic properties."""
        row_value_list = [square_unit_index, False, 0, np.nan]
        if self.__obstacle_list is not None and square_unit_index in self.__obstacle_list:
            row_value_list[1] = True

        for i in list(self.__vehicle_df.index):
            park_position = self.__vehicle_df.loc[i, 'StartPosition']
            if square_unit_index == park_position:
                row_value_list[3] = self.__vehicle_df.loc[i, 'Vehicle']

        return row_value_list
