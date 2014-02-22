# -*- coding: utf-8 -*-
from core import logger, common, webrequest


class Station:
    def __init__(self, data_list):
        # Format of each entry is as follows:
        # bjb|北京北|VAP|beijingbei|bjb|0
        # 0 -> defines alphabetical order, pretty useless
        # 1 -> user-friendly name
        # 2 -> station ID
        # 3 -> name in pinyin
        # 4 -> name in pinyin (abbreviated to first characters)
        # 5 -> station number (0-indexed)
        assert len(data_list) == 6
        self.name = data_list[1]
        self.id = data_list[2]
        self.pinyin = data_list[3]
        self.abbreviation = data_list[4]

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "{0} (ID: {1})".format(self.name, self.id)


class StationList:
    def __init__(self, use_dict=True):
        self.stations = self.__get_all_stations()
        # We can get better lookup performance at the
        # cost of higher memory usage. Choose wisely.
        if use_dict:
            self.name_lookup = {station.name: station for station in self.stations}
            self.id_lookup = {station.id: station for station in self.stations}
            self.pinyin_lookup = {station.pinyin: station for station in self.stations}
            self.abbreviation_lookup = {station.abbreviation: station for station in self.stations}
        else:
            self.name_lookup = None
            self.id_lookup = None
            self.pinyin_lookup = None
            self.abbreviation_lookup = None

    @staticmethod
    def __get_all_stations():
        url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        response = webrequest.get(url)
        js_split = response.text.split("'")
        assert len(js_split) == 3
        station_split = js_split[1].split("@")
        station_data_list = common.slice_list(station_split, start=1)
        station_list = [Station(item.split("|")) for item in station_data_list]
        logger.debug("Fetched station list ({0} stations)".format(len(station_list)))
        return station_list

    def get_by_name(self, station_name):
        if self.name_lookup is None:
            for station in self.stations:
                if station.name == station_name:
                    return station
            raise KeyError()
        else:
            return self.name_lookup[station_name]

    def get_by_id(self, station_id):
        if self.id_lookup is None:
            for station in self.stations:
                if station.id == station_id:
                    return station
            raise KeyError()
        else:
            return self.id_lookup[station_id]

    def get_by_pinyin(self, station_pinyin):
        if self.pinyin_lookup is None:
            for station in self.stations:
                if station.pinyin == station_pinyin:
                    return station
            raise KeyError()
        else:
            return self.pinyin_lookup[station_pinyin]

    def get_by_abbreviation(self, station_abbreviation):
        if self.abbreviation_lookup is None:
            for station in self.stations:
                if station.abbreviation == station_abbreviation:
                    return station
            raise KeyError()
        else:
            return self.pinyin_lookup[station_abbreviation]

    def __iter__(self):
        for station in self.stations:
            yield station

    def __len__(self):
        return len(self.stations)