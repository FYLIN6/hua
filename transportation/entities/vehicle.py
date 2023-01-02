from animation.animation_input.check_movement_direction import CheckMovementDirection

class Vehicle:
    __count = 0

    def __init__(self, park_position, id=None, pace=1):
        Vehicle.__count += 1
        self.__index = Vehicle.__count
        self.__id = id if id is not None else 'Vehicle#' + str(self.__index)
        self.__pace = pace
        self.__park_position = park_position
        self.__static_route = None
        self.__check_movement_direction = CheckMovementDirection()

    @property
    def id(self):
        return self.__id

    @property
    def pace(self):
        """The travel pace of the vehicle. It reflects how many seconds are needed to travel one square unit."""
        return self.__pace

    @pace.setter
    def pace(self, value):
        self.__pace = value

    @property
    def static_route(self):
        """The static property of vehicle, recording the full route from one position to another."""
        return self.__static_route

    @static_route.setter
    def static_route(self, value):
        self.__static_route = value

    @property
    def park_position(self):
        """Vehicle's parking position"""
        return self.__park_position

    @property
    def check_movement_direction(self):
        """Use to check each vehicle direction for animation ."""
        return self.__check_movement_direction


