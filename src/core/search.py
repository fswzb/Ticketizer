# -*- coding: utf-8 -*-
import datetime
import requests
from . import data
from . import logger
from . import common
from . import enums


class TicketPricing:
    NORMAL = "ADULT"
    STUDENT = "0X00"


class TicketDirection:
    ONE_WAY = "dc"
    ROUND_TRIP = "fc"


class ValueRange:

    def __init__(self, lower=None, upper=None):
        self.lower = lower
        self.upper = upper

    def has_check(self):
        return self.lower is not None or self.lower is not None

    def check_value(self, value):
        lower = self.lower
        upper = self.upper
        if lower is None:
            if upper is None:
                return True
            else:
                return value <= upper
        else:
            if upper is None:
                return lower <= value
            else:
                return lower <= value <= upper
        

class TrainSorter:
    
    def __init__(self):
        self.favorites = {}
        self.sorters = []
        self.reverse = False
        
    def set_train_favorited(self, train_name, favorite):
        self.favorites[train_name] = favorite

    def get_train_favorited(self, train_name):
        return self.favorites.get(train_name, False)

    def toggle_train_favorited(self, train_name):
        self.set_train_favorited(train_name, not self.get_train_favorited(train_name))

    def sort(self, train_list):
        for sorter in self.sorters:
            sorter(train_list, self.reverse)

    def sort_by_number(self, train_list, reverse):
        # Note: does NOT take into account the train type!
        # To sort by the type as well, call sort_by_type after this!
        type_stripper = lambda x: x.name[1:] if str.isalpha(x.name[0]) else x.name
        self.__sort_by_key(train_list, lambda x: int(type_stripper(x)), reverse)

    def sort_by_type(self, train_list, reverse):
        self.__sort_by_key(train_list, lambda x: x.type, reverse)

    def sort_by_departure_time(self, train_list, reverse):
        self.__sort_by_key(train_list, lambda x: x.departure_time, reverse)

    def sort_by_arrival_time(self, train_list, reverse):
        self.__sort_by_key(train_list, lambda x: x.arrival_time, reverse)

    def sort_by_duration(self, train_list, reverse):
        self.__sort_by_key(train_list, lambda x: x.duration, reverse)

    def sort_by_price(self, train_list, reverse):
        # No idea why anyone would want to sort by maximum price, but whatever...
        # This method intelligently uses the min/max price of the train's tickets.
        # That means that doing an ascending sort and reversing is NOT the same as
        # doing a descending sort! It MIGHT be (if you're lucky), but not guaranteed!
        if reverse:
            ticket_price_func = lambda x: 0 if x.price is None else x.price
            train_price_func = lambda x: max(map(ticket_price_func, x.tickets.values()))
        else:
            ticket_price_func = lambda x: float("inf") if x.price is None else x.price
            train_price_func = lambda x: min(map(ticket_price_func, x.tickets.values()))
        self.__sort_by_key(train_list, train_price_func, reverse)

    def __sort_by_key(self, train_list, compare_key, reverse):
        # Sorts the train list using the specified key,
        # keeping "favorite" trains in the front.
        # The sorting algorithm used must be stable for this to work!
        train_list.sort(key=compare_key, reverse=reverse)
        train_list.sort(key=lambda x: 0 if self.favorites.get(x.name, False) else 1)
        

