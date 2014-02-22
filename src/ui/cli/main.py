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

import datetime
import os
from configparser import RawConfigParser
from core import common, logger
from core.errors import StopPathSearch, StopCaptchaRetry, StopPurchaseQueue, LoginFailedError
from core.enums import TrainType, TicketType, TicketStatus
from core.data.station import StationList
from core.search.search import TicketSearcher, TrainQuery
from core.search.pathing import PathFinder
from core.processing.filter import TrainFilter
from core.processing.sort import TrainSorter
from core.auth.login import LoginManager

config = RawConfigParser()
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.cfg"))

always_auto = config.getboolean("Config", "always_auto")
logging_enabled = config.getboolean("Config", "logging_enabled")

auto_username = config.get("Config", "username")
auto_password = config.get("Config", "password")

auto_from_station = config.get("Config", "from_station")
auto_to_station = config.get("Config", "to_station")
auto_train_date = config.get("Config", "train_date")

auto_min_xfer_time = config.get("Config", "min_xfer_time")
auto_max_xfer_time = config.get("Config", "max_xfer_time")


def main():
    logger.set_type_enabled(logger.LogType.NETWORK, logging_enabled)
    logger.set_type_enabled(logger.LogType.DEBUG, logging_enabled)

    def menu_validator(answer):
        answer = answer.upper()
        if answer == "LOGIN":
            return "L"
        if answer == "LOGOUT":
            return "O"
        if answer == "SEARCH":
            return "S"
        if answer == "PATH":
            return "P"
        if answer == "BUY":
            return "B"
        if answer == "EXIT":
            return "X"
        raise ValueError("Oh dear, that's not an option! :c")

    sl = StationList()
    lm = None
    tl = None
    while True:
        menu_opt = prompt_valid("Select option (login, logout, search, buy, path, exit): ", menu_validator)
        try:
            if menu_opt == "X":
                print("Bye~")
                return
            if menu_opt == "L":
                lm = login()
            elif menu_opt == "O":
                if lm is not None:
                    lm.logout()
                    lm = None
            elif menu_opt == "S":
                tl = search_tickets(sl)
                print_train_info(tl)
            elif menu_opt == "P":
                if tl is None:
                    tl = search_tickets(sl)
                if len(tl) == 0:
                    print("No trains, try searching for something else!")
                    continue
                train = console_train_selector(tl)
                get_alternative_path(sl, train)
            elif menu_opt == "B":
                if lm is None:
                    lm = login()
                if tl is None:
                    tl = search_tickets(sl)
                if len(tl) == 0:
                    print("No trains, try searching for something else!")
                    continue
                train = console_train_selector(tl)
                purchase_tickets(lm, train)
        except (StopCaptchaRetry, StopPathSearch, StopPurchaseQueue):
            pass


def login():
    login_manager = LoginManager()
    username = prompt_default_valid("Enter your username: ", lambda x: x, auto_username)
    password = prompt_default_valid("Enter your password: ", lambda x: x, auto_password)
    captcha = get_and_solve_captcha(login_manager.get_login_captcha)
    try:
        login_manager.login(username, password, captcha)
        print("Logged in with username: " + username)
        return login_manager
    except LoginFailedError:
        print("Login failed, check your username and password!")
        return None


def search_tickets(station_list):
    tq = get_ticket_query(station_list)
    tf = TrainFilter()

    # tf.ticket_filter.filter_sold_out = True
    # tf.ticket_filter.filter_not_yet_sold = True

    # tf.enabled_types.disable_all()
    # tf.enabled_types[TrainType.T] = True
    # tf.enabled_types[TrainType.D] = True

    # tf.ticket_filter.enabled_types.disable_all()
    # tf.ticket_filter.enabled_types[TicketType.HARD_SEAT] = True
    # tf.ticket_filter.enabled_types[TicketType.SOFT_SEAT] = True

    # tf.blacklist.add("T111")
    # tf.whitelist.add("T7785")

    # tf.price_range.upper = 1000
    # tf.price_range.lower = 500

    # tf.duration_range.upper = datetime.timedelta(hours=10)

    # tf.departure_time_range.lower = common.str_to_time("10:00")
    # tf.departure_time_range.upper = common.str_to_time("18:00")

    # tf.arrival_time_range.lower = common.str_to_time("12:00")
    # tf.arrival_time_range.upper = common.str_to_time("22:00")

    ts = TrainSorter()
    ts.sort_methods.append(ts.sort_by_number)
    ts.sort_methods.append(ts.sort_by_type)
    x = TicketSearcher()
    x.filter = tf
    x.query = tq
    x.sorter = ts
    return x.get_train_list()


