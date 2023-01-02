class Job:
    __count = 0

    def __init__(self, delivery_position, picking_position, id=None):
        Job.__count += 1
        self.__index = Job.__count
        self.__id = id if id is not None else "Job#" + str(self.__index)
        self.__delivery_position = delivery_position
        self.__picking_position = picking_position
        self.__arrival_time = None

    @property
    def id(self):
        return self.__id

    @property
    def delivery_position(self):
        """A square unit where the vehicle to deliver items."""
        return self.__delivery_position

    @delivery_position.setter
    def delivery_position(self, value):
        self.__delivery_position = value

    @property
    def picking_position(self):
        """A square unit where the vehicle to pick items."""
        return self.__picking_position

    @picking_position.setter
    def picking_position(self, value):
        self.__picking_position = value

    @property
    def arrival_time(self):
        """Time when job arrive the system."""
        return self.__arrival_time

    @arrival_time.setter
    def arrival_time(self, value):
        self.__arrival_time = value

