define([
    "underscore",
    "backbone",
    "splunkjs/mvc",
    "jquery",
    "splunkjs/mvc/simplesplunkview",
    "splunkjs/mvc/searchmanager",
    "splunkjs/mvc/simpleform/input/text",
    "splunkjs/mvc/utils"
], function(
    _,
    Backbone,
    mvc,
    $,
    SimpleSplunkView,
    SearchManager,
    TextInput,
    utils
) { 
    // Define the custom view class
    var AnnotateEventView = SimpleSplunkView.extend({
        className: "AnnotateEventView",
        apps: null,
        
        /**
         * Setup the defaults
         */
        defaults: {
        	show_modal     : false,
        	command        : null,
        	device         : null,
        	all_link_group : null
        },
        
        /**
         * Initialize the class
         */
        initialize: function() {
        	
            // Apply the defaults
            this.options = _.extend({}, this.defaults, this.options);
            
            options = this.options || {};
            
            this.show_modal = options.show_modal;
            this.command = options.command;
            this.device = options.device;
            this.all_link_group = options.all_link_group;
            
            this.already_rendered = false;
        },
        
        /**
         * Setup event handlers
         */
        events: {
            "click #save": "save"
        },

        /**
         * Get the parameter with the given name.
         */
        getParameterByName: function(name) {
            name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
            
            var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
                results = regex.exec(location.search);
            
            return results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
        },
        
        /**
         * Show a dialog message.
         */
        showDialog: function(status, message){
        	
        	$("#message_dialog", this.$el).html('<div class="alert alert-' + status + '">' +
                    							'<i class="icon-alert"></i>' + 
                    							message +
                    							'</div>');
        	
        	$("#message_dialog", this.$el).show();
        	$("#event_annotation_form", this.$el).hide();
        	$(".controls", this.$el).hide();
        	
        },
        
        /**
         * Hide the dialog.
         */
        hideDialog: function(){
        	$("#message_dialog", this.$el).hide();
        	$("#event_annotation_form", this.$el).show();
        	$(".controls", this.$el).show();
        },
        
        /**
         * Determine if the provided parameters are valid.
         */
        areParametersValid: function(){
        	
        	// Validate the command
        	if( !/^([0-9a-f])?[0-9a-f]$/gi.test(this.command)){
        		return "Command is not valid";
        	}
        	
        	// Validate the device
        	else if( !/^([0-9a-f]{2,2}.){2,2}[0-9a-f]{2,2}$/gi.test(this.device)){
        		return "Device is not valid";
        	}
        	
        	// Validate the all-link group
        	if( !/^[0-9a-f]+$/gi.test(this.all_link_group)){
        		return "All-link group is not valid";
        	}

        	return true;
        },
        
        /**
         * Load the parameters to initialize this class from the URL
         */
        loadParamsFromURL: function(){
        	
        	this.all_link_group = this.getParameterByName("all_link_group");
        	this.command = this.getParameterByName("command");
        	this.device = this.getParameterByName("device");
        	
        },
        
        /**
         * Get the controls that are necessary for the non-modal form.
         */
        getControls: function(){
        	return '<div class="controls" style="margin-top: 12px"><a href="#" class="btn btn-primary" id="save" style="display: inline;">Save</a></div>';
        },
        
        /**
         * Get the template for a modal
         */
        getModalTemplate: function(title, body){
        	
        	return '<div tabindex="-1" id="annotate-event-modal" class="modal fade in hide">' +
					    '<div class="modal-header">' +
					        '<button type="button" class="close btn-dialog-close" data-dismiss="modal">x</button>' +
					        '<h3 class="text-dialog-title">' + title + '</h3>' +
					    '</div>' +
					    '<div class="modal-body form form-horizontal modal-body-scrolling">' +
					    	body +
					    '</div>' +
					    '<div class="modal-footer">' +
					        '<a href="#" class="btn btn-dialog-cancel" data-dismiss="modal" style="display: inline;">Close</a>' +
					        '<a href="#" class="btn btn-primary" id="save" style="display: inline;">Save</a>' +
					   ' </div>' +
					'</div>'
        },
        
        /**
         * Make a template snippet for holding an input.
         */
        makeInputTemplate: function(label, id, helpblock){
        	
        	return '<div id="' + id + '-control-group" class="control-group">' +
                	'	<label class="control-label">' + label + '</label>' +
                	'		<div class="controls">' + 
    	            '			<div style="display: inline-block;" class="input" id="' + id + '" />' +
    	            '			<span class="hide help-inline"></span>' + 
    	            '			<span class="help-block"> ' + helpblock + '</span>' +
    	            '		</div>' +
    	            '</div>';
        	
        },
        
        /**
         * Get the input template.
         */
        getInputTemplate: function(){
        	
        	return  '<div id="message_dialog"></div>' + 
        			'<span id="event_annotation_form">' + 
        			'<div style="margin-bottom: 32px">Describe this event in order to make it easier to understand the activity (e.g. "garage opening/closing", "TV on", etc.).</div>' +
        			'<div class="input" id="description-input">' +
                		'<label>Description</label>' +
                	'</div>' + 
                	'</span>';
        
        },
        
        /**
         * Start the process of retrieving the current annotation.
         */
        setupAnnotationSearch: function(){
        	
            // Make the search that will retrieve the current value            
            var retrieveAnnotationSearch = new SearchManager({
                "id": "get-annotation-search",
                "earliest_time": "-24h@h",
                "latest_time": "now",
                "search":'`get_all_link_group_annotation($command$, $all_link_group$, $device$)`',
                "cancelOnUnload": true,
                "autostart": false,
                "app": utils.getCurrentApp(),
                "auto_cancel": 90,
                "preview": false
            }, {tokens: true, tokenNamespace: "insteon_annotations"});
            
            
            retrieveAnnotationSearch.on('search:failed', function() {
                console.log("Get annotation search failed");
                this.showLoading(false);
            }.bind(this));
            
            retrieveAnnotationSearch.on("search:start", function() {
                console.log("Get annotation search started");
                this.showLoading();
            }.bind(this));
            
            retrieveAnnotationSearch.on("search:done", function() {
                console.log("Get annotation search completed");
            }.bind(this));
            
            // Process the results
            var annotationResults = retrieveAnnotationSearch.data("results");
            
            annotationResults.on("data", function() {
                
            	console.log("Existing annotation found: " + annotationResults.data().rows[0][3]);
            	mvc.Components.getInstance('description-input').val(annotationResults.data().rows[0][3]);
            	this.showLoading(false);
            }.bind(this));
        },
        
        /**
         * Setup a search to persist the results.
         */
        setupAnnotationPersistenceSearch: function(){
        	
            var updateLookupSearch = new SearchManager({
                "id": "update-annotations-search",
                "earliest_time": "-2m@m",
                "latest_time": "now",
                "search":'`update_all_link_group_annotation($command$, $all_link_group$, $device$, $annotation$)`',
                "cancelOnUnload": true,
                "autostart":false,
                "app": utils.getCurrentApp(),
                "auto_cancel": 90,
                "preview": false
            }, {tokens: true, tokenNamespace: "insteon_annotations"});
            
            updateLookupSearch.on("search:start", function() {
                console.log("Lookup update search started");
                this.showSaving(true);
            }.bind(this));
            
            updateLookupSearch.on("search:done", function() {
                console.log("Lookup update search completed");
                this.showSaving(false);
                
                if( this.show_modal ){
                	$("#annotate-event-modal", this.$el).modal('hide');
                }
                else{
                	this.showDialog('info', 'Annotation successfully saved');
                }
            }.bind(this));
            
            updateLookupSearch.on('search:failed', function(properties) {
            	this.showSaving(false);
                console.log("Lookup update search failed: ", properties);
                this.showDialog('error', 'Annotation could not be saved');
            }.bind(this));
        },
        
        /**
         * Render the view
         */
        render: function() {
            
        	// Stop if the view was already rendered
        	if( !this.already_rendered ){
	        	
	        	var html = "";
	        	
	        	// Show the modal version of the form
	        	if( this.show_modal ){
	        		html = this.getModalTemplate("Event Annotation", this.getInputTemplate());
	        	}
	        	
	        	// Show the non-modal version
	        	else{
	        		html = this.getInputTemplate() + this.getControls();
	        	}
	        	
	        	// Set the HTML
	        	this.$el.html(html);
	        	
	        	// Make the input widget
	        	var description_input = new TextInput({
	                "id": "description-input",
	                "searchWhenChanged": false,
	                "el": $('#description-input', this.$el)
	            }, {tokens: true}).render();
	        	
	        	/*
	        	description_input.on("change", function(newValue) {
	            	this.validate();
	            }.bind(this));
	            */
	            this.setupAnnotationSearch();
	            this.setupAnnotationPersistenceSearch();
	            
	        	this.already_rendered = true;
        	}
        	
        	// Validate the parameters
        	var params_valid = this.areParametersValid();
        	
        	if( params_valid !== true ){
        		this.showDialog('error', params_valid);
        	}
        	else{
        		
	        	this.hideDialog();
	        	this.showLoading();
	        	mvc.Components.getInstance('description-input').val("");
	        	
	        	setTimeout( function(){
					            // Start the search for getting the current annotation
					            var tokens = mvc.Components.getInstance('insteon_annotations', {create: true});
					            tokens.set("command", this.command);
					            tokens.set("all_link_group", this.all_link_group);
					            tokens.set("device", this.device);
					            
					        	mvc.Components.getInstance('get-annotation-search').startSearch();
				        	}.bind(this),
	        	500);
        	}
        	
            return this;
        },
        
        /**
         * Show the form as a dialog
         */
        showModal: function(command, all_link_group, device){
        	this.command = command;
        	this.all_link_group = all_link_group;
        	this.device = device;
        	
        	this.show_modal = true;
        	
        	this.render();
        	$("#annotate-event-modal", this.$el).modal();
        },
        
        /**
         * Change the UI to show that the dialog is saving.
         */
        showSaving: function(isSaving){
        	
        	if( typeof isSaving === 'undefined'){
        		isSaving = true;
        	}
        	
        	if( isSaving ){
        		$('#save', this.$el).prop('disabled', false);
            	$('#save', this.$e).addClass('disabled');
        	}
        	else{
        		$('#save', this.$el).prop('disabled', true);
            	$('#save', this.$e).removeClass('disabled');
        	}
        },
        
        /**
         * Change the UI to show that the dialog is loading.
         */
        showLoading: function(isLoading){
        	
        	if( typeof isLoading === 'undefined'){
        		isLoading = true;
        	}
        	
        	$('input', mvc.Components.getInstance('description-input').$el).prop('disabled', isLoading);
        	
        	$('#save', this.$el).prop('disabled', isLoading);
        	
        	if( isLoading ){
        		$('#save', this.$e).addClass('disabled');
        	}
        	else{
        		$('#save', this.$e).removeClass('disabled');
        	}
        },
        
        /**
         * Save the annotation
         */
        save: function() {
        	
        	this.showSaving();
        	
        	setTimeout( function(){
	            var annotation = mvc.Components.getInstance('description-input').val();
	            
	            // Start the search for getting the current annotation
	            var tokens = mvc.Components.getInstance('insteon_annotations', {create: true});
	            tokens.set("command", this.command);
	            tokens.set("all_link_group", this.all_link_group);
	            tokens.set("device", this.device);
	            tokens.set("annotation", annotation);
	            
	        	mvc.Components.getInstance('update-annotations-search').startSearch();
        	}.bind(this),
        	500);
        },
        

    });
    
    return AnnotateEventView;
});
