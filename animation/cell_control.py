import pygame
from animation.utils import *

class CellControl():
    def __init__(self, SURF, GRID):
        self.SURF = SURF
        self.x_indices = GRID.x_indices
        self.y_indices = GRID.y_indices
        self.cell_width = GRID.cell_width
        self.cell_height = GRID.cell_height
        self.initialise_inbound()
        
    def initialise_inbound(self):
        """
        Initialise area plan coordinates specified in InputFiles/area.json
        """
        try:
            area_data = load_area_file()[0]
            self.park_coors = area_data["park_position"]
            self.obstacle_coors = area_data["obstacle"]
            self.load_coors = area_data["load"]

        except:
            return

    def draw_inbound_floor_plan(self):
        """
        Draw rects for obstacle coordinates specified in InputFiles/obstacle.json
        """
        try:
            self.fill_cells_by_list(self.park_coors, color=CYAN, margin=3, correction=1)
            self.fill_cells_by_list(self.obstacle_coors, color=DARK_PURPLE, margin=3, correction=1)
        except:
            return

    def draw_load(self, margin=4, correction=6):
        for idx, each in enumerate(self.load_coors):
            x, y = each[0], each[1]
            x1, y1 = tuple([i + margin for i in self.get_single_cell_drawing_coors(x, y)])
            image = pygame.image.load("Images/load.png")
            image = pygame.transform.scale(
                image,
                (int(self.cell_width)-correction, int(self.cell_height)-correction)
            )
            self.SURF.blit(image, [x1, y1])

    def add_load(self, new_load_coors):
        self.load_coors.append(new_load_coors)

    def remove_load(self, remove_load_coors):
        if remove_load_coors not in self.load_coors:
            self.load_coors.append(remove_load_coors)
        self.load_coors.remove(remove_load_coors)

    def draw_legend(self, margin=5, correction=1.5):
        """
        Draw legend for grid

        @param margin: Spacing between rect and all 4 sides; if zero, rect will fill entire cell
        @param correction: Needed to account for floating point error (prettier rects)
        """
        font = pygame.font.Font(get_font_path("Bold"), 15)
        x_indices = [20.0, 80.0, 175.0, 310.0, 405.0, 480.0]
        y_pos = 473.53
        height = 26
        width = 24

        y = y_pos + height + margin
        x_end = x_indices[0] + margin
        x_obstacle = x_indices[1] + margin
        x_park = x_indices[2] + margin
        x_reserved = x_indices[3] + margin
        x_route = x_indices[4] + margin
        x_delivery_position = x_indices[5] + margin
        x2, y2 = tuple([i - (margin + correction) for i in (width, height)])

        # end cell
        pygame.draw.rect(self.SURF, ORANGE, (x_end, y, x2, y2))
        start_cell_label = font.render("end", False, BLACK)
        self.SURF.blit(start_cell_label, (x_end+width, y))

        # obstacle cell
        pygame.draw.rect(self.SURF, DARK_PURPLE, (x_obstacle, y, x2, y2))
        start_cell_label = font.render("obstacle", False, BLACK)
        self.SURF.blit(start_cell_label, (x_obstacle + width, y))

        # park_position cell
        pygame.draw.rect(self.SURF, CYAN, (x_park, y, x2, y2))
        start_cell_label = font.render("park position", False, BLACK)
        self.SURF.blit(start_cell_label, (x_park + width, y))

        # reserved cell
        pygame.draw.rect(self.SURF, YELLOW, (x_reserved, y, x2, y2))
        start_cell_label = font.render("reserved", False, BLACK)
        self.SURF.blit(start_cell_label, (x_reserved + width, y))

        # route cell
        pygame.draw.rect(self.SURF, SEAGREEN, (x_route, y, x2, y2))
        start_cell_label = font.render("route", False, BLACK)
        self.SURF.blit(start_cell_label, (x_route + width, y))

        # delivery position cell
        pygame.draw.rect(self.SURF, RED, (x_delivery_position, y, x2, y2))
        start_cell_label = font.render("delivery position", False, BLACK)
        self.SURF.blit(start_cell_label, (x_delivery_position + width, y))

    def fill_single_cell(self, x, y, color=YELLOW, margin=0, correction=1.5):
        """
        Draw a rect at the grid cell specified by the given (x,y) coordinates

        @param x: x coordinate
        @param y: y coordinate
        @param color: Color for the rect drawn
        @param margin: Spacing between rect and all 4 sides; if zero, rect will fill entire cell
        @param correction: Needed to account for floating point error (prettier rects)
        """
        x1, y1 = tuple([i + margin for i in self.get_single_cell_drawing_coors(x, y)])
        x2, y2 = tuple([i - (margin + correction) for i in (self.cell_width, self.cell_height)])

        pygame.draw.rect(self.SURF, color, (x1, y1, x2, y2))

    def fill_cells_by_list(self, coors_list, color=YELLOW, margin=0, correction=1.5):
        """
        Draw rects at the grid cells specified by the list of coordinates

        @param coors_list: Contains lists of coordinates
        @param color: Color for the rect drawn
        @param margin: Spacing between rect and all 4 sides; if zero, rect will fill entire cell
        """
        for each in coors_list:
            x, y = each[0], each[1]
            self.fill_single_cell(x, y, color=color, margin=margin, correction=correction)

    def get_single_cell_drawing_coors(self, x, y):
        """
        Get the actual draw positions given (x, y) coordinates

        @param x: x coordinate
        @param y: y coordinate
        """
        return self.x_indices[x], self.y_indices[y]

