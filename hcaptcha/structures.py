import math

class EventRecorder:
    def __init__(self, agent):
        self._agent = agent
        self._manifest = {}
        self._state = {
            "time_buffers": {},
            "load_time": self._agent.epoch(ms=True),
            "recording": False,
            "init_record": False,
            "record": {
                "mouse": True,
                "touch": True,
                "keys": False,
                "motion": True
            }
        }

    def record(self, mouse=True, keys=True, touch=True, motion=True):
        self._manifest["st"] = self._agent.epoch(ms=True)
        self._state["init_record"] = True
        self._state["recording"] = True

    def stop(self):
        self._state["recording"] = False

    def time(self):
        return self._state["load_time"]

    def get_data(self):
        for event, recorder in self._state["time_buffers"].items():
            self._manifest[event] = recorder.get_data()
            self._manifest[event + "-mp"] = recorder.get_mean_period()
        return self._manifest

    def set_data(self, name, value):
        self._manifest[name] = value

    def reset_data(self):
        self._manifest = {}
        self._state["time_buffers"] = {}
    
    def circ_buff_push(self, event, data):
        self.record_event(event, data)
    
    def record_event(self, event, data):
        if not self._state["recording"]:
            return
        
        if not event in self._state["time_buffers"]:
            self._state["time_buffers"][event] = EventContainer(16, 15e3, agent=self._agent)

        self._state["time_buffers"][event].push(data[-1], data)

class EventContainer:
    def __init__(self, period, interval, agent):
        self._agent = agent
        self._period = period
        self._interval = interval
        self._date = []
        self._data = []
        self._prev_timestamp = 0
        self._mean_period = 0
        self._mean_counter = 0

    def get_mean_period(self):
        return self._mean_period
    
    def get_data(self):
        self._clean_stale_data()
        return self._data
    
    def get_size(self):
        self._clean_stale_data()
        return len(self._data)
    
    def get_capacity(self):
        return self._interval if not self._period else math.ceil(self._interval / self._period)
    
    def push(self, date, data):
        self._clean_stale_data()

        if date - (self._date[-1] if self._date else 0) >= self._period:
            not_first = len(self._date) > 0
            self._date.append(date)
            self._data.append(data)

            if not_first:
                delta = date - self._prev_timestamp
                self._mean_period = (self._mean_period * self._mean_counter + delta) / (self._mean_counter + 1)
                self._mean_counter += 1

        self._prev_timestamp = date

    def _clean_stale_data(self):
        date = self._agent.epoch(ms=True)
        t = len(self._date) - 1

        while t >= 0:
            if date - self._date[t] >= self._interval:
                self._date = self._date[:t + 1]
                self._data = self._data[:t + 1]
                break
            t -= 1