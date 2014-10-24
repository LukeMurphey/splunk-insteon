require.config({
    paths: {
    	annotate_event_view: '../app/insteon/js/views/AnnotateEventView'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'annotate_event_view', 'splunkjs/mvc/simplexml/ready!'],
	function($, _, mvc, AnnotateEventView){

	    var annotateEventView = new AnnotateEventView( {
													    	el: $('#annotate_event_dialog')
												    	});
	    
	    annotateEventView.loadParamsFromURL();
	    annotateEventView.render();
	    
	}
);