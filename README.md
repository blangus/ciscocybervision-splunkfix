# ciscocybervision-splunkfix

The latest version of the Cisco Cybervision Add on for Splunk is buggy and doesn't work with vague error messages.

Managed to fix the bugs and patched the latest version of the addon. Removed the proxy function which didn't work and added extra logging to server_validation.

Hardcoded the from date in activities and components to 2000-01-01. Because of a bug in the addon it doesn't get the correct start date from the GUI.

-----

Background: Splunk in Docker self hosted

First proxy error
Tried different things squid proxy etc, at the end disabled
```TA_cisco_cybervision_server_validation.py:107```

Second ssl issue
found with extra logging -> error due to self signed cert
response logging: ```TA_cisco_cybervision_server_validation.py:161```
disbled ssl validation: ```TA_cisco_cybervision_server_validation.py:128``` 

Third: no data for components and activities 
manually checked api with postman, data can be found.

Added extra logging to see how the request is sent
```input_module_cybervision_components.py:116``` for response
```input_module_cybervision_components.py:126``` for how request looks like

result; the from date is not correctly taken from gui, the date is current time
fixed by hardcoding 1-1-2000 (unix time)
```input_module_cybervision_components.py:112```

