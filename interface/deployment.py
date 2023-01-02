import datetime
import sys
import numpy as np

class Deployment:
    def __init__(self, available_job_df, vehicle_df):
        self.__available_job_df = available_job_df
        self.__vehicle_df = vehicle_df
        # Adjust according to the specific situation of the system
        self.__vehicle_maximum_capacity = 3  # The maximum number of jobs that a vehicle can be assigned at the same time.
        self.__job_maximum_distance = 5  # the maximum distance between jobs and vehicles that are allowed to be assigned.

    def default_algo_to_deploy(self):
        """
        Call __get_vehicle_to_jobs_dict to get new assigned vehicles and jobs;

        All jobs that can be assigned are stored in __available_job_df, including jobs that have never been assigned and
        jobs that have been assigned but have not yet started.
        Divide __available_job_df into long_wait_job_df and remaining_job_df according to the waiting time.
        Algorithm __get_vehicle_to_jobs_dict will use long_wait_job_df and remaining_job_df respectively, but the last parameter is different.
        The last parameter limits the maximum distance between jobs and vehicles that are allowed to be assigned.
        For jobs in long_wait_job_df, this maximum distance is set to the system maximum distance.
        For jobs in remaining_job_df, this maximum distance is set to __job_maximum_distance.

        @return all_vehicle_to_jobs_dict (Contains all vehicles and their jobList information
        <Dictionary<Vehicle: List<Job, Job, ...>, Vehicle: List<Job, Job, ...>, ...>>)
        """
        job_maximum_waiting_time = 300  # The maximum waiting time. Adjust according to the specific situation of the system

        # Distinguish whether the job has been waiting for a long time according to the arrival time of the job
        long_wait_job_df = self.__available_job_df.loc[self.__available_job_df['ArrivalTime'] < self.__get_minimum_arrival_time(job_maximum_waiting_time)]
        job_id_list = long_wait_job_df['JobId'].tolist()
        remaining_job_df = self.__available_job_df[~self.__available_job_df['JobId'].isin(job_id_list)]

        vehicle_to_jobs_dict = {}
        vehicle_to_jobs_dict.update(self.__get_vehicle_to_jobs_dict(long_wait_job_df, self.__vehicle_df, sys.maxsize))
        vehicle_to_jobs_dict.update(self.__get_vehicle_to_jobs_dict(remaining_job_df, self.__vehicle_df, self.__job_maximum_distance))

        # Copy a previous allocation from vehicle_df
        all_vehicle_to_jobs_dict = {}
        for row_vehicle in self.__vehicle_df.itertuples():
            if getattr(row_vehicle, "JobList") is not np.nan:
                all_vehicle_to_jobs_dict[getattr(row_vehicle, "Vehicle")] = getattr(row_vehicle, "JobList").copy()
            else:
                all_vehicle_to_jobs_dict[getattr(row_vehicle, "Vehicle")] = np.nan

        # Compare all_vehicle_to_jobs_dict with vehicle_to_jobs_dict and add and delete on all_vehicle_to_jobs_dict
        for vehicle, jobs in vehicle_to_jobs_dict.items():
            for job in jobs:
                for vehicle_key in all_vehicle_to_jobs_dict.keys():
                    if isinstance(all_vehicle_to_jobs_dict[vehicle_key], list) and job in all_vehicle_to_jobs_dict[vehicle_key]:
                        all_vehicle_to_jobs_dict[vehicle_key].remove(job)
                        if len(all_vehicle_to_jobs_dict[vehicle_key]) == 0:
                            all_vehicle_to_jobs_dict[vehicle_key] = np.nan
                        break
            if isinstance(all_vehicle_to_jobs_dict[vehicle], list):
                all_vehicle_to_jobs_dict[vehicle] += jobs
            else:
                all_vehicle_to_jobs_dict[vehicle] = jobs

        return all_vehicle_to_jobs_dict

    def __get_vehicle_to_jobs_dict(self, job_df, vehicle_df, distance):
        """
        Get new assigned vehicles and jobs.

        For each job, loop to calculate the distance with each vehicle and find the case with the smallest distance which must be less than the param distance

        Calculate the distance between a job and a vehicle as follows:
        Check whether status is park, if so will pass this vehicle.
        If the vehicle's job list is empty
            then Calculate the distance between the picking position of the job and the start position of the vehicle
        else
            if the job is in the job list of the vehicle
                then if the job is the first one in the job list
                        then Calculate the distance between the picking position of the job and the start position of the vehicle
                     else
                        Calculate the distance between the picking position of the job and the delivery position of its previous job
            else
                if the number of jobs in the job list of the vehicle is less than the __vehicle_maximum_capacity
                    then if the vehicle is already in result vehicle_to_jobs_dict
                            then if the number of jobs in the job list of the vehicle plus the number of jobs of the vehicle in vehicle_to_jobs_dict is less than the __vehicle_maximum_capacity
                                    then Calculate the distance between the picking position of the job and the delivery position of the last job of the vehicle in vehicle_to_jobs_dict
                         else Calculate the distance between the picking position of the job and the delivery position of the last job in the job list of the vehicle

        job_vehicle_distance is used to store the calculated distance of the job to new vehicles
        job_vehicle_current_distance is used to store the calculated distance of the job in the previously assigned vehicle, if applicable
        If the job was previously assigned and the newly calculated distance job_vehicle_distance is less than the previous distance job_vehicle_current_distance, reassign it.

        @param job_df: stores jobs that can be assigned
        @param vehicle_df: stores all vehicles
        @param distance: the maximum distance between jobs and vehicles that are allowed to be assigned
        @return vehicle_to_jobs_dict (Contains vehicles and their new jobs information <Dictionary<Vehicle: List<Job, Job, ...>, Vehicle: List<Job, Job, ...>, ...>>)
                (For example: {vehicle1: [job1, job2], vehicle2: [job3]})
        """
        vehicle_to_jobs_dict = {}
        for row_job in job_df.itertuples():
            job_vehicle_distance = distance  # Used to limit the maximum distance between work and vehicle
            target_vehicle = None
            job_vehicle_current_distance = sys.maxsize  # It is used to store the calculated distance of the job in the previously assigned vehicle, if applicable
            for row_vehicle in vehicle_df.itertuples():
                current_staus = getattr(row_vehicle, "Status")
                if current_staus == 'Park':
                    continue
                current_job_list = getattr(row_vehicle, "JobList")
                current_vehicle = getattr(row_vehicle, "Vehicle")
                if not isinstance(current_job_list, list) and np.isnan(current_job_list):
                    temp_distance = self.__get_distance(getattr(row_job, "Job").picking_position,
                                                        getattr(row_vehicle, "StartPosition"))
                    if temp_distance < job_vehicle_distance:
                        job_vehicle_distance = temp_distance
                        target_vehicle = current_vehicle
                else:
                    if getattr(row_job, "Job") in current_job_list:
                        if getattr(row_job, "Job") == current_job_list[0]:
                            job_vehicle_current_distance = self.__get_distance(getattr(row_job, "Job").picking_position,
                                                        getattr(row_vehicle, "StartPosition"))
                        else:
                            job_vehicle_current_distance = self.__get_distance(getattr(row_job, "Job").picking_position,
                                                        current_job_list[current_job_list.index(getattr(row_job, "Job"))-1].delivery_position)
                    elif len(current_job_list) < self.__vehicle_maximum_capacity:
                        if current_vehicle in vehicle_to_jobs_dict.keys():
                            if len(vehicle_to_jobs_dict[current_vehicle]) + len(current_job_list) < self.__job_maximum_distance:
                                temp_distance = self.__get_distance(getattr(row_job, "Job").picking_position, vehicle_to_jobs_dict[current_vehicle][-1].delivery_position)
                                if temp_distance < job_vehicle_distance:
                                    job_vehicle_distance = temp_distance
                                    target_vehicle = current_vehicle
                        else:
                            temp_distance = self.__get_distance(getattr(row_job, "Job").picking_position, current_job_list[-1].delivery_position)
                            if temp_distance < job_vehicle_distance:
                                job_vehicle_distance = temp_distance
                                target_vehicle = current_vehicle

            if target_vehicle is not None:
                if job_vehicle_current_distance < sys.maxsize:
                    if job_vehicle_distance < job_vehicle_current_distance:
                        if target_vehicle in vehicle_to_jobs_dict:
                            vehicle_to_jobs_dict[target_vehicle].append(getattr(row_job, "Job"))
                        else:
                            vehicle_to_jobs_dict[target_vehicle] = [getattr(row_job, "Job")]
                else:
                    if target_vehicle in vehicle_to_jobs_dict:
                        vehicle_to_jobs_dict[target_vehicle].append(getattr(row_job, "Job"))
                    else:
                        vehicle_to_jobs_dict[target_vehicle] = [getattr(row_job, "Job")]

        return vehicle_to_jobs_dict

    def __get_minimum_arrival_time(self, job_maximum_waiting_time):
        minimum_arrival_time = datetime.datetime.now() - datetime.timedelta(seconds=job_maximum_waiting_time)
        return minimum_arrival_time

    def __get_distance(self, start_square_unit_index, end_square_unit_index):
        return abs(end_square_unit_index[0] - start_square_unit_index[0]) + abs(end_square_unit_index[1] - start_square_unit_index[1])

    def user_algo(self):
        """
        User defines a new algorithm to get new assigned vehicles and jobs

        @return vehicle_to_jobs_dict
                (Contains all vehicles and their jobList information <Dictionary<Vehicle: List<Job, Job, ...>, Vehicle: List<Job, Job, ...>, ...>>)
                (For example: {vehicle1: [job1, job2], vehicle2: [job3]})
                (running result: {<transportation.entities.gridmover.GridMover object at 0x000001B6B51737C0>: [<load.job.Job object at
                0x000001B6B4FAFBE0>, <load.job.Job object at 0x000001B6B51736A0>],
                <transportation.entities.gridmover.GridMover object at 0x000001B6B5173E80>: [<load.job.Job object at 0x000001B6B5173460>]})
        """
        vehicle_to_jobs_dict = None
        return vehicle_to_jobs_dict
