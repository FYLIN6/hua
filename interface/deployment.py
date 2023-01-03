import datetime
import sys
import numpy as np

class Deployment:
    def __init__(self, available_job_df, vehicle_df):
        self.__available_job_df = available_job_df
        self.__vehicle_df = vehicle_df
        # Adjust according to the specific situation of the system
        self.__vehicle_maximum_capacity = 2  # The maximum number of jobs that a vehicle can be assigned at the same time.
        self.__job_maximum_distance = 20  # the maximum distance between jobs and vehicles that are allowed to be assigned.

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
        job_maximum_waiting_time = 1  # The maximum waiting time. Adjust according to the specific situation of the system

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
                            if len(vehicle_to_jobs_dict[current_vehicle]) + len(current_job_list) < self.__vehicle_maximum_capacity:
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
        job_maximum_waiting_time = 5  # The maximum waiting time. Adjust according to the specific situation of the system

        # Distinguish whether the job has been waiting for a long time according to the arrival time of the job
        long_wait_job_df = self.__available_job_df.loc[
            self.__available_job_df['ArrivalTime'] < self.__user__get_minimum_arrival_time(
                job_maximum_waiting_time)]  # loc取行消息，看是否超过时长，利用了__get_minimum_arrival_time来获取时间
        job_id_list = long_wait_job_df['JobId'].tolist()  # 把长时间等待的任务的id弄出成数组
        remaining_job_df = self.__available_job_df[
            ~self.__available_job_df['JobId'].isin(job_id_list)]  # id不在长时间等待任务列表的任务

        vehicle_to_jobs_dict = {}
        vehicle_to_jobs_dict.update(self.__user__get_vehicle_to_jobs_dict(long_wait_job_df, self.__vehicle_df,
                                                                          sys.maxsize))  # 最后一个元素是系统长度，即到达一定时间后开始从全局搜索，利用了__get_vehicle_to_jobs_dict获取词典
        vehicle_to_jobs_dict.update(self.__user__get_vehicle_to_jobs_dict(remaining_job_df, self.__vehicle_df,
                                                                          self.__job_maximum_distance))  # 加入时间不长的任务

        # Copy a previous allocation from vehicle_df
        all_vehicle_to_jobs_dict = {}
        for row_vehicle in self.__vehicle_df.itertuples():  # row_vehicle是变量名，itertuples()是行遍历
            if getattr(row_vehicle, "JobList") is not np.nan:  # JobList是属性
                all_vehicle_to_jobs_dict[getattr(row_vehicle, "Vehicle")] = getattr(row_vehicle,
                                                                                    "JobList").copy()  # 为什么这里是Vehicle不是VehicleID
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


    def __user__get_vehicle_to_jobs_dict(self, job_df, vehicle_df, distance):
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
        for row_job in job_df.itertuples():  # 一行行任务分开
            job_vehicle_distance = distance  # Used to limit the maximum distance between work and vehicle
            target_vehicle = None
            job_vehicle_current_distance = sys.maxsize  # It is used to store the calculated distance of the job in the previously assigned vehicle, if applicable
            for row_vehicle in vehicle_df.itertuples():
                current_staus = getattr(row_vehicle, "Status")
                if current_staus == 'Park':
                    continue
                current_job_list = getattr(row_vehicle, "JobList")  # current_job_list即当前Vehicle的工作列表
                current_vehicle = getattr(row_vehicle, "Vehicle")  # current_vehicle即当前Vehicle的ID
                if not isinstance(current_job_list, list) and np.isnan(
                        current_job_list):  # 判断current_job_list是否是list，是则返回True（然后取反）；判断current_job_list是否是空值，为空则返回True；此句即判断他的工作列表是否为空
                    temp_distance = self.__user__get_distance(getattr(row_job, "Job").picking_position, getattr(row_vehicle, "StartPosition"))
                    if temp_distance < job_vehicle_distance:  # 小于限制距离则加入为目标Vehicle
                        job_vehicle_distance = temp_distance
                        target_vehicle = current_vehicle
                else:  # 如果工作集不为空
                    if getattr(row_job,"Job") in current_job_list:  # 如果此任务已经在该Vehicle的工作列表中,getattr(row_job, "Job")是一个Object，则current_job_list是ObjectList
                        if getattr(row_job, "Job") == current_job_list[0]:  # 如果是第一个
                            job_vehicle_current_distance = self.__user__get_distance(
                                getattr(row_job, "Job").picking_position, getattr(row_vehicle, "StartPosition"))
                        else:  # 如果任务在该Vehicle的工作列表中并且不是第一个
                            '''
                            修改部分：
    
                            查询当前车辆的状态：
    
                            如果当前任务不是最后一个任务或者当前任务不是目标任务
                                如果是首次执行
                                    如果是Picking则
                                        计算车辆当前位置（dynamic_route[0])与picking_position的距离
                                        计算当前任务picking_position与deliver_position的距离
                                        任务++
                                    如果是Delivery则
                                        计算车辆当前位置（dynamic_route[0])与deliver_position的距离
                                        任务++
                                不是首次执行
                                    计算当前任务的picking_position与deliver_position的距离
                                    计算当前任务的deliver_position与下一个任务的picking_position的距离
                            计算倒数第一个任务deliver_position与新任务picking_position的距离
                            更新temp_distance
                            '''
                            job_vehicle_current_distance = self.__not_first_distance(current_job_list, current_vehicle, current_staus, row_job)
                            # job_vehicle_current_distance = self.__user__get_distance(getattr(row_job, "Job").picking_position, current_job_list[current_job_list.index(getattr(row_job, "Job")) - 1].delivery_position)
                    elif len(current_job_list) < self.__vehicle_maximum_capacity:  # 如果当前列表小于最大承受的任务数量，该任务不在工作列表中
                        if current_vehicle in vehicle_to_jobs_dict.keys():  # 当前的Vehicle已经在字典中，计算该任务与字典最后一个交付地点的距离（如果从生成开始算的话，不应该是这样，要加上前一个任务剩余的路程）
                            if len(vehicle_to_jobs_dict[current_vehicle]) + len(
                                    current_job_list) < self.__vehicle_maximum_capacity:  # 加上新分配的任务后仍小于最大任务数
                                '''
                                修改部分：
                                '''
                                temp_distance = self.__in_dit_distance(current_job_list, current_vehicle, current_staus, row_job, vehicle_to_jobs_dict)     # 计算并更新距离
                                if temp_distance < job_vehicle_distance:
                                    job_vehicle_distance = temp_distance
                                    target_vehicle = current_vehicle
                        else:  # 如果不在字典中则计算工作列表最后一个交付地点的距离
                            '''
                            修改部分：
                            '''
                            temp_distance = self.__not_dit_distance(current_job_list, current_vehicle, current_staus, row_job)

                            if temp_distance < job_vehicle_distance:
                                job_vehicle_distance = temp_distance
                                target_vehicle = current_vehicle
                            '''
                            if current_staus == 'Delivery':
                                temp_distance = self.__get_distance(getattr(row_job, "Job").picking_position, current_job_list[-1].delivery_position) + \
                                                self.__get_distance(current_job_list[-1].delivery_position,
                                                                    getattr(row_vehicle, "StartPosition"))
                                if temp_distance < job_vehicle_distance:
                                    job_vehicle_distance = temp_distance
                                    target_vehicle = current_vehicle
                            elif current_staus == 'Pick' or current_staus == 'Idle':
                                temp_distance = self.__get_distance(getattr(row_job, "Job").picking_position, current_job_list[-1].delivery_position)+ \
                                                self.__get_distance(current_job_list[-1].delivery_position, current_job_list[-1].picking_position)+\
                                                self.__get_distance(current_job_list[-1].picking_position,
                                                                    getattr(row_vehicle, "StartPosition"))
                                if temp_distance < job_vehicle_distance:
                                    job_vehicle_distance = temp_distance
                                    target_vehicle = current_vehicle
                            '''

            if target_vehicle is not None:
                if job_vehicle_current_distance < sys.maxsize:  # job_vehicle_current_distance 已经处于工作列表的情况，即先前分配的情况
                    if job_vehicle_distance < job_vehicle_current_distance:  # job_vehicle_distance 新分配车辆的距离
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


    def __user__get_minimum_arrival_time(self, job_maximum_waiting_time):  # 得到现在时间与最大等待时间的差
        minimum_arrival_time = datetime.datetime.now() - datetime.timedelta(seconds=job_maximum_waiting_time)
        return minimum_arrival_time


    def __user__get_distance(self, start_square_unit_index, end_square_unit_index):  # 得到两个格子之间的距离
        return abs(end_square_unit_index[0] - start_square_unit_index[0]) + abs(
            end_square_unit_index[1] - start_square_unit_index[1])


    def __not_first_distance(self, current_job_list, current_vehicle, current_staus, row_job):
        temp_job = 0
        temp_distance = 0
        while (current_job_list[temp_job] != current_job_list[-1]) and (
               str(current_job_list[temp_job]) != getattr(row_job, "Job")):
            if temp_job == 0:
                if current_staus == 'Pick' or current_staus == 'Idle':
                    if self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'] == []:
                        temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'StartPosition'], current_job_list[temp_job].picking_position)
                    else:
                        temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'][0], current_job_list[temp_job].picking_position)
                    temp_distance += self.__user__get_distance(current_job_list[temp_job].picking_position, current_job_list[temp_job].delivery_position)
                    temp_distance += self.__user__get_distance(current_job_list[temp_job].delivery_position, current_job_list[temp_job + 1].picking_position)
                if current_staus == 'Delivery':
                    if self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'] == []:
                        temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'StartPosition'], current_job_list[temp_job].delivery_position)
                    else:
                        temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'][0], current_job_list[temp_job].delivery_position)
                    temp_distance += self.__user__get_distance(current_job_list[temp_job].delivery_position, current_job_list[temp_job + 1].picking_position)
            else:
                temp_distance += self.__user__get_distance(current_job_list[temp_job].picking_position, current_job_list[temp_job].delivery_position)
                temp_distance += self.__user__get_distance(current_job_list[temp_job].delivery_position, current_job_list[temp_job + 1].picking_position)
            temp_job += 1
        return temp_distance


    def __in_dit_distance(self, current_job_list, current_vehicle, current_staus, row_job, vehicle_to_jobs_dict):
        temp_job = 0
        temp_distance = 0
        '''
        此段计算工作列表的距离
        '''
        while True:
            if temp_job == 0:
                if current_staus == 'Pick' or current_staus == 'Idle':
                    # if self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'] == []:
                    temp_distance = self.__user__get_distance(
                            self.__vehicle_df.loc[current_vehicle.id, 'StartPosition'],
                            current_job_list[temp_job].picking_position)
                    temp_distance += 7
                    '''
                    else:
                        temp_distance = self.__user__get_distance(
                            self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'][0],
                            current_job_list[temp_job].picking_position)
                    temp_distance += self.__user__get_distance(current_job_list[temp_job].picking_position,
                                                               current_job_list[temp_job].delivery_position)
                    '''
                if current_staus == 'Delivery':
                    # if self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'] == []:
                    temp_distance = self.__user__get_distance(
                            self.__vehicle_df.loc[current_vehicle.id, 'StartPosition'], current_job_list[temp_job].delivery_position)
                    temp_distance += 3
                    '''
                    else:
                        temp_distance = self.__user__get_distance(
                            self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'][0],
                            current_job_list[temp_job].delivery_position)
                    '''
            else:
                temp_distance += self.__user__get_distance(current_job_list[temp_job - 1].delivery_position,
                                                           current_job_list[temp_job].picking_position)
                temp_distance += self.__user__get_distance(current_job_list[temp_job].picking_position,
                                                           current_job_list[temp_job].delivery_position)
                temp_distance += 7
            if current_job_list[temp_job] == current_job_list[-1]:
                temp_distance -= 4      # 把任务的picking算上故而减去
                break
            temp_job += 1
        '''
        此段计算字典中的距离
        '''
        temp_dit = 0
        while True:
            if temp_dit == 0:
                temp_distance += self.__user__get_distance(current_job_list[-1].delivery_position, vehicle_to_jobs_dict[current_vehicle][temp_dit].picking_position)  # 计算并更新距离
                temp_distance += self.__user__get_distance(vehicle_to_jobs_dict[current_vehicle][temp_dit].picking_position,
                                                           vehicle_to_jobs_dict[current_vehicle][temp_dit].delivery_position)
                temp_distance += 7
            else:
                temp_distance += self.__user__get_distance(vehicle_to_jobs_dict[current_vehicle][temp_dit-1].delivery_position,
                                                           vehicle_to_jobs_dict[current_vehicle][
                                                               temp_dit].picking_position)  # 计算并更新距离
                temp_distance += self.__user__get_distance(
                    vehicle_to_jobs_dict[current_vehicle][temp_dit].picking_position,
                    vehicle_to_jobs_dict[current_vehicle][temp_dit].delivery_position)
                temp_distance += 7
            if vehicle_to_jobs_dict[current_vehicle][-1] == vehicle_to_jobs_dict[current_vehicle][temp_dit]:
                break
            temp_dit += 1

        temp_distance += self.__user__get_distance(getattr(row_job, "Job").picking_position, vehicle_to_jobs_dict[current_vehicle][-1].delivery_position)
        return temp_distance

    def __not_dit_distance(self, current_job_list, current_vehicle, current_staus, row_job):
        temp_job = 0
        temp_distance = 0
        while True:
            if temp_job == 0:
                if current_staus == 'Pick' or current_staus == 'Idle':
                    # if self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'] == []:
                    temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'StartPosition'], current_job_list[temp_job].picking_position)
                    temp_distance += 7
                '''
                else:
                    temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'ReservationToRelease'][-1], current_job_list[temp_job].picking_position)
                    print("-2-")
                    print(temp_distance)
                    print("----------------")
                temp_distance += self.__user__get_distance(current_job_list[temp_job].picking_position, current_job_list[temp_job].delivery_position)
                 '''
            if current_staus == 'Delivery':
                # if self.__vehicle_df.loc[current_vehicle.id, 'DynamicRoute'] == []:
                    temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'StartPosition'], current_job_list[temp_job].delivery_position)
                    temp_distance += 3
                    '''
                    else:
                        temp_distance = self.__user__get_distance(self.__vehicle_df.loc[current_vehicle.id, 'ReservationToRelease'][-1], current_job_list[temp_job].delivery_position)
                        print("-4-")
                        print(temp_distance)
                        print("----------------")
                       
                        '''
            else:
                temp_distance += self.__user__get_distance(current_job_list[temp_job - 1].delivery_position,
                                                           current_job_list[temp_job].picking_position)
                temp_distance += self.__user__get_distance(current_job_list[temp_job].picking_position,
                                                           current_job_list[temp_job].delivery_position)
                temp_distance += 7
            if current_job_list[temp_job] == current_job_list[-1]:
                # print(temp_distance)
                break
            temp_job += 1
        temp_distance += self.__user__get_distance(getattr(row_job, "Job").picking_position, current_job_list[-1].delivery_position)
        # print(temp_distance)
        return temp_distance

