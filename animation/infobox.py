import pygame
from animation.utils import *

class InfoBox():
    def __init__(self, SURF, GRID):
        # attributes for drawing
        self.SURF = SURF
        self.right_col_dims = GRID.right_col_dims
        self.x_indices = GRID.x_indices
        self.y_indices = GRID.y_indices
        self.cell_width = GRID.cell_width
        self.cell_height = GRID.cell_height
        self.x_left = self.right_col_dims[0][0]
        self.x_right = self.x_left + self.right_col_dims[1][0]
        # text
        self.texts = [("Press space bar to start.", BLACK)]
        self.timer_box_height = 41
        self.text_height = 20
        self.time_str = "0001-01-01 00:00:00"

    def draw_timer_box(self):
        """
        Draw the box around time display
        """
        font = pygame.font.Font(get_font_path("Bold"), 20)    
        timer_header = font.render("Time", False, BLACK)
        self.SURF.blit(timer_header, (self.x_left + 10, self.right_col_dims[0][1] + 5))

        pygame.draw.line(
            self.SURF,
            BLACK,
            (self.x_left, self.right_col_dims[0][1] + self.timer_box_height),
            (self.x_right, self.right_col_dims[0][1] + self.timer_box_height),
            3
        )

        self.show_time()
        self.update_texts()

    def update_texts(self):
        """
        Draw/update text information for display
        """
        font = pygame.font.Font(get_font_path("Regular"), 14)
        for i, item in enumerate(self.texts):
            txt = ">> " + item[0]
            string_display = font.render(txt, False, item[1])
            height = i * 25 + self.timer_box_height + self.right_col_dims[0][1]
            self.SURF.blit(string_display, (self.x_left + 5, height))
    
    def show_time(self):
        """
        Display time string
        """
        font = pygame.font.Font(get_font_path("Semibold"), 20)
        time_display = font.render(self.time_str, False, BLACK)
        self.SURF.blit(time_display, (self.x_left + 70, self.right_col_dims[0][1] + 5))

    def update_time(self, time_str):
        """
        Update time string

        @param time_str: Time string to be displayed
        """
        try:
            # self.time_str = datetime.utcfromtimestamp(float(time_str)).strftime("%Y-%m-%d %H:%M:%S")
            temp_time_str = str(datetime.fromtimestamp(float(time_str)).strftime("%Y-%m-%d %H:%M:%S"))
            self.time_str = '0001' + temp_time_str[4:]
        except:
            self.time_str = time_str
    
    def update_percentage(self, percentage=0):
        """
        Draw/update percentage completion

        @param percentage: Percentage completed
        """
        if percentage < 0 or percentage > 100: raise Exception("Percentage under/overflow.")
        percentage = str(percentage) if len(str(percentage)) <= 4 else str(percentage)[:4]
        font = pygame.font.Font(get_font_path("Semibold"), 20)
        percentage_display = font.render(percentage+"%", False, BLACK)
        self.SURF.blit(percentage_display, (self.x_left + 280, self.right_col_dims[0][1] + 5))

    def add_text(self, string, color=BLACK):
        """
        Add string to object for display

        @param string: String for display in the info box
        """
        self.texts.append((string, color))
        if len(self.texts) > 16: self.texts.pop(0)