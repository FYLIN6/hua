import logging
import random
from datetime import timedelta
import numpy as np
from job_generator.duration_statistics_config import DurationStatisticsConfig
from load.job import Job
from job_generator.alias import Alias
from standard.action import Action
from standard.sandbox import Sandbox


class JobsDistributionGenerator(Sandbox):
    __count = 0

    def __init__(self, end_time, grid_df, gridmover_system_handler,
                 jobs_creation_dict, seed=0, id=None):
        super().__init__()
        self.__three_seed_list = []
        random.seed(seed)
        for x in range(0, 3):
            self.__three_seed_list.append(random.randint(0, 100))
        JobsDistributionGenerator.__count += 1
        self.__index = JobsDistributionGenerator.__count
        self.__id = id if id is not None else 'JobsGeneratorDistribution#' + str(self.__index)
        self.__end_time = end_time
        self.__gridmover_system_handler = gridmover_system_handler
        self.__jobs_creation_dict = jobs_creation_dict
        # Use for alias
        self.__picking_accept = None
        self.__picking_alias = None
        self.__delivery_accept = None
        self.__delivery_alias = None
        self.__square_unit_list = None
        self.__accept_range = None
        self.__on_generate = Action(Job).add(self.__gridmover_system_handler.job_arrive)

        self.get_square_unit_list(grid_df)

        self.__duration_statistic_config = DurationStatisticsConfig(self.__jobs_creation_dict['Lambda'], self.__three_seed_list[0])
        self.__n = int(self.__jobs_creation_dict['Lambda']*4)  # Approximate number of jobs*10
        self.__random_position_index_seed_list = []
        random.seed(self.__three_seed_list[1])
        for x in range(0, self.__n):
            self.__random_position_index_seed_list.append(random.randint(0, self.__n + 1))

        self.__random_accept_rate_seed_list = []
        random.seed(self.__three_seed_list[2])
        for x in range(0, self.__n):
            self.__random_accept_rate_seed_list.append(random.randint(0, self.__n + 1))
        self.__index_seed = 0

        self.get_generation_rate()

    @property
    def id(self):
        return self.__id

    def get_square_unit_list(self, grid_df):
        grid_df_for_generation = grid_df.loc[grid_df['IsObstacle'] == False]
        grid_df_for_generation = grid_df_for_generation[grid_df_for_generation['OccupiedVehicle'].isin([np.nan])]
        self.__square_unit_list = grid_df_for_generation['SquareUnitIndex'].tolist()

    def generate(self):
        if self.clock_time < self.__end_time:
            distribution_lambda = self.__jobs_creation_dict['Lambda']
            arrival_rate = self.get_arrival_rate(distribution_lambda)
            self.schedule([self.run_generate], timedelta(hours=arrival_rate))
            logging.info("Jobs Generator Distribution - arrival rate is {}".format(arrival_rate))

    def run_generate(self):
        picking_position_index = self.get_position_index(self.__picking_accept, self.__picking_alias)
        delivery_position_index = self.get_position_index(self.__delivery_accept, self.__delivery_alias)
        if picking_position_index != delivery_position_index:
            picking_position = self.__square_unit_list[picking_position_index]
            delivery_position = self.__square_unit_list[delivery_position_index]
            logging.info("Jobs Generator Distribution - picking position is {} and delivery position is {}".format(picking_position, delivery_position))
            job = Job(delivery_position=delivery_position, picking_position=picking_position)
            self.__on_generate.invoke(job)
        else:
            self.run_generate()
            return
        self.generate()

    def get_position_index(self, accept, alias):
        random.seed(self.__random_position_index_seed_list[self.__index_seed])
        random_position_index = random.choice(self.__accept_range)
        random.seed(self.__random_accept_rate_seed_list[self.__index_seed])
        random_accept_rate = random.random()
        if self.__index_seed < self.__n - 1:
            self.__index_seed = self.__index_seed + 1
        if random_accept_rate < accept[random_position_index]:
            position_index = random_position_index
        else:
            position_index = alias[random_position_index]
        return position_index

    def get_generation_rate(self):
        picking_default_rate = self.__jobs_creation_dict['PickingDefaultRate']
        delivery_default_rate = self.__jobs_creation_dict['DeliveryDefaultRate']
        picking_rate_list = [picking_default_rate] * len(self.__square_unit_list)
        delivery_rate_list = [delivery_default_rate] * len(self.__square_unit_list)

        for square_unit in self.__jobs_creation_dict['SquareUnits'].keys():
            index = self.__square_unit_list.index(square_unit)
            picking_rate = self.__jobs_creation_dict['SquareUnits'][square_unit]['PickingRate']
            delivery_rate = self.__jobs_creation_dict['SquareUnits'][square_unit]['DeliveryRate']
            if picking_rate is not None:
                picking_rate_list[index] = picking_rate
            if delivery_rate is not None:
                delivery_rate_list[index] = delivery_rate

        self.__picking_accept, self.__picking_alias = self.get_accept_and_alias(picking_rate_list)
        self.__delivery_accept, self.__delivery_alias = self.get_accept_and_alias(delivery_rate_list)
        self.__accept_range = list(range(len(self.__picking_accept)))

    def get_accept_and_alias(self, rate_list):
        rate_array = np.array(rate_list)
        uniform_rate_array = rate_array / sum(rate_array)
        alias = Alias()
        accept, alias = alias.create_alias_table(uniform_rate_array)
        return accept, alias

    def get_arrival_rate(self, distribution_lambda):
        arrival_rate = self.__duration_statistic_config.generate_exponential(distribution_lambda=distribution_lambda)
        return arrival_rate


