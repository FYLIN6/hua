import datetime
from random import random
import pandas as pd
import numpy as np

from interface.deployment import Deployment
from interface.request import Request
from interface.route import Route
from standard.sandbox import Sandbox
import logging
from output.statistics_output_creator import StatisticsOutputCreator


class GridMoverSystemHandler(Sandbox):
    __count = 0

    def __init__(self, id=None, seed=0, vehicle_df=None, load_duration=4, unload_duration=3,
                 transportation_network=None, animation_output_creator=None):
        super().__init__()
        GridMoverSystemHandler.__count += 1
        self.__index = GridMoverSystemHandler.__count
        self.__id = id if id is not None else 'GridMoverSystemHandler#' + str(self.__index)
        self.__seed = seed
        self.__available_job_df = pd.DataFrame(columns=['Job', 'JobId', 'ArrivalTime'])
        self.__vehicle_df = vehicle_df
        self.__load_duration = load_duration
        self.__unload_duration = unload_duration
        self.__transportation_network = transportation_network
        self.__grid_df = self.__transportation_network.grid_df
        self.__animation_output_creator = animation_output_creator

        # Set up for statistics output
        self.__statistics_output_creator = self.add_child(
            StatisticsOutputCreator(penalty_time = self.__grid_df.shape[0] * 4))
        self.__total_job_count = 0
        self.__job_to_duration_dict = dict()
        self.__vehicle_to_duration_dict = dict()

    @property
    def animation_output_creator(self):
        return self.__animation_output_creator

    @property
    def available_job_df(self):
        """
        Record the information of job waiting to be assigned.

        Information are: 'Job', 'JobId', 'ArrivalTime'.
        """
        return self.__available_job_df

    @property
    def vehicle_df(self):
        """
        Record the dynamic properties of vehicles.

        Properties are: 'VehicleId', 'StartPosition', 'DynamicRoute', 'Reservation', 'ReservationPending',

        'RequestTime', 'PartialRouteCompleteTime', 'ReservationToRelease', JobList', 'Status'.
        """
        return self.__vehicle_df

    @property
    def load_duration(self):
        """Time duration for loading a load onto vehicle."""
        return self.__load_duration

    @load_duration.setter
    def load_duration(self, value):
        self.__load_duration = value

    @property
    def unload_duration(self):
        """Time duration for unloading a load from vehicle."""
        return self.__unload_duration

    @unload_duration.setter
    def unload_duration(self, value):
        self.__unload_duration = value

    @property
    def job_to_duration_dict(self):
        """
        {Job.id:
                {'Waiting for Pick Up Duration': float,
                'Cycle Time': float
                },
                ...
        }

        Waiting for Pick Up Duration is the duration job waiting for vehicle to pick up: start load time - job arrival time;
        Cycle Time records the duration the job stay in the system: end unload time - job arrival time.
        """
        return self.__job_to_duration_dict

    @property
    def vehicle_to_duration_dict(self):
        """
        Record travel to park duration of each vehicle.
        {vehicle_id:
            {Start to Pick: datetime,
            Travel to Pick: float,
            Start to Deliver: datetime,
            Travel to Deliver: float,
            Effective Travel to Deliver: float,
            Start to Park: datetime,
            Travel to Park: float,
            Loaded Pending Duration: float,
            Empty Pending Duration: float
            },
        ...
        }

        Start to Pick is the time point for vehicle start to pick job
        Travel to Pick is the time duration for vehicle travel to pick job : start load time - start to pick time
        Start to Deliver is the time point for vehicle start to deliver job: end load time
        Travel to Deliver is the time duration for vehicle travel to deliver job: start unload time - start to deliver time
        Effective Travel to Deliver is travel to deliver duration exclude delay due to traffic congestion
        Start to Park is the time point for vehicle start to park
        Travel to Park is the time duration for vehicle travel to park: park time - start to park time
        Loaded Pending Duration is the pending duration caused by traffic congestion while the vehicle is loaded
        Empty Pending Duration is the pending duration caused by traffic congestion while the vehicle is empty
        """
        return self.__vehicle_to_duration_dict

    def job_arrive(self, job):
        """
        Receive job and trigger attempt_to_deploy event.

        Add job object, job id and job arrival time to available_job_df.

        @param job: job object arrives in the system
        """
        logging.info('Gridmover System Handler - Job Arrive, job is {}'.format(job.id))
        self.__total_job_count += 1
        logging.info('job arrive, total job count is {}'.format(self.__total_job_count))

        # Add to available_job_df
        job.arrival_time = self.clock_time
        job_value = [job, job.id, job.arrival_time]
        row_number = self.__available_job_df.shape[0]
        self.__available_job_df.loc[row_number] = job_value

        self.attempt_to_deploy()

    def attempt_to_deploy(self):
        """
        Match available jobs and vehicles. Can be triggered by the arrival of new job or the parking of vehicle.

        If user algorithm returns None, then will use default algorithm to deploy jobs and vehicles.

        Check status of each vehicle:
            - If status is Idle, which can refer to the following 2 cases:
                    - the vehicle's job list is not empty, but its first job request failed
                    - the vehicle's job list is empty and is waiting for jobs to be assigned
              then will add job list to vehicle_df and trigger route event only when
              its first job has been changed or its job list is no longer empty;

            - If status is Park, which means the vehicle is moving to park position and its job list is empty,
              then will add job list to vehicle_df;

            - If status is Pick or Delivery, which means it is working on the first job in job list,
            then will keep current job and add newly assigned job list.
        """
        logging.info('Gridmover System Handler - Attempt To Deploy')
        # get deployment result
        deployment = Deployment(self.__available_job_df, self.__vehicle_df)
        vehicle_to_jobs_dict = deployment.user_algo()
        if vehicle_to_jobs_dict is None:
            vehicle_to_jobs_dict = deployment.default_algo_to_deploy()
        logging.info('Gridmover System Handler - Attempt To Deploy, deployment result is {}'.format(vehicle_to_jobs_dict))

        # check deploy result
        self.__check_deployment_result(vehicle_to_jobs_dict)

        # update vehicle_df
        for vehicle, jobs in vehicle_to_jobs_dict.items():
            status = self.__vehicle_df.loc[vehicle.id, 'Status']
            # idle status can refer to requesting for first partial route, or waiting for deployment
            if status == 'Idle':
                jobs_list = self.__vehicle_df.loc[vehicle.id, 'JobList']
                # vehicle is requesting for first partial route
                if jobs is not np.nan and jobs_list is not np.nan:
                    # current processing job is not changed after deployment
                    if jobs[0] is jobs_list[0]:
                        self.__vehicle_df.at[vehicle.id, 'JobList'] = jobs
                    # current processing job is changed after deployment, need to clear info for pending for square unit
                    else:
                        self.__vehicle_df.at[vehicle.id, ['DynamicRoute', 'ReservationPending', 'RequestTime', 'JobList']] =\
                            [np.nan, np.nan, np.nan, jobs]
                        self.route(vehicle)
                # vehicle is waiting for deployment
                elif jobs is not np.nan and jobs_list is np.nan:
                    self.__vehicle_df.at[vehicle.id, 'JobList'] = jobs
                    self.route(vehicle)
                # vehicle is requesting for first partial route, but all jobs have been re-deployed to other vehicle
                elif jobs is np.nan and jobs_list is not np.nan:
                    self.__vehicle_df.at[vehicle.id, ['DynamicRoute', 'ReservationPending', 'RequestTime', 'JobList']] = \
                        [np.nan, np.nan, np.nan, jobs]

            # vehicle is traveling to park, it has no job
            elif status == 'Park':
                self.__vehicle_df.at[vehicle.id, 'JobList'] = jobs

            # vehicle is traveling to pick or deliver, the first job should not be changed
            else:
                current_job = self.__vehicle_df.loc[vehicle.id, 'JobList'][0]
                if current_job != jobs[0]:
                    raise Exception('Moving job cannot be deployed to other vehicle.')
                self.__vehicle_df.at[vehicle.id, 'JobList'] = jobs

    def __check_deployment_result(self, vehicle_to_jobs_dict):
        """
        A sub- function of attempt_to_deploy to check whether a same job is allocated to different
        vehicles repeatedly.

        @param vehicle_to_jobs_dict: Deployment result. {Vehicle: List<Job>}
        """
        deployed_jobs_list = []
        # get all deployed jobs
        for jobs in vehicle_to_jobs_dict.values():
            if jobs is not np.nan:
                deployed_jobs_list += jobs

        deployed_jobs_set = set(deployed_jobs_list)
        # check whether a same job appears into job lists of different vehicles
        if len(deployed_jobs_set) != len(deployed_jobs_list):
            raise Exception('Job has been allocated repeatedly.')

    def route(self, vehicle):
        """
        Get vehicle position; Generate route for vehicle to travel; Change vehicle status.

        - If vehicle status is Idle
            If vehicle current position is picking position, start_loading event will be triggered
            and system will delete the picked job from available_job_df;
            If vehicle current position is not picking position, a route will be generated for vehicle
            to travel to picking position to load.

        - If vehicle status is Delivery
            A route will be generated for vehicle to travel to delivery position to unload.

        - If vehicle status is Park, which means there is no job for the vehicle
            If vehicle current position is park position, parking event will be triggered directly;
            If vehicle current position is not park position, a route will be generated for vehicle
            to travel to park position.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Route, vehicle is {}'.format(vehicle.id))
        start_square_unit = self.__vehicle_df.loc[vehicle.id, 'StartPosition']
        job_list = self.__vehicle_df.loc[vehicle.id, 'JobList']
        vehicle_status = self.__vehicle_df.loc[vehicle.id, 'Status']
        # when status is Idle, vehicle is going to pick
        if vehicle_status == 'Idle':
            # get start travel to pick time (for output purpose)
            if vehicle.id not in self.__vehicle_to_duration_dict:
                self.__vehicle_to_duration_dict[vehicle.id] = dict()
            self.__vehicle_to_duration_dict[vehicle.id]['Start to Pick'] = self.clock_time

            end_square_unit = job_list[0].picking_position
            # vehicle current position is the picking position
            if end_square_unit == start_square_unit:
                self.__vehicle_df.at[vehicle.id, 'Status'] = 'Pick'
                # Delete job from available_job_df if start load at current position.
                for i in list(self.__available_job_df.index):
                    if self.__available_job_df.loc[i, 'JobId'] == job_list[0].id:
                        self.__available_job_df.drop(index=i, inplace=True)
                        break
                self.start_loading(vehicle)
            # vehicle need to travel to picking position
            else:
                self.__get_route(vehicle, start_square_unit, end_square_unit)

        # when status is Delivery, vehicle is going to deliver
        elif vehicle_status == 'Delivery':
            end_square_unit = job_list[0].delivery_position
            self.__get_route(vehicle, start_square_unit, end_square_unit)
        # when status is Park, vehicle is going to park
        elif vehicle_status == 'Park':
            end_square_unit = vehicle.park_position
            # record start time of traveling to park (for output purpose)
            self.__vehicle_to_duration_dict[vehicle.id]['Start To Park'] = self.clock_time

            # vehicle current position is the park position
            if start_square_unit == end_square_unit:
                self.start_parking(vehicle)
            # vehicle need to travel to park position
            else:
                self.__get_route(vehicle, start_square_unit, end_square_unit)

    def __get_route(self, vehicle, start_square_unit, end_square_unit):
        """
        A sub function of route event.
        If user algorithm return none, then will use default algorithm to calculate route.

        Final route will ignore the first square unit, which is the current position of vehicle.
        Then the final route will be added to DynamicRoute in vehicle_df and to vehicle's property static_route.

        Trigger partial_route_first_request.

        If cannot find a route, raise an exception.
        If find an unreasonable route, raise an exception.

        @param vehicle: Vehicle in the system
        @param start_square_unit: Start point for the route
        @param end_square_unit: End point for the route
        """
        # get route
        route = Route(self.__transportation_network, vehicle, start_square_unit, end_square_unit)
        route_list = route.user_algo()
        if route_list is None:
            route_list = route.default_algo_to_generate_route()
        logging.info('route - vehicle is {}, route is {}'.format(vehicle.id, route_list))
        # check whether can find a route
        if route_list:
            # check route
            self.__check_route(route_list)
            # get route list without first start position
            route_list = route_list[1:]
            self.__vehicle_df.at[vehicle.id, 'DynamicRoute'] = route_list
            vehicle.static_route = route_list
            if self.__vehicle_df.loc[vehicle.id, 'Status'] == 'Delivery':
                self.__animation_output_creator.get_route(vehicle, self.clock_time, self.__vehicle_df)
            self.partial_route_first_request(vehicle)
        else:
            raise Exception('{} is traveling from {} to {}. No route is found.'.
                            format(vehicle.id, start_square_unit, end_square_unit))

    def __check_route(self, route_list):
        """
        Check if the route found is in sequential.
        """
        previous_square_unit = route_list[0]
        for square_unit in route_list[1:]:
            x_difference = abs(square_unit[0] - previous_square_unit[0])
            y_difference = abs(square_unit[1] - previous_square_unit[1])
            if [0, 1].sort() != [x_difference, y_difference].sort():
                raise Exception('Wrong route is found.')
            else:
                previous_square_unit = square_unit

    def partial_route_first_request(self, vehicle):
        """
        Request the first partial route of the vehicle.

        If user algorithm return none, then will use default algorithm to request partial route.

        Call check_request method to check whether the request is successful or not.
        If successfully requested, then will trigger attempt to start.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - First Request, vehicle is {}'.format(vehicle.id))
        # get partial route to travel
        square_unit_request = Request(vehicle, self.__vehicle_df, self.__grid_df)
        partial_route = square_unit_request.user_algo()
        if partial_route is None:
            partial_route = square_unit_request.default_algo_to_get_partial_route()
        # check partial route
        if not partial_route:
            raise Exception('No partial route is requested.')

        if self.__check_request(vehicle, partial_route):
            self.attempt_to_start_partial_route(vehicle)

    def __check_request(self, vehicle, partial_route):
        """
        Check if the request is successful.

        For each square unit in requested partial route, check whether it is occupied by other vehicle.
        - If any square unit in the partial route is occupied, the request is failed.
          Then will update ReservationPending and RequestTime.
        - If all square units are available, then will add this partial route to Reservation in vehicle_df,
          and the square unit will be occupied by this vehicle.

        @param vehicle: Vehicle in the system
        @param partial_route: Requested route, List<SquareUnitIndex>
        """
        self.__animation_output_creator.gridmover_reserve(vehicle, self.clock_time, partial_route)
        logging.info('Gridmover System Handler - check request, vehicle is {}'.format(vehicle.id))
        success_request = True
        # check if requested square unit is occupied by other vehicle
        for square_unit in partial_route:
            occupied_vehicle = self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] ==
                                                  square_unit, 'OccupiedVehicle'].tolist()[0]
            if occupied_vehicle is not np.nan:
                logging.info('attempt to request - request vehicle is {}, request square unit is {}, '
                                 'occupied vehicle is {}'.format(vehicle.id, square_unit, occupied_vehicle.id))
                success_request = False
                break

        if success_request:
            # update reservation route and occupied vehicle
            self.__vehicle_df.at[vehicle.id, 'Reservation'] = partial_route
            for square_unit in partial_route:
                self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] == square_unit, 'OccupiedVehicle'] = vehicle
        else:
            # update reservation pending and request time
            self.__vehicle_df.at[vehicle.id, 'ReservationPending'] = partial_route
            logging.info(
                'attempt to request - vehicle is {}, reservation pending is {}'.format(vehicle, partial_route))
            self.__vehicle_df.at[vehicle.id, 'RequestTime'] = self.clock_time
        return success_request

    def attempt_to_start_partial_route(self, vehicle):
        """
        Check if vehicle can start moving.

        When next partial route is reserved successfully, start_partial_route event will be triggered.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Attempt To Start, vehicle is {}'.format(vehicle.id))
        reservation = self.__vehicle_df.loc[vehicle.id, 'Reservation']

        if reservation is not np.nan:
            logging.info('Gridmover System Handler - reservation is {}'.format(reservation))
            self.start_partial_route(vehicle)

    def start_partial_route(self, vehicle):
        """
        If vehicle status is Idle, then will change it to Pick and will delete its current job from available_job_df.

        This event will also add current partial route to ReservationToRelease and delete partial route from
        Reservation in vehicle_df.

        When vehicle start move and before it finishes this partial route, this event will schedule request_partial_route event.
        When vehicle finish current partial route, then will schedule release_partial_route event.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Start, vehicle is {}'.format(vehicle.id))
        vehicle_status = self.__vehicle_df.loc[vehicle.id, 'Status']
        job_list = self.__vehicle_df.loc[vehicle.id, 'JobList']
        reservation = self.__vehicle_df.loc[vehicle.id, 'Reservation']
        dynamic_route = self.__vehicle_df.loc[vehicle.id, 'DynamicRoute']
        remaining_route = list(set(dynamic_route) - set(reservation))

        if vehicle_status == 'Idle':
            self.__vehicle_df.at[vehicle.id, 'Status'] = 'Pick'
            self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] == vehicle.park_position, 'OccupiedVehicle'] = np.nan
            # delete job from available_job_df
            for i in list(self.__available_job_df.index):
                if self.__available_job_df.loc[i, 'JobId'] == job_list[0].id:
                    self.__available_job_df.drop(index=i, inplace=True)
                    break

        self.__vehicle_df.at[vehicle.id, 'ReservationToRelease'] = reservation
        self.__vehicle_df.at[vehicle.id, 'Reservation'] = np.nan
        self.__animation_output_creator.gridmover_movement(vehicle, self.clock_time, self.vehicle_df)

        # calculate schedule time for next events
        duration_to_finish_partial_route = len(reservation) * vehicle.pace
        time_to_request = duration_to_finish_partial_route * random()
        if len(remaining_route) > 0:
            self.schedule([self.partial_route_request, {'vehicle': vehicle}], datetime.timedelta(seconds=time_to_request))
        self.schedule([self.release_partial_route, {'vehicle': vehicle}], datetime.timedelta(seconds=duration_to_finish_partial_route))

    def partial_route_request(self, vehicle):
        """
        Request next partial route of the vehicle.

        If user algorithm return none, then will use default algorithm to request partial route.
        Call check_request method to check whether the request is successful or not.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Request, vehicle is {}'.format(vehicle.id))
        # get route
        square_unit_request = Request(vehicle, self.__vehicle_df, self.__grid_df)
        partial_route = square_unit_request.user_algo()
        if partial_route is None:
            partial_route = square_unit_request.default_algo_to_get_partial_route()
            logging.info('Gridmover System Handler - Request, partial route is {}'.format(partial_route))
        # check partial route
        if not partial_route:
            raise Exception('No partial route is requested.')

        self.__check_request(vehicle, partial_route)

    def release_partial_route(self, vehicle):
        """
        1. Release current partial route.
        Firstly, delete ReservationToRelease from vehicle_df;
        Then cut reservation to release from DynamicRoute;
        Square unit to release will be first (n-1) square unit of reservation to release + vehicle current start position, then for
        square units in square unit to release, will remove OccupiedVehicle and add 1 to VehicleVia.

        2. Check whether has pending vehicle for the partial route.
        If there is content in ReservationPending column of vehicle_df,
        then will trigger allocate_partial_route_for_pending_vehicle event.

        3. Update vehicle start position.
        New start position will be the last square unit of reservation to release.

        4. Trigger complete_partial_route event.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Release, vehicle is {}'.format(vehicle.id))
        current_start_position = self.__vehicle_df.loc[vehicle.id, 'StartPosition']
        square_unit_to_release = self.__vehicle_df.loc[vehicle.id, 'ReservationToRelease']
        self.__vehicle_df.at[vehicle.id, 'ReservationToRelease'] = np.nan

        # delete completed route from dynamic route
        dynamic_route = self.__vehicle_df.loc[vehicle.id, 'DynamicRoute']
        if len(square_unit_to_release) == len(dynamic_route):
            self.__vehicle_df.at[vehicle.id, 'DynamicRoute'] = []
        else:
            self.__vehicle_df.at[vehicle.id, 'DynamicRoute'] = dynamic_route[
                                                                  len(square_unit_to_release) - len(dynamic_route):]
        logging.info('Gridmover System Handler - Release, dynamic route after release {}'.format(
            self.__vehicle_df.loc[vehicle.id, 'DynamicRoute']))

        # get list of square unit to be released
        new_start_position = square_unit_to_release.pop()
        square_unit_to_release.insert(0, current_start_position)

        # release square unit
        for square_unit in square_unit_to_release:
            vehicle_via = self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] == square_unit, 'VehicleVia']
            self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] == square_unit, 'VehicleVia'] = vehicle_via + 1
            self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] == square_unit, 'OccupiedVehicle'] = np.nan
        logging.info('Gridmover System Handler - Release, released route is {}'.format(square_unit_to_release))

        # check vehicle pending list
        for pending_square_units in self.__vehicle_df['ReservationPending'].tolist():
            if pending_square_units is not np.nan and set(pending_square_units).intersection(set(square_unit_to_release)):
                logging.info('release - reservation pending is {}'.format(pending_square_units))
                self.allocate_partial_route_for_pending_vehicle()
                break

        # update start position
        self.__vehicle_df.at[vehicle.id, 'StartPosition'] = new_start_position
        self.__animation_output_creator.gridmover_release_grids(vehicle, self.clock_time, square_unit_to_release,
                                                                self.__vehicle_df)
        self.complete_partial_route(vehicle)

    def complete_partial_route(self, vehicle):
        """
        Complete current partial route.

        If there is still remaining dynamic route, trigger attempt_to_start_partial_route event.
        Else, if job list is empty, then will trigger parking event; if the job list is not empty, then will check the
        position of vehicle.
            - If the position is at current job's picking location, then will trigger start_loading event;
            - If the position is at current job's delivery location, then will trigger start_unloading event.
        Update PartialRouteCompleteTime in vehicle_df.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Complete, vehicle is {}'.format(vehicle.id))

        dynamic_route = self.__vehicle_df.loc[vehicle.id, 'DynamicRoute']
        job_list = self.__vehicle_df.loc[vehicle.id, 'JobList']
        start_position = self.__vehicle_df.loc[vehicle.id, 'StartPosition']
        status = self.__vehicle_df.loc[vehicle.id, 'Status']
        # update partial route complete time
        self.__vehicle_df.at[vehicle.id, 'PartialRouteCompleteTime'] = self.clock_time

        logging.info('Gridmover System Handler - Complete, dynamic route is {}'.format(dynamic_route))

        if len(dynamic_route) > 0:
            self.attempt_to_start_partial_route(vehicle)
        else:
            if status == 'Park':
                self.start_parking(vehicle)
            else:
                if start_position == job_list[0].picking_position:
                    self.start_loading(vehicle)
                elif start_position == job_list[0].delivery_position:
                    self.start_unloading(vehicle)

    def allocate_partial_route_for_pending_vehicle(self):
        """
        Allocate released square units to pending vehicles.

        Get vehicle from vehicle_df that ReservationPending is not nan and sort them according to RequestTime.
        For loop these vehicle, to check whether its pending square units is all available now.
        If all pending square units are available, then will add to selected vehicle list.

        For those selected vehicles, call update_data_after_allocation method to update data.
        Then for those selected vehicles whose ReservationToRelease is nan will be pushed to
        attempt_to_start_partial_route event.
        """
        logging.info('Gridmover System Handler - Allocate for Pending')
        pending_vehicle_df = self.__vehicle_df[self.__vehicle_df['ReservationPending'].notnull()]
        pending_vehicle_df = pending_vehicle_df.sort_values(by='RequestTime', ascending=False)
        selected_vehicle_list = []

        # select suitable vehicle
        for pending_vehicle in pending_vehicle_df['Vehicle'].tolist():
            success_allocation = True
            pending_square_unit = \
                self.__vehicle_df.loc[self.__vehicle_df['Vehicle'] == pending_vehicle, 'ReservationPending'].tolist()[0]
            # check if pending square unit is occupied by other vehicle
            for square_unit in pending_square_unit:
                occupied_vehicle = self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] == square_unit, 'OccupiedVehicle'].tolist()[0]
                if occupied_vehicle is not np.nan:
                    success_allocation = False
                    break
            if success_allocation:
                self.__update_data_after_allocation(pending_vehicle)
                selected_vehicle_list.append(pending_vehicle)

        for selected_vehicle in selected_vehicle_list:
            # to assure the previous partial route has been finished before starting new partial route
            if self.__vehicle_df.loc[selected_vehicle.id, 'ReservationToRelease'] is np.nan:
                # get pending duration for vehicle
                status = self.__vehicle_df.loc[selected_vehicle.id, 'Status']
                job_list = self.__vehicle_df.loc[selected_vehicle.id, 'JobList']
                complete_time = self.__vehicle_df.loc[selected_vehicle.id, 'PartialRouteCompleteTime']
                request_time = self.__vehicle_df.loc[selected_vehicle.id, 'RequestTime']
                self.__vehicle_df.at[selected_vehicle.id, 'RequestTime'] = np.nan
                if job_list is not np.nan:
                    # for loaded vehicle
                    if status == 'Delivery':
                        if 'Loaded Pending Duration' not in self.__vehicle_to_duration_dict[selected_vehicle.id]:
                            self.__vehicle_to_duration_dict[selected_vehicle.id]['Loaded Pending Duration'] = 0
                        if complete_time is not np.nan:
                            self.__vehicle_to_duration_dict[selected_vehicle.id]['Loaded Pending Duration'] += \
                                (self.clock_time - complete_time).total_seconds()
                        else:
                            self.__vehicle_to_duration_dict[selected_vehicle.id]['Loaded Pending Duration'] += \
                                (self.clock_time - request_time).total_seconds()
                    # for empty vehicle
                    else:
                        if selected_vehicle.id not in self.__vehicle_to_duration_dict:
                            self.__vehicle_to_duration_dict[selected_vehicle.id] = dict()
                        if 'Empty Pending Duration' not in self.__vehicle_to_duration_dict[selected_vehicle.id]:
                            self.__vehicle_to_duration_dict[selected_vehicle.id]['Empty Pending Duration'] = 0
                        if complete_time is not np.nan:
                            self.__vehicle_to_duration_dict[selected_vehicle.id]['Empty Pending Duration'] += \
                                (self.clock_time - complete_time).total_seconds()
                        else:
                            self.__vehicle_to_duration_dict[selected_vehicle.id]['Empty Pending Duration'] += \
                                (self.clock_time - request_time).total_seconds()

                self.attempt_to_start_partial_route(selected_vehicle)

    def __update_data_after_allocation(self, selected_vehicle):
        """
        A sub function of allocate_for_pending, to update vehicle_df, grid_df for the selected vehicle after allocation.

        Move ReservationPending to Reservation;
        Add selected vehicle to occupied vehicle.

        @param selected_vehicle: Selected vehicle after allocation
        """
        logging.info('Update Data After Allocation - selected vehicle is {}'.format(selected_vehicle.id))
        # modify vehicle_df
        reservation_pending = self.__vehicle_df.loc[selected_vehicle.id, 'ReservationPending']
        self.__vehicle_df.at[selected_vehicle.id, 'Reservation'] = reservation_pending
        self.__vehicle_df.at[selected_vehicle.id, 'ReservationPending'] = np.nan

        # modify grid_df
        for square_unit in reservation_pending:
            row_index = self.__grid_df[self.__grid_df['SquareUnitIndex'] == square_unit].index
            self.__grid_df.at[row_index[0], 'OccupiedVehicle'] = selected_vehicle

    def start_loading(self, vehicle):
        """
        Start loading a load onto vehicle.
        Clear PartialRouteCompleteTime in vehicle_df and schedule end_loading event after load duration.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Start Load'.format(vehicle.id))
        self.__animation_output_creator.gridmover_load(vehicle, self.clock_time, self.__vehicle_df)

        # calculate duration for job waiting to be picked up (for output purpose)
        current_job = self.__vehicle_df.loc[vehicle.id, 'JobList'][0]
        if current_job.id not in self.__job_to_duration_dict:
            self.__job_to_duration_dict[current_job.id] = dict()
        self.__job_to_duration_dict[current_job.id]['Waiting for Pick Up Duration'] = \
            (self.clock_time - current_job.arrival_time).total_seconds()
        self.schedule([self.end_loading, {'vehicle': vehicle}], datetime.timedelta(seconds=self.__load_duration))

        # calculate duration for vehicle travel to pick (for output purpose)
        if 'Travel to Pick' not in self.__vehicle_to_duration_dict[vehicle.id]:
            self.__vehicle_to_duration_dict[vehicle.id]['Travel to Pick'] = 0
        self.__vehicle_to_duration_dict[vehicle.id]['Travel to Pick'] += \
            (self.clock_time - self.__vehicle_to_duration_dict[vehicle.id]['Start to Pick']).total_seconds()

        # delete compete time
        self.__vehicle_df.at[vehicle.id, 'PartialRouteCompleteTime'] = np.nan

    def end_loading(self, vehicle):
        """
        Finish loading a load onto vehicle.
        Change vehicle status to Delivery and schedule route event.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - End Load, vehicle is {}'.format(vehicle.id))
        self.__vehicle_df.at[vehicle.id, 'Status'] = 'Delivery'

        # get star to deliver time (for output purpose)
        self.__vehicle_to_duration_dict[vehicle.id]['Start to Deliver'] = self.clock_time

        self.route(vehicle)

    def start_unloading(self, vehicle):
        """
        Start unloading a load from vehicle.
        Clear PartialRouteCompleteTime in vehicle_df and schedule end_unloading event after unload duration.

        @param vehicle: Vehicle in the system
        """
        self.__animation_output_creator.gridmover_unload(vehicle, self.clock_time, self.__vehicle_df)
        self.__animation_output_creator.release_route(vehicle, self.clock_time, self.__vehicle_df)
        logging.info('Gridmover System Handler - Start Unload, vehicle is {}'.format(vehicle.id))

        # calculate travel to deliver duration (for output purpose)
        if 'Travel to Deliver' not in self.__vehicle_to_duration_dict[vehicle.id]:
            self.__vehicle_to_duration_dict[vehicle.id]['Travel to Deliver'] = 0
        self.__vehicle_to_duration_dict[vehicle.id]['Travel to Deliver'] += \
            (self.clock_time - self.__vehicle_to_duration_dict[vehicle.id]['Start to Deliver']).total_seconds()

        # delete compete time
        self.__vehicle_df.at[vehicle.id, 'PartialRouteCompleteTime'] = np.nan
        self.schedule([self.end_unloading, {'vehicle': vehicle}], datetime.timedelta(seconds=self.__unload_duration))

    def end_unloading(self, vehicle):
        """
        Finish unloading a load from vehicle.
        1. Delete current job from job list, and check whether the job list is empty.
           - If job list is empty, then change status to Park.
           - If job list is not empty, then change status to Idle.

        2. Trigger route event for next task, either to park or to next job picking location.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - End Unload, vehicle is {}'.format(vehicle.id))
        job_list = self.__vehicle_df.loc[vehicle.id, 'JobList']
        current_job = job_list[0]

        # calculate job cycle time (for output purpose)
        if current_job.id not in self.__job_to_duration_dict:
            self.__job_to_duration_dict[current_job.id] = dict()
        self.__job_to_duration_dict[current_job.id]['Cycle Time'] = \
            (self.clock_time - current_job.arrival_time).total_seconds()

        # calculate effective travel to deliver duration (for output purpose)
        if 'Effective Travel to Deliver' not in self.__vehicle_to_duration_dict[vehicle.id]:
            self.__vehicle_to_duration_dict[vehicle.id]['Effective Travel to Deliver'] = 0
        self.__vehicle_to_duration_dict[vehicle.id]['Effective Travel to Deliver'] += len(vehicle.static_route) * vehicle.pace

        # delete current job
        job_list.pop(0)
        if len(job_list) > 0:
            self.__vehicle_df.at[vehicle.id, 'JobList'] = job_list
            self.__vehicle_df.at[vehicle.id, 'Status'] = 'Idle'
        else:
            self.__vehicle_df.at[vehicle.id, 'JobList'] = np.nan
            self.__vehicle_df.at[vehicle.id, 'Status'] = 'Park'
        self.route(vehicle)


    def start_parking(self, vehicle):
        """
        Occupy park position and change vehicle’s status to Idle.
        Clear PartialRouteCompleteTime in vehicle_df and trigger attempt_to_deploy event.

        @param vehicle: Vehicle in the system
        """
        logging.info('Gridmover System Handler - Park, vehicle is {}'.format(vehicle.id))
        vehicle_start_position = self.__vehicle_df.loc[vehicle.id, 'StartPosition']
        if vehicle_start_position == vehicle.park_position:
            self.__grid_df.loc[self.__grid_df['SquareUnitIndex'] == vehicle.park_position, 'OccupiedVehicle'] = vehicle
        self.__vehicle_df.at[vehicle.id, 'Status'] = 'Idle'

        # get park duration (for output purpose)
        if 'Travel to Park' not in self.__vehicle_to_duration_dict[vehicle.id]:
            self.__vehicle_to_duration_dict[vehicle.id]['Travel to Park'] = 0
        self.__vehicle_to_duration_dict[vehicle.id]['Travel to Park'] +=\
            (self.clock_time - self.__vehicle_to_duration_dict[vehicle.id]['Start To Park']).total_seconds()

        # delete compete time
        self.__vehicle_df.at[vehicle.id, 'PartialRouteCompleteTime'] = np.nan

        self.__animation_output_creator.gridmover_park(vehicle, self.clock_time, self.__vehicle_df)

        self.attempt_to_deploy()

    def end(self):
        """
        Observe statistics output.
        """
        logging.info('Gridmover System Handler - End event')
        self.__statistics_output_creator.observe_statistics_output(total_job_count=self.__total_job_count,
                                                                   job_to_duration_dict=self.__job_to_duration_dict,
                                                                   vehicle_to_duration_dict=self.__vehicle_to_duration_dict)
        vehicle_list = self.__vehicle_df['Vehicle'].tolist()
        for vehicle in vehicle_list:
            self.__animation_output_creator.gridmover_end(vehicle=vehicle)



