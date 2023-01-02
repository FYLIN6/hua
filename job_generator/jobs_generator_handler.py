from datetime import datetime, timedelta
from job_generator.jobs_distribution_generator import JobsDistributionGenerator
from standard.sandbox import Sandbox


class JobsGeneratorHandler(Sandbox):
    __count = 0

    def __init__(self, gridmover_system_handler, grid_df, jobs_creation_dict,
                 runtime_duration=1, id=None, seed=0):
        super().__init__()
        JobsGeneratorHandler.__count += 1
        self.__index = JobsGeneratorHandler.__count
        self.__id = id if id is not None else 'JobsGeneratorHandler#' + str(self.__index)
        self.__seed = seed
        self.__gridmover_system_handler = gridmover_system_handler
        self.__grid_df = grid_df
        self.__start_time = datetime.min
        self.__runtime_duration = runtime_duration
        self.__jobs_distribution_generator = None
        self.__jobs_creation_dict = jobs_creation_dict

    @property
    def id(self):
        """Account for different generator system handler with different id."""
        return self.__id

    @property
    def runtime_duration(self):
        """Hour duration for generators to generate orders."""
        return self.__runtime_duration

    @runtime_duration.setter
    def runtime_duration(self, value):
        self.__runtime_duration = value

    @property
    def grid_df(self):
        return self.__grid_df

    @property
    def jobs_creation_dict(self):
        return self.__jobs_creation_dict

    @property
    def jobs_distribution_generator(self):
        return self.__jobs_distribution_generator

    def create_generator(self):
        self.__jobs_distribution_generator = self.add_child(
            JobsDistributionGenerator(end_time=self.__start_time + timedelta(hours=self.__runtime_duration),
                                      grid_df=self.__grid_df,
                                      gridmover_system_handler=self.__gridmover_system_handler,
                                      jobs_creation_dict=self.__jobs_creation_dict,
                                      seed=self.__seed
                                      ))
        self.__jobs_distribution_generator.run_generate()




