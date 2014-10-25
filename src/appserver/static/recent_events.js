require.config({
    paths: {
    	annotate_events_cell_renderer: '../app/insteon/js/views/AnnotateEventCellRenderer',
    	insteon_data_cell_renderer: '../app/insteon/js/views/InsteonDataCellRenderer',
    	annotate_event_view: '../app/insteon/js/views/AnnotateEventView'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'annotate_events_cell_renderer', 'insteon_data_cell_renderer','annotate_event_view', 'splunkjs/mvc/simplexml/ready!'],
	function($, _, mvc, AnnotateEventCellRenderer, InsteonDataCellRenderer, AnnotateEventView){
	
	    var statusTable = mvc.Components.get('recent_activity_table');
	    
	    // Make the location to attach the dialog code to
	    $('<div id="modal_annotation_dialog"></div>').appendTo($('body'));
	    
	    var annotateEventView = new AnnotateEventView({ el: $('#modal_annotation_dialog') });
	    
	    statusTable.getVisualization(function(tableView){
	        tableView.table.addCellRenderer(new AnnotateEventCellRenderer({'annotate_event_view' : annotateEventView}));
	        tableView.table.addCellRenderer(new InsteonDataCellRenderer());
	        tableView.table.render();
	    });
	    
	    
	    
	}
);