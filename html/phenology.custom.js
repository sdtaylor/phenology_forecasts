
//leaflet map stuff
//var map;
//var map_image_layer;
//var map_image_bounds = [[24.0625,-125.0208],[49.9375,-66.479]];
var debug=false

//information which populates the dropdowns
var image_metadata;
$.getJSON('image_metadata.json', 
        function(json) {image_metadata=json} );
          
// diplay='block' mean display normally, display='none' means hide it
function toggle_maps() {
    var L_map = document.getElementById("leaflet_map");
    var S_map = document.getElementById("static_map");
  
    if (L_map.style.display === "none") {
        L_map.style.display = "block";
    } else {
        L_map.style.display = "none";
    }
    
    if (S_map.style.display === "none") {
        S_map.style.display = "block";
    } else {
        S_map.style.display = "none";
    }
    
    document.getElementById("test_output").innerHTML += '<br>type changed';
} 

function current_map_type() {
    var L_map = document.getElementById("leaflet_map");
    if (L_map.style.display === "none"){
        var map_type='static';
    } else {
        var map_type='interactive';
    }
    return map_type;
}

var osm;
function init_page() {
    log_text("initializing")
    $.getJSON('image_metadata.json', 
          function(json) {
              load_menus(json);
              draw_map();} );

    //leaflet map stuff
    // create map and set center and zoom level
    //map = new L.map('leaflet_map');
    //map.setView([39,-95],4);

    //var selection;
    //var selectedLayer;
    //var selectedFeature;
    //// create and add osm tile layer
    //osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    //  maxZoom: 19,
    //  attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    //});

}

// get current status of a specified dropdown
function get_selection(select_id) {
    var s = document.getElementById(select_id);
    return s.options[s.selectedIndex].value;
}


function log_text(message) {
    if (debug){
        document.getElementById("log_output").innerHTML += '<br>' + message;
    }
}

//This updates the text info below all the menus
function update_forecast_info(message) {
    document.getElementById("forecast_info").innerHTML = '<b>' + message + '</b>';
}

function clear_map() {
    map.eachLayer(function (layer) {
        map.removeLayer(layer);
    });
    osm.addTo(map)
}

function draw_map() {
    //get info to display
    log_text("drawing map")
    var map_type = get_selection("map_type_select");
    var issue_date = get_selection("issue_date_select");
    var species = get_selection("species_select");
    var phenophase = get_selection("phenophase_select");
    
    log_text("#######################")
    log_text("selected map_type: "+map_type);
    log_text("selected issue_date: "+issue_date);
    log_text("selected species: "+species);
    log_text("selected phenophase: "+phenophase);


    //var current_type = current_map_type()
    if (current_map_type() == map_type) {
        log_text("map types equal");
    } else {
        log_text("map types dont equal");
        toggle_maps();
    }
    var prior_image_layer;
    var current_image_layer;
    if (map_type=='interactive') {
        clear_map();
        var image_filename = species+'_'+phenophase+'_'+issue_date+'_map.png';
        var image_url = 'images/'+issue_date+'/'+image_filename;
        
        if (image_metadata.available_images.indexOf(image_filename) == -1){
            update_forecast_info("Forecast not available");
            log_text("map not available: "+image_filename);
        } else {
            update_forecast_info("");
            log_text('setting image: ' + image_filename);
        }
        
        map_image_layer = L.imageOverlay(image_url, map_image_bounds, {opacity: 0.7});
        map_image_layer.addTo(map);
    } else {
        //construct image url
        var image_filename_prediction = species+'_'+phenophase+'_'+issue_date+'_prediction.png';
        var image_url_prediction = 'images/'+issue_date+'/'+image_filename_prediction;
        
        var image_filename_uncertainty = species+'_'+phenophase+'_'+issue_date+'_uncertainty.png';
        var image_url_uncertainty = 'images/'+issue_date+'/'+image_filename_uncertainty;
        
        if (image_metadata.available_images.indexOf(image_filename_prediction) == -1){
            update_forecast_info("Forecast not available");
            log_text("image not available: "+image_filename);
        } else {
            update_forecast_info("");
            log_text('setting image: ' + image_url);
        }
        //set image
        $('#static_map_prediction').attr('src',image_url_prediction);
        $('#static_map_uncertainty').attr('src',image_url_uncertainty);
    }
}

function load_menus(image_metadata){
    log_text("populating issue dates")
    populate_drop_down('issue_date_select', image_metadata.available_issue_dates);   
    log_text("populating species")
    populate_drop_down('species_select', image_metadata.available_species);   
    log_text("populating phenophase")
    populate_drop_down('phenophase_select', image_metadata.available_phenophase);   
}

function populate_drop_down(dropdown_name, items) {
    var dropdown_menu = document.getElementById(dropdown_name);
    
    for (var i=0; i<items.length; i++) {
        var item_i = items[i];

        var dropdown_item = document.createElement("option");
        dropdown_item.textContent = item_i.display_text;
        dropdown_item.value = item_i.value;
        
        dropdown_menu.appendChild(dropdown_item);
        if (item_i.default==1) {
            dropdown_menu.selectedIndex=i;
        }
    }
}

