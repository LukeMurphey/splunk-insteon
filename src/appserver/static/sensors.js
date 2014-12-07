require.config({
    paths: {
    	insteon_sensor_data_cell_renderer: '../app/insteon/js/views/InsteonSensorDataCellRenderer'
    }
});

require(['jquery','underscore','splunkjs/mvc', 'insteon_sensor_data_cell_renderer', 'splunkjs/mvc/simplexml/ready!'],
	function($, _, mvc, InsteonSensorDataCellRenderer){
	
	    var leakSensorTable = mvc.Components.get('leak_sensor_table');
	    
	    leakSensorTable.getVisualization(function(tableView){
	        tableView.table.addCellRenderer(new InsteonSensorDataCellRenderer(
	        		{
	        			'status_descriptions' : {
	        				'alert' : 'wet',
	        				'clear' : 'dry'
	        			}
	        		}
	        		));
	        tableView.table.render();
	    });
	    
	    var smokeSensorTable = mvc.Components.get('smoke_sensor_table');
	    
	    smokeSensorTable.getVisualization(function(tableView){
	        tableView.table.addCellRenderer(new InsteonSensorDataCellRenderer());
	        tableView.table.render();
	    });
	    
	}
);