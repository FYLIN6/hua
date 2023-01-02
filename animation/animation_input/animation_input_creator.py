from config_pack.file_config import FileConfig
import os
import json
import glob

from standard.sandbox import Sandbox
import logging
from datetime import timedelta


class AnimationInputCreator(Sandbox):
    def __init__(self, vehicle_df):
        super().__init__()
        self.__file_config = FileConfig()
        self.__vehicle_df = vehicle_df
        self.__animation_output_dir = self.__file_config.get_animation_input_path()
        if not os.path.exists(self.__animation_output_dir):
            os.makedirs(self.__animation_output_dir)

    def create_warehouse(self):
        # delete old json files to start afresh
        self.__delete_jsons()

        json_object = {
            'park_position': [],
            'obstacle': [],
            'load': [],
            }
        with open(self.__animation_output_dir + "area.json", "w") as area:
            json.dump(json_object, area)

    def __delete_jsons(self):
        files = glob.glob(self.__animation_output_dir + '/*')
        for f in files:
            os.remove(f)

    def create_warehouse_area(self, vehicle_df, grid_df):
        # create warehouse component
        warehouse_area_file = open(self.__animation_output_dir + "area.json", "r")
        json_object = json.load(warehouse_area_file)
        warehouse_area_file.close()

        park_position_list = vehicle_df['StartPosition'].tolist()
        json_object['park_position'] = park_position_list
        obstacle_df = grid_df.loc[grid_df['IsObstacle'] == True]
        obstacle_list = obstacle_df['SquareUnitIndex'].tolist()
        json_object['obstacle'] = obstacle_list

        warehouse_area_file = open(self.__animation_output_dir + "area.json", "w")
        json.dump(json_object, warehouse_area_file)
        warehouse_area_file.close()

    def create_gridmover(self, vehicle, clock_time, initial_direction):
        vehicle.check_movement_direction.current_direction = initial_direction
        vehicle_id = vehicle.id
        json_object = {
                        'gridmover': [{'type': 'vehicle',
                                       'length': 1,
                                       'width': 1,
                                       'occupied_width': 1,
                                       'occupied_length': 1,
                                       'initial_direction': initial_direction}],
                        'start_coors': vehicle.park_position,
                        'end_coors': vehicle.park_position,
                        'start_time': str(clock_time),
                        'end_time': str(clock_time),
                        'events': [{'event_type': 'start',
                                    'time': str(clock_time),
                                    'current_coors': vehicle.park_position,
                                    'coors': vehicle.park_position}]
                        }
        with open(self.__animation_output_dir + vehicle_id + ".json", "w", encoding='utf-8') as gridmover:
            json.dump(json_object, gridmover, ensure_ascii=False, default=str, indent=4)

    def gridmover_reserve(self, vehicle, clock_time, partial_route):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        last_event_before_reserve = json_object['events'][-1]
        if last_event_before_reserve['event_type'][0:4] == 'move':
            reserve_event_time = str(clock_time).split('.')[0]
            if reserve_event_time > last_event_before_reserve['time']:
                reserve_event_dict = {'event_type': 'reserve',
                                      'time': reserve_event_time,
                                      'current_coors': json_object['events'][-1]['coors'],
                                      'coors': partial_route}
                json_object['events'].append(reserve_event_dict)
            else:
                event_index = -1
                while(reserve_event_time <= json_object['events'][event_index-1]['time']) and json_object['events'][event_index-1]['event_type'] != 'reserve' and json_object['events'][event_index-1]['event_type'] != 'release':
                    json_object['events'][event_index] = json_object['events'][event_index-1]
                    event_index = event_index - 1
                temp_current_coors = json_object['events'][event_index-1]['coors']
                if json_object['events'][event_index-1]['event_type'][0:4] != 'move' and json_object['events'][event_index-1]['event_type'][0:4] != 'turn':
                    temp_current_coors = json_object['events'][event_index-1]['current_coors']
                reserve_event_dict = {'event_type': 'reserve',
                                      'time': reserve_event_time,
                                      'current_coors': temp_current_coors,
                                      'coors': partial_route}
                json_object['events'][event_index] = reserve_event_dict
                json_object['events'].append(last_event_before_reserve)
        else:
            reserve_event_dict = {'event_type': 'reserve',
                                  'time': str(clock_time).split('.')[0],
                                  'current_coors': last_event_before_reserve['current_coors'],
                                  'coors': partial_route}
            json_object['events'].append(reserve_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def gridmover_movement(self, vehicle, clock_time, vehicle_df):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        route = []
        route.append(vehicle_df.loc[vehicle.id, 'StartPosition'])
        reservation_to_release = vehicle_df.loc[vehicle.id, 'ReservationToRelease']
        for square_unit in reservation_to_release:
            route.append(square_unit)

        current_direction = vehicle.check_movement_direction.current_direction
        for i in range(1, len(route)):
            logging.critical(route[i])
            current_direction = vehicle.check_movement_direction.judge_direction(current_direction, route[i - 1], route[i])
            turn_result = vehicle.check_movement_direction.turn_result
            move_result = vehicle.check_movement_direction.move_result
            turning_clock_time = str(clock_time + timedelta(seconds=vehicle.pace * (i-1))).split('.')[0]
            movement_clock_time = str(clock_time + timedelta(seconds=vehicle.pace * (i-1))).split('.')[0]
            if turn_result:
                if i == 1:
                    if json_object['events'][-1]['event_type'] == 'reserve' or json_object['events'][-1]['event_type'] == 'release':
                        turning_clock_time = json_object['events'][-1]['time']
                turn_event_dict = {'event_type': turn_result['event_type'],
                                   'time': turning_clock_time,
                                   'coors': turn_result['coors']}
                json_object['events'].append(turn_event_dict)
            if move_result:
                move_event_dict = {'event_type': move_result['event_type'],
                                   'time': movement_clock_time,
                                   'coors': move_result['coors']}
                json_object['events'].append(move_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def gridmover_release_grids(self, vehicle, clock_time, square_unit_to_relase, vehicle_df):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        release_event_dict = {'event_type': 'release',
                              'time': str(clock_time).split('.')[0],
                              'current_coors': vehicle_df.loc[vehicle.id,'StartPosition'],
                              'coors': square_unit_to_relase}
        json_object['events'].append(release_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def gridmover_load(self, vehicle, clock_time, vehicle_df):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        load_event_dict = {'event_type': 'load',
                           'time': str(clock_time).split('.')[0],
                           'current_coors': vehicle_df.loc[vehicle.id, 'StartPosition'],
                           'coors': vehicle_df.loc[vehicle.id, 'StartPosition']}

        json_object['events'].append(load_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def gridmover_unload(self, vehicle, clock_time, vehicle_df):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        unload_event_dict = {'event_type': 'unload',
                             'time': str(clock_time).split('.')[0],
                             'current_coors': vehicle_df.loc[vehicle.id, 'StartPosition'],
                             'coors': vehicle_df.loc[vehicle.id, 'StartPosition']}
        json_object['events'].append(unload_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def gridmover_park(self, vehicle, clock_time, vehicle_df):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        park_event_dict = {'event_type': 'wait',
                           'time': str(clock_time).split('.')[0],
                           'current_coors': vehicle_df.loc[vehicle.id, 'StartPosition'],
                           'coors': vehicle_df.loc[vehicle.id, 'StartPosition']}
        json_object['events'].append(park_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def gridmover_end(self, vehicle):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        json_object['end_coors'] = json_object['events'][-1]['current_coors']
        json_object['end_time'] = json_object['events'][-1]['time']
        end_event_dict = {'event_type': 'end',
                          'time': json_object['end_time'],
                          'current_coors': json_object['end_coors'],
                          'coors': json_object['end_coors']}
        json_object['events'].append(end_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def get_route(self, vehicle, clock_time, vehicle_df):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        delivery_route = vehicle.static_route
        get_route_event_dict = {'event_type': 'route',
                                'time': str(clock_time).split('.')[0],
                                'current_coors': vehicle_df.loc[vehicle.id, 'StartPosition'],
                                'coors': delivery_route}
        json_object['events'].append(get_route_event_dict)

        delivery_position = []
        delivery_position.append(delivery_route[-1])
        delivery_position_event_dict = {'event_type': 'delivery position',
                                        'time': str(clock_time).split('.')[0],
                                        'current_coors': vehicle_df.loc[vehicle.id, 'StartPosition'],
                                        'coors': delivery_position}
        json_object['events'].append(delivery_position_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()

    def release_route(self, vehicle, clock_time, vehicle_df):
        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "r")
        json_object = json.load(gridmover_file)
        gridmover_file.close()

        release_route_event_dict = {'event_type': 'release route',
                                    'time': str(clock_time).split('.')[0],
                                    'current_coors': vehicle_df.loc[vehicle.id, 'StartPosition'],
                                    'coors': vehicle.static_route}
        json_object['events'].append(release_route_event_dict)

        gridmover_file = open(self.__animation_output_dir + vehicle.id + ".json", "w")
        json.dump(json_object, gridmover_file)
        gridmover_file.close()