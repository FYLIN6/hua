from animation.imports import *


class AnimationMain:
    def __init__(self, dimension=(15, 15), seed=0):
        pygame.init()
        pygame.display.set_caption('Simple Visualisation')
        # general game settings
        self.SURF = pygame.display.set_mode(SCREENSIZE)
        self.fps = 60
        self.clock = pygame.time.Clock()
        # game time control
        self.global_time = 0
        self.global_time_status = False
        # initialise other classes
        # please make sure value of n_rows and n_cols are compatible with json file data
        self.GRID = Grid(self.SURF, WIDTH, HEIGHT, n_rows=30, n_cols=35, used_rows=dimension[1], used_cols=dimension[0], random_seed=seed)
        self.initialise_other_classes()

    def initialise_other_classes(self):
        """
        Initialise self-defined classes
        """
        self.GRID.initialise_grid()
        self.CELL_CTRL = CellControl(self.SURF, self.GRID)
        self.INFO_BOX = InfoBox(self.SURF, self.GRID)
        self.EVENT_CTRL = EventControl(self.SURF, self.CELL_CTRL, self.INFO_BOX)

    def listen_events(self):
        """
        Listen for keyboard inputs
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_q:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_SPACE:
                    self.spacebar_pressed()

    def increment_global_time(self, dt):
        """
        Increase global time by dt

        @param dt: Smallest unit of time
        """
        if not self.global_time_status: return
        self.global_time += dt
    
    def spacebar_pressed(self):
        """
        Method called if spacebar is pressed
        """
        if self.EVENT_CTRL.pause:
            self.INFO_BOX.add_text("Simulation started.")
        else:
            self.INFO_BOX.add_text("Simulation paused.")

        # stop rects from moving
        self.EVENT_CTRL.set_pause(not self.EVENT_CTRL.pause)
        self.global_time_status = not self.global_time_status

    def run(self):
        """
        Core method
        """

        while True:
            # time control 
            dt = self.clock.tick(self.fps)
            self.increment_global_time(dt)

            # listen for events
            self.listen_events()

            # draw base layout
            self.SURF.fill(GREY)
            self.GRID.initialise_grid()
            self.INFO_BOX.draw_timer_box()

            # obstacles and legend
            self.CELL_CTRL.draw_legend()

            # inbound area
            self.CELL_CTRL.draw_inbound_floor_plan()

            # event-related visualisations and movements
            self.EVENT_CTRL.update_rects(self.global_time, dt)
            self.EVENT_CTRL.draw_rects()

            # update screen
            pygame.display.update()
