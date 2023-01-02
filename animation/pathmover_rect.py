import pygame
import time

from log.logger import Logger
from animation.utils import *
from animation.event import Event
from config_pack.file_config import FileConfig


class PathmoverRect(pygame.sprite.Sprite):
    def __init__(self, SURF, CELL_CTRL, INFO_BOX, pathmover, color=GREEN, alpha=150, speed=0.05):
        super().__init__()
        self.SURF = SURF
        self.CELL_CTRL = CELL_CTRL
        self.INFO_BOX = INFO_BOX
        self.pathmover = pathmover
        self.name = self.pathmover.get_name()
        self.type = self.pathmover.get_type()
        self.color = color
        self.alpha = (alpha,)
        self.speed = speed
        self.timer = 0
        self.loaded = False
        self.current_event = None
        self.current_coors = None
        self.reserved_path = []
        self.delivery_route = None
        self.job_delivery_position = None
        self.route_status = False
        self.current_direction = None
        self.file_config = FileConfig()
        self.initialise()

    def initialise(self):
        """
        Initialise certain attributes of the PathmoverRect object
        """
        center = self.get_center(self.pathmover.start_coors)
        self.mover_width, self.mover_length = self.pathmover.mover_info['width'], self.pathmover.mover_info['length']
        width, length = self.get_sides(self.pathmover.mover_info['occupied_width'],
                                       self.pathmover.mover_info['occupied_length'])
        self.rect = pygame.Rect(0, 0, width, length)
        self.rect.center = center
        # let the position of the object be the center of the rect
        self.pos = self.rect.center
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.current_direction = self.pathmover.mover_info['initial_direction']
        self.blit_image()
        self.image.fill(self.color + self.alpha)

    def update(self, simulation_time, dt):
        """
        Check certain conditions and update object accordingly

        @param simulation time: Simulation time
        @param dt: Smallest unit of time
        """
        # always update clock
        self.INFO_BOX.update_time("{:.1f}".format(simulation_time))
        # if the first event has not been dispatched, dispatch it
        if not isinstance(self.current_event, Event):
            self.dispatch_events(simulation_time, dt)
        else:
            # if current event is completed, reset timer and dispatch the next event
            if self.current_event.completed:
                if self.current_event.event_type != "end":
                    # self.INFO_BOX.update_time(self.current_event.datetime)
                    pass
                self.timer = 0
                self.dispatch_events(simulation_time, dt)
            else:
                self.move(dt)

    def dispatch_events(self, simulation_time, dt):
        """
        Dispatch events

        @param simulation_time: Simulation time
        @param dt: Smallest unit of time
        """
        if self.all_dispatched(): return
        # if the current event is not completed, don't dispatch next event
        if isinstance(self.current_event, Event) and self.current_event.completed == False: return

        for i, event in enumerate(self.pathmover.events):
            if not event.dispatched and event.timestamp <= simulation_time:
                self.current_event = event
                self.INFO_BOX.add_text("Event dispatched {} @ {}.".format(self.name, int(simulation_time)))
                event.set_dispatched(True)
                if self.all_dispatched(): self.INFO_BOX.add_text("All events for {} dispatched.".format(self.name))
                self.move(dt)

    def move(self, dt):
        """
        Move (or not move) according to the current event

        @param dt: Smallest unit of time
        """
        event_type = self.current_event.event_type
        if event_type == "start":
            self.start(dt)
        elif event_type == "end":
            self.end(dt)
        elif event_type == "move_up":
            self.move_up(dt)
        elif event_type == "move_down":
            self.move_down(dt)
        elif event_type == "move_left":
            self.move_left(dt)
        elif event_type == "move_right":
            self.move_right(dt)
        elif event_type == "turn_left":
            self.turn_left(dt)
        elif event_type == "turn_right":
            self.turn_right(dt)
        elif event_type == "turn_180":
            self.turn_180(dt)
        elif event_type == "wait":
            self.wait(dt)
        elif event_type == "reserve":
            self.reserve(dt)
        elif event_type == "release":
            self.release(dt)
        elif event_type == "teleport":
            self.teleport(dt)
        elif event_type == "load":
            self.load(dt)
        elif event_type == "unload":
            self.unload(dt)
        elif event_type == "route":
            self.route(dt)
        elif event_type == "delivery position":
            self.delivery_position(dt)
        elif event_type == "release route":
            self.release_route(dt)
        else:
            raise Exception("Unrecognised event type.")

    """
    MOVEMENT CONTROL METHODS
    """

    def start(self, dt):
        self.INFO_BOX.add_text("{} starting now...".format(self.name), color=SAND)
        self.current_event.set_completed(True)

    def end(self, dt):
        self.INFO_BOX.add_text("{} has ended.".format(self.name), color=RED)
        self.current_event.set_completed(True)

    def wait(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} is idle now.".format(self.name))
        self.current_event.set_completed(True)

    def reserve(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("Reserved path for {}.".format(self.name))
        self.reserved_path.extend(self.current_event.coors)
        self.current_event.set_completed(True)

    def route(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("Job Delivery Route for {}.".format(self.name))
        self.delivery_route = self.current_event.coors
        self.route_status = True
        self.current_event.set_completed(True)

    def delivery_position(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("Job Delivery Position for {}.".format(self.name))
        self.job_delivery_position = self.current_event.coors
        self.route_status = True
        self.current_event.set_completed(True)

    def release(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("Released path for {}.".format(self.name))
        self.reserved_path = [i for i in self.reserved_path if i not in self.current_event.coors]
        # self.reservation_status = False
        self.current_event.set_completed(True)

    def release_route(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("Released route for {}.".format(self.name))
        self.route_status = False
        self.current_event.set_completed(True)

    def teleport(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("Teleporting {}...".format(self.name))
        center = self.get_center(self.current_event.coors)
        self.rect.center = center
        # let the position of the object be the center of the rect
        self.pos = self.rect.center
        self.current_event.set_completed(True)

    def move_up(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} moving up...".format(self.name))
        self.timer += dt
        if self.check_if_reached_coors(self.current_event.coors):
            self.current_event.set_completed(True)
        else:
            self.pos = self.pos[0], self.pos[1] - self.speed * dt
            self.rect.center = self.pos

    def move_down(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} moving down...".format(self.name))
        self.timer += dt
        if self.check_if_reached_coors(self.current_event.coors):
            self.current_event.set_completed(True)
        else:
            self.pos = self.pos[0], self.pos[1] + self.speed * dt
            self.rect.center = self.pos

    def move_right(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} moving right...".format(self.name))
        self.timer += dt
        if self.check_if_reached_coors(self.current_event.coors):
            self.current_event.set_completed(True)
        else:
            self.pos = self.pos[0] + self.speed * dt, self.pos[1]
            self.rect.center = self.pos

    def move_left(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} moving left...".format(self.name))
        self.timer += dt
        if self.check_if_reached_coors(self.current_event.coors):
            self.current_event.set_completed(True)
        else:
            self.pos = self.pos[0] - self.speed * dt, self.pos[1]
            self.rect.center = self.pos

    def turn_left(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} turning left...".format(self.name))
        self.timer += dt

        if self.timer > self.current_event.duration:
            self.get_next_direction("left")
            self.blit_image()
            self.current_event.set_completed(True)

    def turn_right(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} turning right...".format(self.name))
        self.timer += dt

        if self.timer > self.current_event.duration:
            self.get_next_direction("right")
            self.blit_image()
            self.current_event.set_completed(True)

    def turn_180(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} turning 180 degree...".format(self.name))
        self.timer += dt

        if self.timer > self.current_event.duration:
            self.get_next_direction("180")
            self.blit_image()
            self.current_event.set_completed(True)

    def load(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} loading...".format(self.name))
        self.timer += dt

        if self.timer > self.current_event.duration:
            self.CELL_CTRL.remove_load(self.current_event.coors)

            # remove pallet
            if self.type != "ReachTruck":
                # show pallet and load on mover
                self.loaded = True
                self.blit_image()

            self.current_event.set_completed(True)

    def unload(self, dt):
        if self.timer == 0: self.INFO_BOX.add_text("{} unloading...".format(self.name))
        self.timer += dt

        if self.timer > self.current_event.duration:
            self.CELL_CTRL.add_load(self.current_event.coors)
            if self.type != "ReachTruck":
                self.loaded = False
                self.blit_image()
            self.current_event.set_completed(True)

    """
    END OF MOVEMENT CONTROL METHODS
    """

    def blit_image(self):
        """
        Blit a suitable image for the mover
        """
        img_path = self.file_config.get_animation_path() + "Images/" + self.type + "_" + self.current_direction + ".png"
        if self.loaded and self.type != "ReachTruck":
            img_path = self.file_config.get_animation_path() + "Images/" + self.type + "_" + "loaded" + "_" + self.current_direction + ".png"
        self.car_image = pygame.image.load(img_path)
        self.car_image = pygame.transform.scale(
            self.car_image,
            (int(self.CELL_CTRL.cell_width) * self.mover_width, int(self.CELL_CTRL.cell_height) * self.mover_length)
        )

    def draw(self):
        """
        Draw rect
        This is usually called after update method so to reflect the update
        """
        # show route
        if self.route_status:
            self.CELL_CTRL.fill_cells_by_list(self.delivery_route, SEAGREEN, margin=6.5, correction=3.5)
            self.CELL_CTRL.fill_cells_by_list(self.job_delivery_position, RED, margin=6.5, correction=3.5)

        # show reserved path
        self.CELL_CTRL.fill_cells_by_list(self.reserved_path, margin=5, correction=2.5)

        # show start and end cells
        self.draw_start_end_cells()
        # show mover rectangle 
        self.SURF.blit(self.image, self.rect)

        # show mover image
        car_image_rect = self.car_image.get_rect(center=self.pos)
        self.SURF.blit(self.car_image, car_image_rect)

        # show mover text
        self.image.blit(
            pygame.font.SysFont('Times New Roman', 13).render(self.name[-2:], False, BLACK),
            [0, 0]
        )

    def draw_start_end_cells(self):
        """
        Draw start and end coors; GREEN for start, RED for end
        """
        start_x, start_y = self.pathmover.start_coors[0], self.pathmover.start_coors[1]
        if self.pathmover.end_coors is not None and self.pathmover.end_coors is not None:
            end_x, end_y = self.pathmover.end_coors[0], self.pathmover.end_coors[1]
            self.CELL_CTRL.fill_single_cell(end_x, end_y, color=ORANGE, margin=5)
        self.CELL_CTRL.fill_single_cell(start_x, start_y, color=CYAN, margin=5)

    def all_dispatched(self):
        """
        Check if all events are dispatched
        """
        for event in self.pathmover.events:
            if event.dispatched == False: return False
        return True

    def all_completed(self):
        """
        Check if all events are completed
        """
        for event in self.pathmover.events:
            if event.completed == False:
                return False

        return True

    def get_sides(self, width, length, margin=4):
        """
        Get the width and length for drawing the rect

        @param width: Width of pathmover as stated in json
        @param length: Length of pathmover as stated in json
        @param margin: Spacing between rect and the 4 sides
        """
        rect_width, rect_length = width, length
        cell_width, cell_height = self.CELL_CTRL.cell_width, self.CELL_CTRL.cell_height
        return rect_width * cell_width - margin * 2, rect_length * cell_height - margin * 2

    def get_center(self, coors, margin_x=0):
        """
        Get the center position of the cell specified by coors

        @param coors: 3-dimensioanl coordinates [x,y,z]
        """
        try:
            x, y = self.CELL_CTRL.x_indices[coors[0]], self.CELL_CTRL.y_indices[coors[1]]
        except IndexError:
            raise Exception("Coordinates in jason files exceed Grid Size defined in animation_main.py.")
        return x + self.CELL_CTRL.cell_width / 2 + margin_x, y + self.CELL_CTRL.cell_height / 2

    def check_if_reached_coors(self, coors, margin=1.0):
        """
        Check if rect has reach the position specified by coors

        @param coors: 3-dimensioanl coordinates [x,y,z]
        @param margin: Account for floating error (make things prettier/more aligned)
        """
        typ = self.current_event.event_type
        target_pos = tuple([int(i) for i in self.get_center(coors)])

        if typ == "move_right":
            if self.pos[0] >= target_pos[0] - margin:
                self.pos = target_pos[0], target_pos[1]
                self.rect.center = self.pos
                return True
        elif typ == "move_down":
            if self.pos[1] >= target_pos[1] - margin:
                self.pos = target_pos[0], target_pos[1]
                self.rect.center = self.pos
                return True
        elif typ == "move_left":
            if self.pos[0] <= target_pos[0] + margin:
                self.pos = target_pos[0], target_pos[1]
                self.rect.center = self.pos
                return True
        elif typ == "move_up":
            if self.pos[1] <= target_pos[1] + margin:
                self.pos = target_pos[0], target_pos[1]
                self.rect.center = self.pos
                return True
        return False

    def check_initial_direction(self):
        """
        Check the initial direction of the mover
        """
        direction = ""
        for each in self.pathmover.events:
            if each.event_type.startswith("move"):
                direction = each.event_type.split("_")[1]
                break

        if direction == "": raise Exception("Moving direction not found for {}".format(self.name))

        return direction

    def get_next_direction(self, turn_direction):
        """
        Get the next direction of the mover

        @param turn_direction: The direction the mover will be turning to
        """
        if turn_direction == "right":
            if self.current_direction == "right":
                self.current_direction = "down"
            elif self.current_direction == "down":
                self.current_direction = "left"
            elif self.current_direction == "left":
                self.current_direction = "up"
            elif self.current_direction == "up":
                self.current_direction = "right"
        elif turn_direction == "left":
            if self.current_direction == "right":
                self.current_direction = "up"
            elif self.current_direction == "down":
                self.current_direction = "right"
            elif self.current_direction == "left":
                self.current_direction = "down"
            elif self.current_direction == "up":
                self.current_direction = "left"
        elif turn_direction == "180":
            if self.current_direction == "right":
                self.current_direction = "left"
            elif self.current_direction == "down":
                self.current_direction = "up"
            elif self.current_direction == "left":
                self.current_direction = "right"
            elif self.current_direction == "up":
                self.current_direction = "down"
        else:
            raise Exception("Unrecognised turning direction")
