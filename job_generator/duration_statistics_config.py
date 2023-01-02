import random
import numpy as np


class DurationStatisticsConfig:
    def __init__(self, n, seed):
        self.__n = int(n*2)  # Approximate number of jobs*2
        self.__seed_list = []
        random.seed(seed)
        for x in range(0, self.__n):
            self.__seed_list.append(random.randint(0, self.__n+1))
        self.__index_seed = 0

    def generate_exponential(self, distribution_lambda):
        random.seed(self.__seed_list[self.__index_seed])
        if self.__index_seed < self.__n - 1:
            self.__index_seed = self.__index_seed + 1
        if distribution_lambda <= 0:
            raise Exception("Negative mean not applicable")
        else:
            return random.expovariate(distribution_lambda)

    def generate_normal(self, mean, standard_deviation):
        if mean < 0:
            raise Exception("Negative mean not applicable")
        if standard_deviation < 0:
            raise Exception("Negative standard deviation not applicable for normal distribution")

        if mean == 0:
            return 0
        if standard_deviation == 0:
            return mean
        return random.normalvariate(mu=mean, sigma=standard_deviation)

    def generate_poisson(self, mean):
        if mean < 0:
            raise Exception("Negative mean not applicable")

        if np.random.poisson(mean) != 0:
            return np.random.poisson(mean)
        else:
            return 0.000000001

    def generate_geometric(self, mean):
        if mean <= 0:
            raise Exception("Negative mean not applicable")
        else:
            return np.random.geometric(1/mean)

    def generate_uniform(self, lowerbound, upperbound):
        if lowerbound < 0 or upperbound < 0:
            raise Exception("Negative lowerbound or upperbound is not applicable")
        return np.random.uniform(lowerbound, upperbound)
