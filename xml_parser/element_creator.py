from transportation.resources.transportation_network import TransportationNetwork
import pandas as pd
from job_generator.jobs_generator_handler import JobsGeneratorHandler
from standard.sandbox import Sandbox
from handler.gridmover_system_handler import GridMoverSystemHandler
from transportation.entities.vehicle import Vehicle

from animation.animation_input.animation_input_creator import AnimationInputCreator

class ElementCreator(Sandbox):
    def __init__(self):
        super().__init__()
        self.__obstacles_list = []
        self.__transportation_network = None
        self.__grid_df = None
        self.__vehicle_df = pd.DataFrame(columns=['Vehicle', 'VehicleId', 'StartPosition', 'DynamicRoute',
                                                  'Reservation', 'ReservationPending', 'RequestTime',
                                                  'PartialRouteCompleteTime', 'ReservationToRelease',
                                                  'JobList', 'Status'])
        self.__jobs_creation_dict = {}
        self.__jobs_generator_handler = None
        self.__gridmover_system_handler = None
        self.__animation_output_creator = self.add_child(AnimationInputCreator(vehicle_df=self.vehicle_df))


    @property
    def vehicle_df(self):
        return self.__vehicle_df

    @vehicle_df.setter
    def vehicle_df(self, value):
        self.__vehicle_df = value

    @property
    def animation_output_creator(self):
        return self.__animation_output_creator

    @animation_output_creator.setter
    def animation_output_creator(self, value):
        self.__animation_output_creator = value

    @property
    def jobs_creation_dict(self):
        """
        {'Lambda': float,
        'PickingDefaultRate': float,
        'DeliveryDefaultRate': float,
        'SquareUnits':
            {SquareUnitIndex1:{'PickingRate': float, 'DeliveryRate': float},
            SquareUnitIndex2:{'PickingRate': float, 'DeliveryRate': float},
            ...
            }
        }
        """
        return self.__jobs_creation_dict

    @property
    def transportation_network(self):
        return self.__transportation_network

    @transportation_network.setter
    def transportation_network(self, value):
        self.__transportation_network = value

    @property
    def grid_df(self):
        return self.__grid_df

    @property
    def jobs_generator_handler(self):
        return self.__jobs_generator_handler

    @property
    def gridmover_system_handler(self):
        return self.__gridmover_system_handler

    def create(self, gridmover_system_dict, seed):
        self.__animation_output_creator.create_warehouse()
        self.create_vehicle_df(gridmover_system_dict)
        self.create_transportation_network(gridmover_system_dict)
        self.__grid_df = self.transportation_network.grid_df
        self.create_simulated_jobs_dict(gridmover_system_dict)
        self.__gridmover_system_handler = self.add_child(GridMoverSystemHandler(vehicle_df=self.__vehicle_df,
                                                                                transportation_network=self.__transportation_network,
                                                                                animation_output_creator=self.__animation_output_creator))

        self.__gridmover_system_handler.animation_output_creator.create_warehouse_area(self.__vehicle_df, self.__grid_df)
        self.__jobs_generator_handler = self.add_child(JobsGeneratorHandler(runtime_duration=1,
                                                                            grid_df=self.__grid_df,
                                                                            jobs_creation_dict=self.__jobs_creation_dict,
                                                                            gridmover_system_handler=self.__gridmover_system_handler,
                                                                            seed=seed))
        self.__jobs_generator_handler.create_generator()

    def create_vehicle_df(self, gridmover_system_dict):
        gridmover_resources_list = gridmover_system_dict['GridMoverSystem']['GridMoverResources'] if \
            'GridMoverResources' in gridmover_system_dict['GridMoverSystem'] else []
        if type(gridmover_resources_list) is dict:
            gridmover_resources_list = [gridmover_resources_list]
        if type(gridmover_resources_list) is not list:
            return

        for vehicles_dict in gridmover_resources_list:
            for vehicle_tag, vehicle in vehicles_dict.items():
                vehicle_type = vehicle_tag
                id = vehicle['Id'] if 'Id' in vehicle else None
                park_position = eval(vehicle['ParkPosition']) if 'ParkPosition' in vehicle else None
                vehicle_command = vehicle_type + '(' \
                                    + 'park_position=park_position,' \
                                    + 'id=id,'
                vehicle_command = vehicle_command[:-1] + ')'
                vehicle = eval(vehicle_command)
                self.__vehicle_df = self.__vehicle_df.append([{'Vehicle': vehicle,
                                                               'VehicleId': id,
                                                               'StartPosition': park_position,
                                                               'Status': 'Idle'}],
                                                             ignore_index=True)

                self.__animation_output_creator.create_gridmover(vehicle, self.clock_time, initial_direction='down')
        self.__vehicle_df.set_index(['VehicleId'], inplace=True)

    def create_transportation_network(self, gridmover_system_dict):
        transportation_network_dict = gridmover_system_dict['GridMoverSystem']['TransportationNetwork'] if \
            'TransportationNetwork' in gridmover_system_dict['GridMoverSystem'] else dict()
        obstacles_group_list = transportation_network_dict[
            'Obstacles'] if 'Obstacles' in transportation_network_dict else []
        if type(obstacles_group_list) is dict:
            obstacles_group_list = [obstacles_group_list]
        if type(obstacles_group_list) is not list:
            return
        obstacles_list = []
        for obstacles_dict in obstacles_group_list:
            for obstacles_tag, obstacle_point in obstacles_dict.items():
                obstacle = eval(obstacle_point)
                obstacles_list.append(obstacle)
        transportation_network_id = transportation_network_dict['Id'] if 'Id' in transportation_network_dict else None
        start_point = eval(
            transportation_network_dict['StartPoint']) if 'StartPoint' in transportation_network_dict else (0, 0)
        dimension = eval(transportation_network_dict['Dimension']) if 'Dimension' in transportation_network_dict else (
        10, 10)

        if len(transportation_network_dict.keys()) > 0:
            self.__transportation_network = TransportationNetwork(id=transportation_network_id,
                                                                  start_point=start_point,
                                                                  dimension=dimension,
                                                                  obstacle_list=obstacles_list,
                                                                  vehicle_df=self.__vehicle_df)
        else:
            self.__transportation_network = TransportationNetwork(id='DefaultTransportationNetwork',
                                                                  start_point=(0, 0),
                                                                  dimension=(10, 10),
                                                                  obstacle_list=[],
                                                                  vehicle_df=self.__vehicle_df)

    def create_simulated_jobs_dict(self, gridmover_system_dict):
        simulated_jobs_dict = gridmover_system_dict['GridMoverSystem']['SimulatedJobs'] if \
            'SimulatedJobs' in gridmover_system_dict['GridMoverSystem'] else {}
        self.__jobs_creation_dict['Lambda'] = float(simulated_jobs_dict['Lambda'])
        self.__jobs_creation_dict['PickingDefaultRate'] = float(simulated_jobs_dict['PickingDefaultRate'])
        self.__jobs_creation_dict['DeliveryDefaultRate'] = float(simulated_jobs_dict['DeliveryDefaultRate'])
        square_units_list = simulated_jobs_dict['SquareUnits']
        if type(square_units_list) is dict:
            square_units_list = [square_units_list]
        if type(square_units_list) is not list:
            return
        self.__jobs_creation_dict['SquareUnits'] = dict()
        for square_unit_dict in square_units_list:
            for square_unit_tag, square_unit in square_unit_dict.items():
                square_unit_index = eval(square_unit['SquareUnitIndex'])
                self.__jobs_creation_dict['SquareUnits'][square_unit_index] = dict()
                self.__jobs_creation_dict['SquareUnits'][square_unit_index]['PickingRate'] = float(square_unit['PickingRate']) \
                    if 'PickingRate' in square_unit else None
                self.__jobs_creation_dict['SquareUnits'][square_unit_index]['DeliveryRate'] = float(square_unit['DeliveryRate']) \
                    if 'DeliveryRate' in square_unit else None
        print('create jon info:', self.__jobs_creation_dict)


