# ciscocybervision-splunkfix

The latest version of the Cisco Cybervision Add on for Splunk is buggy and doesn't work with vague error messages.

Managed to fix the bugs and patched the latest version of the addon. Removed the proxy function which didn't work and added extra logging to server_validation.

Hardcoded the from date in activities and components to 2000-01-01. Because of a bug in the addon it doesn't get the correct start date from the GUI.
