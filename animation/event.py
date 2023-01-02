from animation.utils import *

class Event():
    def __init__(self, single_event, duration):
        self.event_type = single_event["event_type"]
        self.datetime = single_event["time"]
        self.timestamp = datetime_to_timestamp(single_event["time"])
        self.coors = single_event["coors"]
        self.duration = duration
        self.dispatched = False
        self.completed = False

    def set_dispatched(self, value):
        self.dispatched = value

    def set_completed(self, value):
        self.completed = value

    def __repr__(self):
        return "Event: {} | Coors: {} | Time needed: {} | Dispatched: {}".\
            format(self.event_type, self.coors, self.duration, self.dispatched)