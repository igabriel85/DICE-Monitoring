#Changelog
* v0.1.1 - First alpha release
* v0.1.2 - Minor alpha release
	* added support for Spark monitoring
	* modified logstash conf generation to include graphite input 
* v0.1.3 - Minor alpha release
	* added jmxtrans install to pysshCore
	* added the capability to define node roles
	* added the capability to start/stop all auxiliary components
	* added the capability to start/stop auxiliary components on specified nodes
	* updated kibana version from 4.0.2 to 4.1.2
	* enabled import export of kibana dashboard
	* added resources to controll kibana instance
	* created pid file directory for core components
	* created log file directory for core components
	* created dmon-stop script
	* enhanced queryConstructor function to enable elasticsearch date math
	* updated all Vagrant files
* v0.1.4 - Minor alpha release
	* added log export resource
	* added parallel processing of some requests (marked with _../v2/.._)
	* added new dmon-agent for controlling auxiliary monitoring components
	* added dmon-wui template to respoitory