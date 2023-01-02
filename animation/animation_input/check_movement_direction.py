import logging


class CheckMovementDirection:
    def __init__(self):
        self.__turn_result = {}
        self.__move_result = {}
        self.__current_direction = None

    @property
    def turn_result(self):
        return self.__turn_result

    @turn_result.setter
    def turn_result(self, value):
        self.__turn_result = value

    @property
    def move_result(self):
        return self.__move_result

    @move_result.setter
    def move_result(self, value):
        self.__move_result = value

    @property
    def current_direction(self):
        return self.__current_direction

    @current_direction.setter
    def current_direction(self, value):
        self.__current_direction = value

    def judge_direction(self, current_direction, square_unit_A, square_unit_B):
        self.__turn_result = {}
        self.__move_result = {}
        dis_x = square_unit_B[0] - square_unit_A[0]
        dis_y = square_unit_B[1] - square_unit_A[1]

        if dis_x == 0 and dis_y == 1:
            if current_direction != 'down':
                if current_direction == 'up':
                    self.__turn_result['event_type'] = 'turn_180'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'left':
                    self.__turn_result['event_type'] = 'turn_left'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'right':
                    self.__turn_result['event_type'] = 'turn_right'
                    self.__turn_result['coors'] = square_unit_A
                current_direction = 'down'
            self.__move_result['event_type'] = 'move_down'
            self.__move_result['coors'] = square_unit_B

        elif dis_x == 0 and dis_y == -1:
            if current_direction != 'up':
                if current_direction == 'down':
                    self.__turn_result['event_type'] = 'turn_180'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'left':
                    self.__turn_result['event_type'] = 'turn_right'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'right':
                    self.__turn_result['event_type'] = 'turn_left'
                    self.__turn_result['coors'] = square_unit_A
                current_direction = 'up'
            self.__move_result['event_type'] = 'move_up'
            self.__move_result['coors'] = square_unit_B

        elif dis_x == 1 and dis_y == 0:
            if current_direction != 'right':
                if current_direction == 'down':
                    self.__turn_result['event_type'] = 'turn_left'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'up':
                    self.__turn_result['event_type'] = 'turn_right'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'left':
                    self.__turn_result['event_type'] = 'turn_180'
                    self.__turn_result['coors'] = square_unit_A
                current_direction = 'right'
            self.__move_result['event_type'] = 'move_right'
            self.__move_result['coors'] = square_unit_B

        elif dis_x == -1 and dis_y == 0:
            if current_direction != 'left':
                if current_direction == 'down':
                    self.__turn_result['event_type'] = 'turn_right'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'up':
                    self.__turn_result['event_type'] = 'turn_left'
                    self.__turn_result['coors'] = square_unit_A
                elif current_direction == 'right':
                    self.__turn_result['event_type'] = 'turn_180'
                    self.__turn_result['coors'] = square_unit_A
                current_direction = 'left'
            self.__move_result['event_type'] = 'move_left'
            self.__move_result['coors'] = square_unit_B
        self.__current_direction = current_direction
        return current_direction