class TrainFilter:
    
    def __init__(self):
        # Type mask to filter train types
        self.train_type_filter = enums.TrainType.ALL
        # Type mask to filter ticket types
        self.ticket_type_filter = enums.TicketType.ALL
        # Dictionary of train names to blacklist
        # True = ignored, False/no key = OK
        self.blacklist = {}
        # Departure and arrival time filters. Trains that depart/arrive
        # outside this time range will be ignored. -- ValueRange<datetime.time>
        # Very important note: These compare __times__, and not __datetimes__!
        self.departure_time_range = ValueRange()
        self.arrival_time_range = ValueRange()
        # Duration time filter. Trains that have a travel time
        # outside this range will be ignored. -- ValueRange<datetime.timedelta>
        self.duration_range = ValueRange()
        # Price filter. Tickets with prices outside
        # this range will be ignored. (ValueRange)
        self.price_range = ValueRange()
        # Whether to ignore trains that aren't selling tickets yet
        self.filter_not_yet_sold = False
        # Whether to ignore trains that are completely sold out
        self.filter_sold_out = False

    def disable_all_train_types(self):
        self.train_type_filter = enums.TrainType.NONE

    def enable_all_train_types(self):
        self.train_type_filter = enums.TrainType.ALL

    def set_train_type_enabled(self, train_type, enable):
        if enable:
            self.train_type_filter |= train_type
        else:
            self.train_type_filter &= ~train_type

    def get_train_type_enabled(self, train_type):
        return (self.train_type_filter & train_type) == train_type

    def toggle_train_type_enabled(self, train_type):
        self.train_type_filter ^= train_type

    def enable_all_trains(self):
        self.blacklist.clear()
    
    def set_train_enabled(self, train_name, enable):
        self.blacklist[train_name] = not enable
    
    def get_train_enabled(self, train_name):
        return not self.blacklist.get(train_name, False)

    def toggle_train_enabled(self, train_name):
        self.set_train_enabled(train_name, not self.get_train_enabled(train_name))

    def disable_all_ticket_types(self):
        self.ticket_type_filter = enums.TicketType.NONE

    def enable_all_ticket_types(self):
        self.ticket_type_filter = enums.TicketType.ALL

    def set_ticket_type_enabled(self, ticket_type, enable):
        if enable:
            self.ticket_type_filter |= ticket_type
        else:
            self.ticket_type_filter &= ~ticket_type

    def get_ticket_type_enabled(self, ticket_type):
        return (self.ticket_type_filter & ticket_type) == ticket_type

    def toggle_ticket_type_enabled(self, ticket_type):
        self.ticket_type_filter ^= ticket_type

    def __filter_tickets(self, ticket_dict):
        for ticket in ticket_dict.values():
            if ticket.count.status == enums.TicketStatus.NotApplicable:
                continue
            if self.filter_sold_out and ticket.count.status == enums.TicketStatus.SoldOut:
                continue
            if self.filter_not_yet_sold and ticket.count.status == enums.TicketStatus.NotYetSold:
                continue
            if (self.ticket_type_filter & ticket.type) != ticket.type:
                continue
            # Try to lazily evaluate ticket price to save a lot of network requests
            if self.price_range.has_check() and not self.price_range.check_value(ticket.price):
                continue
            yield ticket
    
    def __filter_trains(self, train_list):
        for train in train_list:
            if (self.train_type_filter & train.type) != train.type:
                continue
            if self.blacklist.get(train.name, False):
                continue
            if not self.departure_time_range.check_value(train.departure_time.time()):
                continue
            if not self.arrival_time_range.check_value(train.arrival_time.time()):
                continue
            if not self.duration_range.check_value(train.duration):
                continue
            if next(self.__filter_tickets(train.tickets), None) is None:
                continue
            yield train

    def filter(self, train_list):
        return list(self.__filter_trains(train_list))


class TrainQuery:

    def __init__(self):
        # The type of ticket pricing -- normal ("adult") or student
        self.type = TicketPricing.NORMAL
        # The trip type -- one-direction or round-trip
        self.direction = TicketDirection.ONE_WAY

        # Strings are allowed for the following parameters
        # to make testing easier (don't need to instantiate
        # any complex objects, just use the date/ID directly).

        # The departure date -- datetime.date
        self.date = None
        # The departure station -- data.Station
        self.departure_station = None
        # The destination station -- data.Station
        self.destination_station = None

    def __get_query_string(self):
        return common.get_ordered_query_params(
            "leftTicketDTO.train_date", common.date_to_str(self.date),
            "leftTicketDTO.from_station", self.departure_station.id,
            "leftTicketDTO.to_station", self.destination_station.id,
            "purpose_codes", self.type)

    def execute(self):
        url = "https://kyfw.12306.cn/otn/leftTicket/query?" + self.__get_query_string()
        response = requests.get(url, verify=False)
        response.raise_for_status()
        json_data = common.read_json_data(response)
        logger.debug("Got ticket list from {0} to {1} on {2}".format(
            self.date,
            self.departure_station,
            self.destination_station
        ), response)
        train_list = []
        for train_data in json_data:
            combined_data = common.combine_subdicts(train_data)
            train_list.append(data.Train(combined_data, self.departure_station, self.destination_station))
        return train_list


class TicketSearcher:

    def __init__(self):
        self.query = None
        self.filter = None
        self.sorter = None

    def filter_by_train(self, train_list):
        if self.filter is not None:
            return self.filter.filter(train_list)
        else:
            return train_list

    def sort_trains(self, train_list):
        if self.sorter is not None:
            self.sorter.sort(train_list)

    def get_train_list(self):
        train_list = self.query.execute()
        train_list = self.filter_by_train(train_list)
        self.sort_trains(train_list)
        return train_list
