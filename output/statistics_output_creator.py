import logging

from config_pack.file_config import FileConfig
import os
import json

from standard.sandbox import Sandbox


class StatisticsOutputCreator(Sandbox):
    def __init__(self, penalty_time):
        super().__init__()
        self.__penalty_time = penalty_time
        self.__file_config = FileConfig()
        self.__statistic_output_dict = {}
        self.__statistic_output_dir = self.__file_config.get_output_folder()
        if not os.path.exists(self.__statistic_output_dir):
            os.makedirs(self.__statistic_output_dir)

    @property
    def penalty_time(self):
        """Penalty time for unfinished job."""
        return self.__penalty_time

    @penalty_time.setter
    def penalty_time(self, value):
        self.__penalty_time = value

    def observe_statistics_output(self, total_job_count, job_to_duration_dict, vehicle_to_duration_dict):
        """
        {
            "Total Number of Job Generated": 31,
            "Finished Job": {
                "Quantity": 31,
                "Effective Duration With Load [s]": 325,
                "Effective Ratio": 0.3993,
                "Average Job Cycle Time [s]": 26.2562
            },
            "Unfinished Job": {
                "Quantity": 0,
                "Penalty Time Per Job [s]": 900
            },
            "Delay Due To Waiting for Pick Up (Job) [s]": 271.94,
            "Delay Due To Traffic Congestion (Loaded Vehicle) [s]": 0,
            "Delay Due To Traffic Congestion (Empty Vehicle) [s]": 2.33,
            "Duration Without Load [s]": 604.56,
            "Adjusted Average Job Cycle Time [s]": 26.2562
        }

        Effective Duration With Load: total time for vehicles traveling with load, excluding pending time for grid;
        Effective Ratio: ratio of effective duration with load to total job cycle time;
            - total job cycle time: sum of each job's unload time minus its arrival time
        Delay Due To Waiting for Pick Up: duration for job waiting for vehicle to pick up;
        Delay Due To Traffic Congestion (Loaded Vehicle): the pending duration caused by traffic congestion while the vehicle is loaded;
        Delay Due To Traffic Congestion (Empty Vehicle): the pending duration caused by traffic congestion while the vehicle is empty;
        Adjusted Average Job Cycle Time: total job cycle time for finished job combine with
                                        total penalty time for unfinished job, divided by total job generated

        @param total_job_count: total quantity of job generated
        @param job_to_duration_dict: record different duration for each job
        @param vehicle_to_duration_dict: record different duration for each vehicle
        """
        logging.info('Statistics Output Creator - job to duration dict is {}'.format(job_to_duration_dict))
        logging.info('Statistics Output Creator - vehicle to  travel duration dict is {}'.format(vehicle_to_duration_dict))
        finished_job_quantity = len(job_to_duration_dict.keys())
        unfinished_job_quantity = total_job_count - finished_job_quantity

        total_job_cycle_time = 0
        job_waiting_for_pick_up_duration = 0
        travel_to_pick_duration = 0
        travel_to_deliver_duration = 0
        travel_to_park_duration = 0
        effective_travel_duration = 0
        loaded_vehicle_pending_duration = 0
        empty_vehicle_pending_duration = 0
        for _, job_duration in job_to_duration_dict.items():
            if 'Cycle Time' in job_duration:
                total_job_cycle_time += job_duration['Cycle Time']
            if 'Waiting for Pick Up Duration' in job_duration:
                job_waiting_for_pick_up_duration += job_duration['Waiting for Pick Up Duration']
        for _, vehicle_duration in vehicle_to_duration_dict.items():
            if 'Travel to Pick' in vehicle_duration:
                travel_to_pick_duration += vehicle_duration['Travel to Pick']
            if 'Travel to Deliver' in vehicle_duration:
                travel_to_deliver_duration += vehicle_duration['Travel to Deliver']
            if 'Travel to Park' in vehicle_duration:
                travel_to_park_duration += vehicle_duration['Travel to Park']
            if 'Effective Travel to Deliver' in vehicle_duration:
                effective_travel_duration += vehicle_duration['Effective Travel to Deliver']
            if 'Loaded Pending Duration' in vehicle_duration:
                loaded_vehicle_pending_duration += vehicle_duration['Loaded Pending Duration']
            if 'Empty Pending Duration' in vehicle_duration:
                empty_vehicle_pending_duration += vehicle_duration['Empty Pending Duration']

        self.__statistic_output_dict['Total Number of Job Generated'] = total_job_count
        self.__statistic_output_dict['Finished Job'] = {}
        self.__statistic_output_dict['Finished Job']['Quantity'] = finished_job_quantity
        self.__statistic_output_dict['Finished Job']['Effective Duration With Load [s]'] = round(effective_travel_duration, 2)
        if total_job_cycle_time > 0:
            self.__statistic_output_dict['Finished Job']['Effective Ratio'] = \
                round(self.__statistic_output_dict['Finished Job']['Effective Duration With Load [s]']/total_job_cycle_time, 4)
        if finished_job_quantity > 0:
            self.__statistic_output_dict['Finished Job']['Average Job Cycle Time [s]'] = \
                round((total_job_cycle_time / finished_job_quantity), 4)

        self.__statistic_output_dict['Unfinished Job'] = {}
        self.__statistic_output_dict['Unfinished Job']['Quantity'] = unfinished_job_quantity
        self.__statistic_output_dict['Unfinished Job']['Penalty Time Per Job [s]'] = self.__penalty_time
        self.__statistic_output_dict['Delay Due To Waiting for Pick Up (Job) [s]'] = \
            round(job_waiting_for_pick_up_duration, 2)
        self.__statistic_output_dict['Delay Due To Traffic Congestion (Loaded Vehicle) [s]'] = \
            round(loaded_vehicle_pending_duration, 2)
        self.__statistic_output_dict['Delay Due To Traffic Congestion (Empty Vehicle) [s]'] = \
            round(empty_vehicle_pending_duration, 2)
        self.__statistic_output_dict['Duration Without Load [s]'] = \
            round(travel_to_pick_duration + travel_to_park_duration, 2)
        self.__statistic_output_dict['Adjusted Average Job Cycle Time [s]'] = \
            round((total_job_cycle_time + (unfinished_job_quantity * self.__penalty_time)) / total_job_count, 4)

        statistic_output_file_name = os.path.join(self.__statistic_output_dir,"statistics_output.json")
        with open(statistic_output_file_name, "w", encoding='utf-8') as f:
            json.dump(self.__statistic_output_dict, f, ensure_ascii=False, default=str, indent=4)