def get_ticket_query(station_list):
    tq = TrainQuery(station_list)

    def get_date(answer):
        return common.str_to_date(answer)

    def get_station(answer):
        return get_station_from_text(station_list, answer)

    date = prompt_default_valid("Enter train date (YYYY-mm-dd format): ", get_date, auto_train_date)
    from_station = prompt_default_valid("Enter origin station: ", get_station, auto_from_station)
    to_station = prompt_default_valid("Enter destination station: ", get_station, auto_to_station)
    tq.date = date
    tq.departure_station = from_station
    tq.destination_station = to_station
    return tq


def get_alternative_path(station_list, train):
    pf = PathFinder(station_list, console_path_selector)

    def time_conv(answer):
        return str_to_timedelta(answer)

    min_xfer = prompt_default_valid("Enter the minimum transfer time (H:MM format): ", time_conv, auto_min_xfer_time)
    max_xfer = prompt_default_valid("Enter the maximum transfer time (H:MM format): ", time_conv, auto_max_xfer_time)
    pf.transfer_time_range.lower = min_xfer
    pf.transfer_time_range.upper = max_xfer
    path = pf.get_path(train)
    if path is not None:
        print("Got path from {0} to {1}:".format(train.departure_station.name, train.destination_station.name))
        for subtrain in path:
            print("[{0}] {1}: {2} -> {3}".format(
                common.datetime_to_str(subtrain.departure_time),
                subtrain.name,
                subtrain.departure_station.name,
                subtrain.destination_station.name))
    return path


def purchase_tickets(login_manager, train):
    pd = login_manager.get_purchaser()
    pd.train = train
    pd.begin_purchase()
    passenger_list = pd.get_passenger_list()
    selected_passengers = console_passenger_selector(passenger_list)
    passenger_dict = console_ticket_selector(selected_passengers, pd.train)
    captcha = get_and_solve_captcha(pd.get_purchase_captcha)
    order_id = pd.continue_purchase(passenger_dict, captcha, console_queue_callback)
    print("Order completed! ID: " + order_id)


def console_train_selector(train_list):
    print_tickets_remaining(train_list)

    def get_train(answer):
        for train in train_list:
            if train.name == answer.upper():
                return train
        raise ValueError("That's not in the list of trains, silly!")

    return prompt_valid("Enter a train name: ", get_train)


def console_passenger_selector(passenger_list):
    for i in range(len(passenger_list)):
        print("{0}. {1}".format(i, passenger_list[i].name))

    def get_passengers(answer):
        ind_split = answer.split(",")
        passengers = []
        for ind in ind_split:
            passengers.append(passenger_list[int(ind.strip())])
        return passengers

    return prompt_valid("Select passenger number(s) -- separate by commas: ", get_passengers)


def console_ticket_selector(passenger_list, train):
    ticket_list = [x for x in train.tickets if x.status == TicketStatus.NORMAL]
    print_ticket_info(ticket_list)

    def select_tickets(answer):
        return ticket_list[int(answer.strip())]

    passenger_dict = {}
    for passenger in passenger_list:
        ticket = prompt_valid("Enter ticket type # for " + passenger.name + ": ", select_tickets)
        passenger_dict[passenger] = ticket
    return passenger_dict


