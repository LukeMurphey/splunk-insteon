


/**
 * This cell renderer adds a dialog for annotating events to table cells.
 */
define(function(require, exports, module) {
	
    // Load dependencies
    var _ = require('underscore');
    var mvc = require('splunkjs/mvc');
    var $ = require('jquery');
    var AnnotateEventView = require('annotate_event_view');
    
    var BaseCellRenderer = require('views/shared/results_table/renderers/BaseCellRenderer');
    
    var AnnotateEventCellRenderer = BaseCellRenderer.extend({
    	
	   	 defaults: {
	         annotate_event_view: null
		 },
		 
	     initialize: function() {
	         
			 args = _.extend({}, this.defaults);
	
			 for( var c = 0; c < arguments.length; c++){
			 	args = _.extend(args, arguments[c]);
			 }
	
	         // Get the arguments
	         this.annotate_event_view = args.annotate_event_view;
	     },
	     
    	 canRender: function(cell) {
    		 return $.inArray(cell.field, ["options"]) >= 0;
		 },
		 
		 openForm: function(command, link_group, from_device, to_device){
			
			 if( this.annotate_event_view === null ){
				 alert("No annotation view available");
			 }
			 else{
				 this.annotate_event_view.showModal(command, link_group, from_device, to_device);
			 }
		 },
		 
		 render: function($td, cell) {
			 
			// If a value was provided, then 
			if( cell.value !== null && cell.value !== undefined && cell.value.length > 0){
				
				// Parse the value
				var parse_command_re = /^([0-9]*)[:]([0-9]*)[:]([a-f0-9.]*)[:]([a-f0-9.]*)$/i;
				
				var found = cell.value.match(parse_command_re);
				var command = found[1];
				var link_group = found[2];
				var from_device = found[3];
				var to_device = found[4];
				
				// Render the annotation with the link
				$td.html(_.template('<label style="float:left"><a href="#"><i style="margin-right: 2px;" class="icon-pencil"></i>Annotate</a></label>', {
				    	 value: cell.value,
				    	 field: cell.field
				}));
				
				// Setup a click handler to open the form
				$td.click(function(event){
					event.stopPropagation();
					this.openForm(command, link_group, from_device, to_device);
				}.bind(this));
				
			}
			else{
				$td.html("");
			}
		 }
	});
    
    return AnnotateEventCellRenderer;
});