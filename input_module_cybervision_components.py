# encoding = utf-8

import calendar
import time
import datetime
import splunk.version as ver
import TA_cisco_cybervision_utils as utils
import re

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
'''
# For advanced users, if you want to create single instance mod input, uncomment this method.
def use_single_instance_mode():
    return True
'''


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations."""
    # This example accesses the modular input variable
    global_account = definition.parameters.get('global_account', None)
    start_date = definition.parameters.get('start_date')
    interval = definition.parameters.get('interval')
    helper.log_debug("Cyber Vision Debug: interval is " + str(interval))
    current_utc = calendar.timegm(datetime.datetime.utcnow().timetuple())
    error_msg_prefix = "Cyber Vision Error: "

    if not global_account:
        msg = "global account not found. Please add the valid global account."
        helper.log_error(error_msg_prefix + msg)
        raise ValueError(msg)

    if start_date:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", start_date):
            msg = 'start date should be in "YYYY-MM-DDThh:mm:ssZ" format.'
            helper.log_error(error_msg_prefix + msg)
            raise ValueError(msg)

        time_pattern = "%Y-%m-%dT%H:%M:%SZ"
        start_date = calendar.timegm(time.strptime(start_date, time_pattern))

        if start_date < 0:
            msg = 'start date can not be lesser than "1970-01-01T00:00:00Z".'
            helper.log_error(error_msg_prefix + msg)
            raise ValueError(msg)

        if start_date > current_utc:
            msg = 'start date can not be greater than current UTC.'
            helper.log_error(error_msg_prefix + msg)
            raise ValueError(msg)
    pass


def collect_events(helper, ew):
    """Implement your data collection logic here."""
    try:
        input_name = helper.get_input_stanza_names()
        dc_starting_time = datetime.datetime.now()
        helper.log_info(
            "Starting data collection for input {} at {}".format(input_name, dc_starting_time))
        global_account = helper.get_arg('global_account')
        if not global_account:
            raise Exception(
                "Invalid global_account for input '{}'.".format(input_name))
        api_token = global_account.get('api_token')
        server_address = global_account.get('ip_address')
        page_size = helper.get_arg('page_size')
        verify_ssl = utils.VERIFY_SSL
        stanza_name = str(helper.get_input_stanza_names())
        current_time = int(time.time() * 1000)
        splunk_version = ver.__version__
        if not splunk_version:
            helper.log_error(
                "Cisco Cyber Vision Error: unable to fetch splunk version.")
            return
        # Fetching proxy data
        proxy_dict = helper.get_proxy()
        proxy_uri = None
        if proxy_dict:
            proxy_uri = utils.format_proxy_uri(proxy_dict)
        proxy_settings = {"http": proxy_uri, "https": proxy_uri}

        # Storing necessary data into dictionary
        config_details = {}
        config_details['server_address'] = server_address
        if not server_address.startswith("https"):
            helper.log_error(
                "Unsuccessfully terminating the data collection. Reason: Server address "
                "should start with https. Found {}".format(server_address))
            exit(1)
        host_name = server_address.split("https://")[1]
        config_details['user_agent'] = "Splunk/{}".format(splunk_version)
        config_details['stanza'] = stanza_name
        config_details['proxy_settings'] = proxy_settings
        config_details['verify_ssl'] = verify_ssl
        config_details['api_token'] = api_token
        config_details['api_version'] = "3.0"
        config_details['end_date'] = current_time
        sourcetype = "cisco:cybervision:components"
        endpoint = "/components"
        utils.get_checkpoint(helper, config_details, sourcetype, endpoint)
        start_date = config_details['start_date']
        page = 1

        while True:
            helper.log_info("--->>>> test")
            params = {"from": "946681200000", "to": current_time,
                      "sort": "lastActivity:desc", "page": page, "size": page_size}
            data = utils.request_get(
                helper, "components", config_details, params)
            #helper.log_info(f"Response data: {data}")
            if data and (page == 1):
                lastActivity = data[0]['lastActivity']
                config_details['end_date'] = lastActivity + 1
            page += 1
            additional_fields = {}
            additional_fields['host'] = host_name
            additional_fields['time_field'] = "lastActivity"
            utils.ingest_in_splunk(helper, ew, data, sourcetype,
                                   additional_fields, source="Components")
            helper.log_info(f"Request params: {params}")
            if len(data) < int(page_size):
                break
        utils.update_checkpoint(helper, config_details)
        helper.log_info(
            "Data collection process is completed for input {}".format(input_name))
        helper.log_info("foo Total time taken in data collection for input {} is {} seconds".format(
            input_name, (datetime.datetime.now() - dc_starting_time).total_seconds()))
    except Exception as e:
        helper.log_error(
            "Cisco Cyber Vision Error: while collecting components data: {}".format(e))
        helper.log_error(
            "Cisco Cyber Vision Error: Terminating the data collection unsuccessfully."
        )
        exit(1)