def console_queue_callback(queue_length):
    print("Waiting in line, current queue length: " + str(queue_length))
    resp = input("Type 'ABORT' to abort, or anything else to check again: ")
    if resp == "ABORT":
        raise StopPurchaseQueue()


def console_captcha_solver(image_data):
    # noinspection PyUnresolvedReferences
    captcha_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captcha.jpg")
    with open(captcha_path, "wb") as f:
        f.write(image_data)
    answer = input("Enter captcha answer: ")
    try:
        if answer == "CHANGE":
            answer = None
        elif answer == "ABORT":
            raise StopCaptchaRetry()
    finally:
        os.remove(captcha_path)
    return answer


def console_path_selector(train_list):
    def get_train(answer):
        if answer == "UNDO":
            return None
        if answer == "ABORT":
            raise StopPathSearch()
        for train in train_list:
            if train.name == answer.upper():
                return train
        raise ValueError("That's not in the list of trains, silly!")
    if len(train_list) > 0:
        print_train_info(train_list)
        prompt = "Enter a train name: "
    else:
        prompt = "No trains in this path! Type 'UNDO' to go back or 'ABORT' to exit: "
    return prompt_valid(prompt, get_train, StopPathSearch)


def print_ticket_info(ticket_list):
    pretty_print_table(ticket_list, ("#", "Count", "Price", "Type"),
                       lambda i, x: (i,
                                     x.count,
                                     x.price,
                                     TicketType.FULL_NAME_LOOKUP[x.type]))


def print_tickets_remaining(train_list):
    pretty_print_table(train_list,
                      ("Name", "Date", "Departure", "Arrival", "Duration", "Business", "Special",
                       "First class", "Second class", "Sleeper+", "Soft sleeper",
                       "Hard sleeper", "Soft seat", "Hard seat", "No seat", "Other"),
                       lambda i, x: (x.name,
                                     common.date_to_str(x.departure_time, "%m/%d"),
                                     common.time_to_str(x.departure_time),
                                     common.time_to_str(x.arrival_time),
                                     common.timedelta_to_str(x.duration),
                                     get_ticket_count(x, TicketType.BUSINESS),
                                     get_ticket_count(x, TicketType.SPECIAL),
                                     get_ticket_count(x, TicketType.FIRST_CLASS),
                                     get_ticket_count(x, TicketType.SECOND_CLASS),
                                     get_ticket_count(x, TicketType.SOFT_SLEEPER_PRO),
                                     get_ticket_count(x, TicketType.SOFT_SLEEPER),
                                     get_ticket_count(x, TicketType.HARD_SLEEPER),
                                     get_ticket_count(x, TicketType.SOFT_SEAT),
                                     get_ticket_count(x, TicketType.HARD_SEAT),
                                     get_ticket_count(x, TicketType.NO_SEAT),
                                     get_ticket_count(x, TicketType.OTHER)))


def print_ticket_prices(train_list):
    pretty_print_table(train_list,
                      ("Name", "Date", "Departure", "Arrival", "Duration", "Business", "Special",
                       "First class", "Second class", "Sleeper+", "Soft sleeper",
                       "Hard sleeper", "Soft seat", "Hard seat", "No seat", "Other"),
                       lambda i, x: (x.name,
                                     common.date_to_str(x.departure_time, "%m/%d"),
                                     common.time_to_str(x.departure_time),
                                     common.time_to_str(x.arrival_time),
                                     common.timedelta_to_str(x.duration),
                                     get_ticket_price(x, TicketType.BUSINESS),
                                     get_ticket_price(x, TicketType.SPECIAL),
                                     get_ticket_price(x, TicketType.FIRST_CLASS),
                                     get_ticket_price(x, TicketType.SECOND_CLASS),
                                     get_ticket_price(x, TicketType.SOFT_SLEEPER_PRO),
                                     get_ticket_price(x, TicketType.SOFT_SLEEPER),
                                     get_ticket_price(x, TicketType.HARD_SLEEPER),
                                     get_ticket_price(x, TicketType.SOFT_SEAT),
                                     get_ticket_price(x, TicketType.HARD_SEAT),
                                     get_ticket_price(x, TicketType.NO_SEAT),
                                     get_ticket_price(x, TicketType.OTHER)))


