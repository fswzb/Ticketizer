# -*- coding: utf-8 -*-
import urllib.parse
import random
import re
from core import common, webrequest, logger
from core.enums import TicketPricing, TicketDirection, TicketType, TicketStatus
from core.errors import UnfinishedTransactionError, DataExpiredError
from core.errors import PurchaseFailedError, InvalidRequestError, InvalidOperationError
from core.auth.captcha import Captcha, CaptchaType
from core.data.credentials import Credentials


class TicketPurchaser:
    def __init__(self, cookies):
        self.__cookies = cookies
        self.__submit_token = None
        self.__purchase_key = None
        self.direction = TicketDirection.ONE_WAY
        self.pricing = TicketPricing.NORMAL
        self.train = None

    def __get_captcha_check_params(self):
        return {
            "REPEAT_SUBMIT_TOKEN": self.__submit_token
        }

    def __get_passenger_query_data(self):
        return {
            "REPEAT_SUBMIT_TOKEN": self.__submit_token
        }

    def __get_purchase_submit_data(self):
        return {
            "back_train_date": common.date_to_str(self.train.departure_time.date()),  # TODO
            "purpose_codes": TicketPricing.PURCHASE_LOOKUP[self.pricing],
            "query_from_station_name": self.train.departure_station.name,
            "query_to_station_name": self.train.destination_station.name,
            # Need to unescape this string or else it will become
            # double-escaped when we send the request.
            "secretStr": urllib.parse.unquote(self.train.data["secret_key"]),
            "tour_flag": self.direction,
            "train_date": common.date_to_str(self.train.departure_time.date())
        }

    def __get_check_order_data(self, passenger_strs, captcha):
        old_pass_str, new_pass_str = passenger_strs
        return {
            "REPEAT_SUBMIT_TOKEN": self.__submit_token,
            "bed_level_order_num": "000000000000000000000000000000",
            "cancel_flag": "2",
            "oldPassengerStr": old_pass_str,
            "passengerTicketStr": new_pass_str,
            "randCode": captcha.answer,
            "tour_flag": self.direction
        }

    def __get_queue_count_data(self, passenger_dict):
        date_str = self.train.departure_time.date().strftime("%a %b %d %Y 00:00:00 GMT+0800 (China Standard Time)")
        return {
            "REPEAT_SUBMIT_TOKEN": self.__submit_token,
            "fromStationTelecode": self.train.departure_station.id,
            "toStationTelecode": self.train.destination_station.id,
            "leftTicket": self.train.data["ticket_count"],
            "purpose_codes": TicketPricing.PURCHASE_LOOKUP[self.train.pricing],
            "seatType": TicketType.ID_LOOKUP[random.choice(list(passenger_dict.values())).type],
            "stationTrainCode": self.train.name,
            "train_no": self.train.id,
            "train_date": date_str
        }

    def __get_confirm_purchase_data(self, passenger_strs, captcha):
        old_pass_str, new_pass_str = passenger_strs
        return {
            "REPEAT_SUBMIT_TOKEN": self.__submit_token,
            "key_check_isChange": self.__purchase_key,
            "train_location": self.train.data["location_code"],
            "leftTicketStr": self.train.data["ticket_count"],
            "purpose_codes": TicketPricing.PURCHASE_LOOKUP[self.train.pricing],
            "oldPassengerStr": old_pass_str,
            "passengerTicketStr": new_pass_str,
            "randCode": captcha.answer
        }

    def __get_purchase_confirm_url(self):
        return {
            TicketDirection.ONE_WAY: "https://kyfw.12306.cn/otn/confirmPassenger/initDc",
            TicketDirection.ROUND_TRIP: "https://kyfw.12306.cn/otn/confirmPassenger/initWc"
        }[self.direction]

    @staticmethod
    def __get_submit_token(text):
        return re.match(".*var\s+globalRepeatSubmitToken\s*=\s*['\"]([^'\"]*).*", text, flags=re.S).group(1)

    @staticmethod
    def __get_purchase_key(text):
        return re.match(".*['\"]key_check_isChange['\"]\s*:\s*['\"]([^'\"]*).*", text, flags=re.S).group(1)

    def __get_purchase_page(self):
        url = self.__get_purchase_confirm_url()
        response = webrequest.post(url, cookies=self.__cookies)
        return response.text

    @staticmethod
    def __get_passenger_strs(passenger_dict):
        old_format = "{name},{id_type},{id_no},{passenger_type}"
        new_format = "{seat_type},0,{ticket_type},{name},{id_type},{id_no},{phone_no},N"
        format_func = lambda passenger, format_str: format_str.format(
            name=passenger.name,
            id_type=passenger.id_type,
            id_no=passenger.id_number,
            passenger_type=passenger.type,
            seat_type=TicketType.ID_LOOKUP[passenger_dict[passenger].type],
            ticket_type=passenger.type,
            phone_no=passenger.phone_number
        )
        old_passenger_str = "_".join(map(lambda x: format_func(x, old_format), passenger_dict)) + "_"
        new_passenger_str = "_".join(map(lambda x: format_func(x, new_format), passenger_dict))
        return old_passenger_str, new_passenger_str

    def __submit_order_request(self):
        url = "https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest"
        data = self.__get_purchase_submit_data()
        json = webrequest.post_json(url, data=data, cookies=self.__cookies)
        if json["status"] is not True:
            messages = json["messages"]
            for message in messages:
                if message.startswith("您还有未处理的订单"):
                    raise UnfinishedTransactionError()
                elif message.startswith("车票信息已过期"):
                    raise DataExpiredError()
            raise InvalidRequestError(common.join_list(messages))

    def __check_order_info(self, passenger_strs, captcha):
        url = "https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo"
        data = self.__get_check_order_data(passenger_strs, captcha)
        json = webrequest.post_json(url, data=data, cookies=self.__cookies)
        webrequest.check_json_flag(json, "data", "submitStatus", exception=PurchaseFailedError)

    def __get_queue_count(self, passenger_dict):
        url = "https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount"
        data = self.__get_queue_count_data(passenger_dict)
        json = webrequest.post_json(url, data=data, cookies=self.__cookies)
        if common.is_true(json["data"]["op_2"]):
            raise PurchaseFailedError("Too many people in queue")
        queue_length = int(json["data"]["countT"])
        if queue_length > 0:
            logger.debug("{0} people in queue".format(queue_length))

    def __confirm_purchase(self, passenger_strs, captcha):
        url = "https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue"
        data = self.__get_confirm_purchase_data(passenger_strs, captcha)
        json = webrequest.post_json(url, data=data, cookies=self.__cookies)
        webrequest.check_json_flag(json, "data", "submitStatus", PurchaseFailedError)

    def __ensure_order_submitted(self):
        if self.__submit_token is None:
            raise InvalidOperationError("Order has not been submitted yet")

    @staticmethod
    def __ensure_tickets_valid(passenger_dict):
        for ticket in passenger_dict.values():
            if ticket.status != TicketStatus.NORMAL:
                raise InvalidOperationError("Invalid ticket selection")

    def get_purchase_captcha(self):
        self.__ensure_order_submitted()
        check_params = self.__get_captcha_check_params()
        return Captcha(CaptchaType.PURCHASE, self.__cookies, check_params=check_params)

    def get_passenger_list(self):
        self.__ensure_order_submitted()
        url = "https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs"
        data = self.__get_passenger_query_data()
        json = webrequest.post_json(url, data=data, cookies=self.__cookies)
        passenger_data_list = json["data"]["normal_passengers"]
        logger.debug("Fetched passenger list ({0} passengers)".format(len(passenger_data_list)))
        return [Credentials(data) for data in passenger_data_list]

    def begin_purchase(self):
        # Due to the design of the 12306 API, we have to submit the
        # purchase before getting the captcha. To avoid having to use
        # a callback pattern to solve the captcha, the purchase process
        # is split into 2 steps.

        # How to use this API in a nutshell:
        # 1. Submit the order
        #    -> begin_purchase()
        # 2. Get the captcha and passenger list
        #    -> get_purchase_captcha() and get_passenger_list()
        # 3. Solve the captcha and select passengers
        #    -> (this part is for the client to implement)
        # 4. Complete the order
        #    -> continue_purchase(passenger_dict, captcha)
        #       -> passenger_dict: maps passengers to tickets
        #       -> captcha: a solved captcha object

        # Note: If continue_purchase() throws an exception,
        # you must call begin_purchase() again!
        logger.debug("Purchasing tickets for train " + self.train.name)
        self.__submit_order_request()
        purchase_page = self.__get_purchase_page()
        self.__submit_token = self.__get_submit_token(purchase_page)
        self.__purchase_key = self.__get_purchase_key(purchase_page)

    def continue_purchase(self, passenger_dict, captcha):
        self.__ensure_order_submitted()
        try:
            self.__ensure_tickets_valid(passenger_dict)
            passenger_strs = self.__get_passenger_strs(passenger_dict)
            self.__check_order_info(passenger_strs, captcha)
            self.__get_queue_count(passenger_dict)
            self.__confirm_purchase(passenger_strs, captcha)
        except:
            self.__submit_token = None
            self.__purchase_key = None
            raise