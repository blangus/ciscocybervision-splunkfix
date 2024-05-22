import requests
import os
import json

import splunk.admin as admin
import splunk.version as ver
import splunk.rest as rest

from splunktaucclib.rest_handler.endpoint.validator import Validator
import logger_manager as log
import TA_cisco_cybervision_utils as utils
logger = log.setup_logging('ta_cisco_cybervision_server_validation')


class GetSessionKey(admin.MConfigHandler):
    """Class to initialize session key."""

    def __init__(self):
        """Initializes session key."""
        self.session_key = self.getSessionKey()


class ValidateAccount(Validator):
    """Class to Validate account fields."""

    __URL_FORMAT = "__REST_CREDENTIAL__#TA-cisco_cybervision#configs"\
                   "/conf-ta_cisco_cybervision_settings:proxy``splunk_cred_sep``1:"
    __URL_ENCODE = requests.compat.quote_plus(__URL_FORMAT)

    def __init__(self, *args, **kwargs):
        """:param validator: user-defined validating function."""
        super(ValidateAccount, self).__init__()
        self.my_app = __file__.split(os.sep)[-3]

    def get_proxy(self):
        """
        Gives information of proxy if proxy is enable.

        :return: dictionary having proxy information
        """
        session_key = GetSessionKey().session_key
        proxy_settings = None

        _, response_content = rest.simpleRequest(
            "/servicesNS/nobody/{}/configs/conf-ta_cisco_cybervision_settings/proxy"
            .format(self.my_app),
            sessionKey=session_key,
            getargs={"output_mode": "json"},
            raiseAllErrors=True)
        proxy_info = json.loads(response_content)['entry'][0]['content']
        if int(proxy_info.get("proxy_enabled", 0)) == 0:
            return proxy_settings

        proxy_port = proxy_info.get('proxy_port')
        proxy_url = proxy_info.get('proxy_url')
        proxy_type = proxy_info.get('proxy_type')
        proxy_username = proxy_info.get('proxy_username', '')
        proxy_password = ''

        if proxy_username:
            try:
                _, response_content = rest.simpleRequest(
                    "/servicesNS/nobody/{}/storage/passwords/".format(
                        self.my_app) + self.__URL_ENCODE,
                    sessionKey=session_key,
                    getargs={"output_mode": "json"},
                    raiseAllErrors=True)
                response_dict = json.loads(
                    response_content)['entry'][0]['content']
                cred = json.loads(response_dict.get('clear_password', '{}'))
                proxy_password = cred.get("proxy_password", None)
            except Exception as e:
                self.put_msg("Error While Fetching Proxy")
                logger.exception(
                    "Error While fetching proxy \n Error: {}".format(str(e)))
        proxy_settings = self.get_proxy_setting(proxy_type, proxy_username,
                                                proxy_password, proxy_url,
                                                proxy_port)
        return proxy_settings

    def get_proxy_setting(self, proxy_type, proxy_username, proxy_password,
                          proxy_url, proxy_port):
        """Function To get Proxy Setting."""
        if proxy_username and proxy_password:
            proxy_username = requests.compat.quote_plus(proxy_username)
            proxy_password = requests.compat.quote_plus(proxy_password)
            proxy_uri = "%s://%s:%s@%s:%s" % (proxy_type, proxy_username,
                                              proxy_password, proxy_url,
                                              proxy_port)
        else:
            proxy_uri = "%s://%s:%s" % (proxy_type, proxy_url, proxy_port)
        proxy_settings = {"http": proxy_uri, "https": proxy_uri}

        return proxy_settings

    def validate(self, value, data):
        """
        Check if the given value is valid.

        :param value: value to validate.
        :param data: whole payload in request.
        :return True or False
        """
        # Get Splunk Version
        splunk_version = ver.__version__
        # Get proxy settings information
        #try:
        #    proxy_settings = self.get_proxy()
        #except Exception as exception:
        #    logger.exception(
        #        "Error while fetching proxy information.\n Error: {}".format(
        #            exception))
        #    self.put_msg("Error while fetching proxy information.")
        #    return False

        ip_address = data['ip_address']
        user_agent = "Splunk/{}".format(splunk_version)
        error_msg_prefix = "Connection unsuccessful."
        if not ip_address.startswith('https://'):
            self.put_msg("IP Address must start with https.")
            logger.error("IP Address must start with https.")
            return False
        api_token = data.get('api_token')
        if not api_token:
            self.put_msg("API Token is required.")
            logger.error("API Token is required.")
            return False
        #verify_ssl = utils.VERIFY_SSL
        header = {
            'x-token-id': api_token,
            'user-agent': user_agent
        }
        try:
            response = requests.get("{}/api/3.0/components".format(ip_address),
                                    headers=header,
                                    timeout=10, verify=False)
            response.raise_for_status()
            if response.status_code == 200 or response.status_code == 201:
                try:
                    response.json()
                    return True
                except Exception:
                    self.put_msg("{} Please verify API Token, IP Address and "
                                 "Proxy Settings are correct.".format(error_msg_prefix))
                    logger.error("API Token, IP Address or Proxy Settings are incorrect.")
                    return False
            else:
                self.put_msg("{} Please verify API Token, IP Address and "
                             "Proxy Settings are correct.".format(error_msg_prefix))
                logger.error("API Token, IP Address or Proxy Settings are incorrect.")
        except requests.exceptions.SSLError:
            self.put_msg("SSL certificate verification failed. Please add a valid "
                         "SSL Certificate or Change VERIFY_SSL flag to False")
            logger.error("SSL certificate verification failed. Please add a valid "
                         "SSL Certificate or Change VERIFY_SSL flag to False")
            return False
        except Exception:
            self.put_msg("{} Please verify API Token, IP Address and Proxy Settings "
                         "are correct.".format(error_msg_prefix))
            logger.error(
                "Could not validate account provided IP Address {}. Response: {}. Exception{}".format(ip_address, response_text, str(e)))
            return False