def print_train_info(train_list):
    pretty_print_table(train_list,
                      ("Name", "Date", "Departure station", "Destination station",
                       "Departure time", "Arrival time", "Duration"),
                       lambda i, x: (x.name,
                                     common.date_to_str(x.departure_time, "%m/%d"),
                                     x.departure_station.id + " (" + x.departure_station.pinyin + ")",
                                     x.destination_station.id + " (" + x.destination_station.pinyin + ")",
                                     common.time_to_str(x.departure_time),
                                     common.time_to_str(x.arrival_time),
                                     common.timedelta_to_str(x.duration)))


def get_ticket_count(train, ticket_type):
    return str(train.tickets[ticket_type].count)


def get_ticket_price(train, ticket_type):
    price = train.tickets[ticket_type].price
    if price is None:
        return "--"
    return str(price)


def get_station_from_text(station_list, text):
    methods = (station_list.id_lookup,
               station_list.abbreviation_lookup,
               station_list.name_lookup,
               station_list.pinyin_lookup)

    def select_station(abbrev_station_list):
        def validator(answer):
            return abbrev_station_list[int(answer)]

        for i in range(len(abbrev_station_list)):
            print("{0}. {1}".format(i, abbrev_station_list[i].name))
        return prompt_valid("Select a station #: ", validator)

    for method in methods:
        station = method.get(text)
        if isinstance(station, list):
            station = select_station(station)
        if station is not None:
            return station
    raise KeyError("Station not found: " + text)


def str_to_timedelta(timedelta_str, start_with_hours=True):
    split = timedelta_str.split(":")
    length = len(split)
    if start_with_hours:
        if length == 1:
            # Assume hours
            return datetime.timedelta(hours=int(split[0]))
        if length == 2:
            # Assume hours and minutes
            return datetime.timedelta(hours=int(split[0]), minutes=int(split[1]))
        if length == 3:
            # Assume hours, minutes, seconds
            return datetime.timedelta(hours=int(split[0]), minutes=int(split[1]), seconds=int(split[2]))
    else:
        if length == 1:
            # Assume minutes
            return datetime.timedelta(minutes=int(split[0]))
        if length == 2:
            # Assume minutes and seconds
            return datetime.timedelta(minutes=int(split[0]), seconds=int(split[1]))
    raise ValueError("Incorrect timedelta format")


def get_and_solve_captcha(getter):
    while True:
        captcha = getter()
        while True:
            answer = console_captcha_solver(captcha.image_data)
            if answer is not None:
                success = captcha.check_answer(answer)
                if success:
                    return captcha
                else:
                    print("Incorrect answer, try again!")
            else:
                break


def pretty_print_table(items, header, mapper, padding=2):
    clengths = [len(x) for x in header]
    rvalues = [header]

    for i in range(len(items)):
        values = mapper(i, items[i])
        for j in range(len(values)):
            clengths[j] = max(clengths[j], len(str(values[j])))
        rvalues.append(values)

    for row in rvalues:
        for i in range(len(row)):
            print(str(row[i]).ljust(clengths[i] + padding), end="")
        print()


def prompt_valid(prompt, response_converter, *ignored_exceptions):
    while True:
        answer = input(prompt)
        try:
            return response_converter(answer)
        except Exception as ex:
            if isinstance(ex, ignored_exceptions):
                raise
            print("Invalid input: " + str(ex))


def prompt_default_valid(prompt, response_converter, default=None):
    while True:
        if always_auto:
            answer = default
        else:
            answer = input(prompt)
            if answer == "":
                answer = default
        try:
            return response_converter(answer)
        except Exception as ex:
            print("Invalid input: " + str(ex))


if __name__ == "__main__":
    main()