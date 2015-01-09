[insteon_plm://default]
* Configure an input for monitoring an Insteon PLM

plm_host = <value>
* The hostname or IP address of the Insteon PLM

plm_port = <value>
* The port number of the Insteon PLM (usually 9761)

no_activity_restart_interval = <value>
* How long to wait to restart the PLM connection if no modem activity is observed

[weather_info://default]
* Configure an input for obtaining weather information

woeid = <value>
* A where-on-Earth ID that indicates the location you would like to get weather information for (obtain one from http://woeid.rosselliot.co.nz/)

interval = <value>
* How often to get weather information (how many seconds in between each call)