import pygame

from animation.utils import *

class Grid():
    def __init__(self, SURF, WIDTH, HEIGHT, n_rows=30, n_cols=35, used_rows=15, used_cols=15, random_seed=0):
        self.SURF = SURF
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.used_rows = used_rows
        self.used_cols = used_cols
        self.random_seed = random_seed


    def initialise_grid(self):
        """
        Initialise grid by calling the following methods
        """
        self.draw_boxes()
        self.draw_grid()
        self.write_grid_size()
        self.write_random_seed()
        self.draw_coordinates()

    def draw_grid(self):
        """
        Draw horizontal and vertical lines to form the grid
        """
        n_cols = self.n_cols
        n_rows = self.n_rows

        start_x, start_y = self.left_col_dims[0]
        self.cell_width = self.left_col_dims[1][0]/n_cols
        self.cell_height = self.left_col_dims[1][1]/n_rows

        self.y_indices = []
        self.x_indices = []

        # vertical lines
        for x in range(n_cols):
            pygame.draw.line(
                self.SURF,
                BLACK,
                (start_x + self.cell_width * x, start_y),
                (start_x + self.cell_width * x, self.left_col_dims[1][1] + start_y),
                1
            )
            self.x_indices.append(start_x + self.cell_width * x)

        # horizontal lines
        for x in range(n_rows):
            pygame.draw.line(
                self.SURF,
                BLACK,
                (start_x, start_y + self.cell_height * x),
                (self.left_col_dims[1][0] + start_x, start_y + self.cell_height * x),
                1
            )
            self.y_indices.append(start_y + self.cell_height * x)
        
    def draw_boxes(self):
        """
        Draw two boxes:
            left box: grid
            right box: info box
        """
        top_spacing = 50
        line_thickness = 3
        left_col = (int(3*self.WIDTH/5), int(6*self.HEIGHT/8))
        right_col = (self.WIDTH - 20*3 - left_col[0], left_col[1])

        # grid box
        pygame.draw.rect(
            self.SURF,
            DimGREY,
            (20, top_spacing, left_col[0], left_col[1]),
            0
        )

        # available area of grid box
        pygame.draw.rect(
            self.SURF,
            GREY,
            (20, top_spacing, left_col[0]*self.used_cols/self.n_cols, left_col[1]*self.used_rows/self.n_rows),
            0
        )

        # frame of grid box
        pygame.draw.rect(
            self.SURF,
            BLACK, 
            (20, top_spacing, left_col[0], left_col[1]), 
            line_thickness
        )

        # info box
        pygame.draw.rect(
            self.SURF, 
            BLACK, 
            (left_col[0] + 2*20, top_spacing, right_col[0], right_col[1]), 
            line_thickness
        )

        self.left_col_dims = [(20, top_spacing), left_col]
        self.right_col_dims = [(left_col[0] + 2*20, top_spacing), right_col]

    def write_grid_size(self):
        font = pygame.font.Font(get_font_path("Semibold"), 16)    
        grid_size_text = font.render("Grid Size: {} x {}".format(self.used_rows, self.used_cols), False, BLACK)
        self.SURF.blit(grid_size_text, (20, 5))

    def write_random_seed(self):
        font = pygame.font.Font(get_font_path("Semibold"), 16)
        grid_size_text = font.render("Random Seed: {}".format(self.random_seed), False, BLACK)
        self.SURF.blit(grid_size_text, (int(3*self.WIDTH/5)+40, 25))

    def draw_coordinates(self):
        font = pygame.font.Font(get_font_path("Semibold"), 12)
        for x in range(self.used_cols):
            grid_size_text = font.render("{}".format(x), False, BLACK)
            if x < 10:
                self.SURF.blit(grid_size_text, (self.x_indices[x] + 6, 33))
            else:
                self.SURF.blit(grid_size_text, (self.x_indices[x] + 2, 33))

        for y in range(self.used_rows):
            grid_size_text = font.render("{}".format(y), False, BLACK)
            if y < 10:
                self.SURF.blit(grid_size_text, (10, self.y_indices[y]))
            else:
                self.SURF.blit(grid_size_text, (5, self.y_indices[y]))
