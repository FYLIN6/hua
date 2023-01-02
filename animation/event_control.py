import sys

from animation.pathmover import Pathmover
from animation.pathmover_rect import PathmoverRect
from animation.utils import *

class EventControl():
    def __init__(self, SURF, CELL_CTRL, INFO_BOX):
        self.SURF = SURF
        self.CELL_CTRL = CELL_CTRL
        self.INFO_BOX = INFO_BOX
        self.pause = True
        self.simulation_time = sys.maxsize
        self.simulation_dt = 0.1
        self.ratio_speed_dt = 7/10 # simulation dt / speed; not rigorously set
        self.pathmover_rects = self.create_rect()

    def set_pause(self, value):
        """
        Set pause value

        @param value: Target value to be set to
        """
        self.pause = value

    def create_rect(self):
        """
        Create movable rect for each Pathmover object
        """
        pathmover_rects = []
        raw_data = load_input_files()
        for i, each in enumerate(raw_data):
            mover = Pathmover(each)
            pathmover_rects.append(PathmoverRect(self.SURF, self.CELL_CTRL, self.INFO_BOX, mover, speed=self.simulation_dt/self.ratio_speed_dt))

            # get the minimum start time
            if datetime_to_timestamp(mover.start_time) < self.simulation_time:
                self.simulation_time = datetime_to_timestamp(mover.start_time)
            
        return pathmover_rects

    def update_rects(self, global_time, dt):
        """
        Update rects (calls update function of each PathmoverRect object)

        @param global_time: int; global game time
        @param dt: int; smallest unit of time
        """
        # if pause == True, stop all rects' movements
        if self.pause: return
        for each in self.pathmover_rects:
            each.update(self.simulation_time, dt)
        self.simulation_time += self.simulation_dt

        # check if all events are completed
        if self.check_all_completed():
            self.INFO_BOX.add_text("All events dispatched.", color=RED)
            self.pause = True

    def draw_rects(self):
        """
        Draw rects (call draw function of each PathmoverRect object)
        """
        for each in self.pathmover_rects:
            each.draw()
    
    def check_all_completed(self):
        for each in self.pathmover_rects:
            if not each.all_completed():
                return False
        return True