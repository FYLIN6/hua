import numpy as np


class Alias:
    def __init__(self):
        pass

    def create_alias_table(self, area_ratio):
        N = len(area_ratio)
        accept, alias = [0]*N, [0]*N
        small, large = [], []

        area_ratio_N = np.array(area_ratio)*N

        for i, prob in enumerate(area_ratio_N):
            if prob < 1.0:
                small.append(i)
            else:
                large.append(i)

        while small and large:
            small_idx, large_idx = small.pop(), large.pop()
            accept[small_idx] = area_ratio_N[small_idx]
            alias[small_idx] = large_idx
            area_ratio_N[large_idx] = area_ratio_N[large_idx] - (1 - area_ratio_N[small_idx])
            if area_ratio_N[large_idx] < 1.0:
                small.append(large_idx)
            else:
                large.append(large_idx)

        while large:
            large_idx = large.pop()
            accept[large_idx] = 1
        while small:
            small_idx = small.pop()
            accept[small_idx] = 1

        return accept, alias


