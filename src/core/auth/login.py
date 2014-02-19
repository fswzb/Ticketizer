# -*- coding: utf-8 -*-
from core import logger, webrequest
from core.errors import LoginFailedError, InvalidOperationError
from core.auth.cookies import SessionCookies
from core.auth.captcha import CaptchaType, Captcha
from core.auth.purchase import TicketPurchaser


class LoginManager:
    def __init__(self):
        self.__cookies = SessionCookies()
        self.__username = None

    def __del__(self):
        # Doesn't matter if this throws an exception; it will be ignored anyways
        if self.__username is not None:
            self.logout()

    @staticmethod
    def __get_login_params(username, password, captcha_answer):
        return {
            "loginUserDTO.user_name": username,
            "userDTO.password": password,
            "randCode": captcha_answer
        }

    def __is_logged_in(self):
        if self.__username is None:
            return False
        url = "https://kyfw.12306.cn/otn/login/checkUser"
        return webrequest.post_json(url, cookies=self.__cookies)["data"]["flag"] is True

    def get_purchaser(self):
        if not self.__is_logged_in():
            raise InvalidOperationError("Cannot purchase tickets without logging in")
        return TicketPurchaser(self.__cookies)

    def login(self, username, password, captcha):
        # Submit user credentials to the server
        data = self.__get_login_params(username, password, captcha.answer)
        url = "https://kyfw.12306.cn/otn/login/loginAysnSuggest"
        json = webrequest.post_json(url, data=data, cookies=self.__cookies)
        # Check server response to see if login was successful
        # response > data > loginCheck should be "Y" if we logged in
        # otherwise, loginCheck will be absent
        webrequest.check_json_flag(json, "data", "loginCheck", exception=LoginFailedError)
        logger.debug("Successfully logged in with username " + username)
        self.__username = username

    def logout(self):
        webrequest.get("https://kyfw.12306.cn/otn/login/loginOut", cookies=self.__cookies)
        if self.__username is not None:
            # noinspection PyTypeChecker
            logger.debug("Logged out of user: " + self.__username)
        else:
            logger.warning("Logged out of unknown user")

    def get_login_captcha(self):
        return Captcha(CaptchaType.LOGIN, self.__cookies)