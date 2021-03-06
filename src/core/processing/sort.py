# -*- coding: utf-8 -*-
#
# This file is part of Ticketizer.
# Copyright (c) 2014 Andrew Sun <youlosethegame@live.com>
#
# Ticketizer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ticketizer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ticketizer.  If not, see <http://www.gnu.org/licenses/>.


class TrainPriorityMap:
    # TODO: Implement
    pass


class TrainSorter:
    def __init__(self):
        self.favorites = None
        self.sort_methods = None

    def sort(self, train_list):
        sort_methods = self.sort_methods
        if sort_methods is not None:
            for sorter in sort_methods:
                sorter(train_list)

        favorites = self.favorites
        if favorites is not None:
            train_list.sort(key=lambda x: favorites.get(x.name, len(favorites)))

    @staticmethod
    def sort_by_name(train_list, reverse):
        type_stripper = lambda x: x.name[1:] if str.isalpha(x.name[0]) else x.name
        train_list.sort(key=lambda x: int(type_stripper(x)), reverse=reverse)
        train_list.sort(key=lambda x: x.type, reverse=reverse)

    @staticmethod
    def sort_by_departure_time(train_list, reverse):
        train_list.sort(key=lambda x: x.departure_time, reverse=reverse)

    @staticmethod
    def sort_by_arrival_time(train_list, reverse):
        train_list.sort(key=lambda x: x.arrival_time, reverse=reverse)

    @staticmethod
    def sort_by_duration(train_list, reverse):
        train_list.sort(key=lambda x: x.duration, reverse=reverse)

    @staticmethod
    def sort_by_price(train_list, reverse):
        # No idea why anyone would want to sort by maximum price, but whatever...
        # This method intelligently uses the min/max price of the train's tickets.
        # That means that doing an ascending sort and reversing is NOT the same as
        # doing a descending sort! It MIGHT be (if you're lucky), but not guaranteed!
        if reverse:
            ticket_price_func = lambda x: 0 if x.price is None else x.price
            train_price_func = lambda x: max(map(ticket_price_func, x.tickets))
        else:
            ticket_price_func = lambda x: float("inf") if x.price is None else x.price
            train_price_func = lambda x: min(map(ticket_price_func, x.tickets))
        train_list.sort(key=train_price_func, reverse=reverse)