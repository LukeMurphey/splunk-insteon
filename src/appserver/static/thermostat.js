require.config({
    paths: {
    	info_message_view: '../app/insteon/js/views/InfoMessageView'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'info_message_view', 'splunkjs/mvc/searchmanager', 'splunkjs/mvc/utils', 'splunkjs/mvc/simplexml/ready!'],
	function($, _, mvc, InfoMessageView, SearchManager, utils){
	
	    // Make the search that will determine if weather inputs exist
	    var hasWeatherInputSearch = new SearchManager({
	        "id": "weather-inputs-search",
	        "earliest_time": "-24h@h",
	        "latest_time": "now",
	        "search":'| rest /services/data/inputs/weather_info | stats count',
	        "cancelOnUnload": true,
	        "autostart": false,
	        "app": utils.getCurrentApp(),
	        "auto_cancel": 90,
	        "preview": false
	    }, {tokens: false});
	
	    var infoMessageView = new InfoMessageView({
	    	search_manager: hasWeatherInputSearch,
	    	message: 'No weather inputs exist yet; create one to compare weather data to. <a target="_blank" href="../../manager/insteon/adddata/selectsource?input_type=weather_info&modinput=1&input_mode=1">Create a weather input now.</a>',
	    	eval_function: function(searchResults){ return searchResults.rows[0][0] === "0" }
	    });
	    
	    // Update the weather info token such that a default value gets set
	    var submittedTokens = mvc.Components.get('submitted');
	    
	    var setDefaultWeatherToken = function(){
	    	if(submittedTokens.has('location')) {
	    		submittedTokens.set('_location', submittedTokens.get('location'));
	    	}
	    	else{
	    		submittedTokens.set('_location','weather_info://NoWeatherInfo');
	    	}
	    }
	    
        setDefaultWeatherToken();
	    
	    // When the location token changes...
	    submittedTokens.on('change:location', setDefaultWeatherToken);
	    
	    var submit = mvc.Components.get('submit');
        submit.on("submit", setDefaultWeatherToken);
	    
	}
);