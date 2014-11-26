


/**
 * This cell renderer adds a dialog for annotating events to table cells.
 */
define(function(require, exports, module) {
	
    // Load dependencies
    var _ = require('underscore');
    var mvc = require('splunkjs/mvc');
    var $ = require('jquery');
    
    var BaseCellRenderer = require('views/shared/results_table/renderers/BaseCellRenderer');
    
    var InsteonDataCellRenderer = BaseCellRenderer.extend({
    	
    	 canRender: function(cell) {
    		 return $.inArray(cell.field, ["wet", "status", "last_seen"]) >= 0;
		 },
		 
		 render: function($td, cell) {
			 
			 // Handle wet state
			 if(cell.field === "status" && cell.value === "1" || cell.value === 1 || cell.value === "wet"){
				 $td.html('<span style="display: inline-block; ' + 
						 'padding-left: 20px;' + 
						 'width: 20px;' + 
						 'height: 20px;' +
						 'background-repeat: no-repeat;' +
						 'background-image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAACXBIWXMAAAsTAAALEwEAmpwYAAAB00lEQVQ4jWP8//8/AzUBEzGK7NYxpFgvZcgiRi0jMS6U9u58/f/vb45nO2r4GRgY/lHkwmMMDPL/fn8T+f/vN88iBgYVQuoJGlgwjSEUxp7Yh2CTayD7812T02GclwcnpDAwMHCQbaBB56+qP9/ewL359/t7Bb2mtw1kGbiBgUH51b7OUnTxN0enFsxiYNDApQ9XLDMqRi/f/+P1DXtskuxCiicfrEiwYsAS41hd6LiDIQ6XYQwMDAw/3903t13NkEKsC9mlfbof/Pv1RQKXgQwMDAxMrFxvnm4tl2dgYPiG14Xelxh8CBnGwMDA8O/3NxHXQwwBGBahCzze+N6EkGEw8HznAzOCBv75+poXnyHccuYbhU0TJzIwMDD8+f6eh6CB/Opqt3AZxsTC8X7lHK88mQCFYwwMDAy8yoY3CRo4O5FhPSMj8090cR4F67VTt1WaGjMwfLjaOrmVgYHpd0M2w1qCBuowMDyW8q5rQBcXNnc7vOoPg5Jc8Iyjf769UZFwqW71ZmC4h64OZ/FlMoGh8tn2xob///+xobnht6Rrbcu5UqZmBgYGDM14y8MNDAzKDe3fEr4+OqHOwMDAwCVjeru4mndhHAMDznAmqoAlBQAAljKnHiVeobMAAAAASUVORK5CYII=);' +
				 		'">wet</span>');
				 //background-color: #FFE7CE;
				 $td.html('<span style="float: right; color: #d85d3c; font-weight: bold"><i style="font-size: 14pt;" class="icon-alert icon-warning"></i> wet</span>');
			 }
			 
			 //Handle dry state
			 else if(cell.field === "status" && cell.value === "0" || cell.value === 0 || cell.value === "dry"){
				 $td.html('<span style="display: inline-block; ' + 
						 'padding-left: 20px;' + 
						 'width: 20px;' + 
						 'height: 20px;' +
				 		'">dry</span>');
				 
				 $td.html('<span style="float: right; color: #65a637; font-weight: bold"><i style="font-size: 14pt;" class="icon-box-checked"></i> dry </span>');
				 
			 }
			 
			 //Handle last_seen
			 else if(cell.field === "last_seen" && cell.value !== null && cell.value !== undefined){
				 
				 // If the sensor was last_seen "never", then it has not checked in yet
				 if(cell.value == "never"){
					 $td.html('<span style="color: #fac51c; font-weight: bold"><i style="font-size: 14pt;" class="icon-question-circle"></i> ' + cell.value + '</span>');
				 }
				 
				 // If the cell has an exclamation mark, then the sensor has checked in too long ago
			     else if(cell.value.indexOf("!") >= 0){
					 $td.html('<span style="color: #d85d3c; font-weight: bold"><i style="font-size: 14pt;" class="icon-alert icon-warning"></i> ' + cell.value + '</span>');
				 }
				 
				 // Otherwise, the sensor is good
				 else{
					 $td.html('<span style="color: #65a637; font-weight: bold"><i style="font-size: 14pt;" class="icon-box-checked"></i> ' + cell.value + '</span>');
				 }
			 }
			 
			 //Handle unknown state
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