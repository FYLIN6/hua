from animation.event import Event
from animation.utils import *

class Pathmover():
    __count = 0

    def __init__(self, data):
        Pathmover.__count += 1
        self.id = "#" + str(Pathmover.__count)
        # static
        self.mover_info = data["gridmover"][0]
        self.start_coors = data["start_coors"]
        self.end_coors = data["end_coors"]
        self.start_time = data["start_time"]
        self.end_time = data["end_time"]
        self.events = self.parse_events(data["events"])
        # dynamic
        self.current_coors = self.start_coors

    def parse_events(self, events):
        """
        Append events chronologically into a list and return that list

        @param events: Contains dictionaries that describe events
        """
        event_objects = []
        event_duration = self.get_event_duration(events)
        if len(events) != len(event_duration): raise Exception("duration list and event list should be same length.")
        for i, event in enumerate(events):
            event_objects.append(Event(event, event_duration[i]))
        return event_objects

    def get_event_duration(self, events):
        """
        Get duration of a single event and appends to a list

        @param events: Contains dictionaries that describe events
        """
        event_duration = [0.0]
        for idx, event in enumerate(events):
            if idx + 1 <= len(events) - 1:
                time_prev = datetime_to_timestamp(events[idx]["time"])
                time_next = datetime_to_timestamp(events[idx+1]["time"])
                duration = time_next - time_prev
                if duration < 0:
                    raise Exception("Wrong event time sequences. Check your input files.")
                event_duration.append(duration)
        return event_duration

    def get_name(self):
        """
        Get the name of the pathmover (instance of this class)
        """
        return "{}{}".format(self.mover_info["type"], self.id)

    def get_type(self):
        """
        Get the type of the pathmover (instance of this class)
        """
        return self.mover_info["type"]

    def __repr__(self):
        return "{}{} {}; {}".format(
            self.mover_info["type"],
            self.id, 
            str(self.mover_info["length"]) + "x" + str(self.mover_info["width"]),
            "Current coordinate: " + str(self.current_coors))

