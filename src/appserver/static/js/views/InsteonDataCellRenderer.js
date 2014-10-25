


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
    
    var InsteonDataCellRenderer = BaseCellRenderer.extend({
    	
    	 canRender: function(cell) {
    		 return $.inArray(cell.field, ["status"]) >= 0;
		 },
		 
		 render: function($td, cell) {
			 
			 // Handle ack
			 if(cell.field === "ack" && cell.value === "1" || cell.value === 1 || cell.value === "ack"){
				 $td.html('<span class="label label-success">ack</span>');
			 }
			 
			 //Handle nack
			 else if(cell.field === "ack" && cell.value === "-1" || cell.value === -1 || cell.value === "nack"){
				 $td.html('<span class="label label-success">nack</span>');
			 }
			 
			 // Handle other cases
			 else{
				$td.html("");
			 }
		 }
	});
    
    return InsteonDataCellRenderer;
});