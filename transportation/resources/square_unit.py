class SquareUnit:
    def __init__(self, row_index, column_index):
        self.__row_index = row_index
        self.__column_index = column_index
        self.__square_unit_index = (self.__row_index, self.__column_index)

    @property
    def square_unit_index(self):
        """
        Indicate which row and column the square unit is in the network.

        First value is row_index, second_value is column_index.
        """
        return self.__square_unit_index

    @square_unit_index.setter
    def square_unit_index(self, value):
        self.__square_unit_index = value