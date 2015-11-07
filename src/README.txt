================================================
Overview
================================================

This app provides a mechanism for getting Insteon data into Splunk and reporting on it.



================================================
Configuring Splunk
================================================

This app exposes a new input type that can be configured in the Splunk Manager. To configure it, create a new input in the Manager under Data inputs � Insteon PLM.



================================================
Getting Support
================================================

Go to the following website if you need support:

     http://answers.splunk.com/answers/app/2694

You can access the source-code and get technical details about the app at:

     https://github.com/LukeMurphey/splunk-insteon



================================================
Change History
================================================

+---------+------------------------------------------------------------------------------------------------------------------+
| Version |  Changes                                                                                                         |
+---------+------------------------------------------------------------------------------------------------------------------+
| 0.5     | Initial release                                                                                                  |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.6     | Added link to Splunk answers in README                                                                           |
|         | Fixed search "Leak Sensor Failed to Check In"                                                                    |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.7     | Fixing the issue where the source type could not be set                                                          |
|---------|------------------------------------------------------------------------------------------------------------------|
| 0.8     | Fixing Synchrolinc dashboard that sometimes returned no data                                                     |
+---------+------------------------------------------------------------------------------------------------------------------+
