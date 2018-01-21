var map;
var map_image_layer;
var map_image_bounds = [[24.0625,-125.0208],[49.9375,-66.479]];

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
function init() {
    // create map and set center and zoom level
    map = new L.map('leaflet_map');
    map.setView([39,-95],4);

    var selection;
    var selectedLayer;
    var selectedFeature;
    // create and add osm tile layer
    osm = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    });
    draw_map()
}

// get current status of a specified dropdown
function get_selection(select_id) {
    var s = document.getElementById(select_id);
    return s.options[s.selectedIndex].value;
}


function log_text(message) {
    document.getElementById("test_output").innerHTML += '<br>' + message;
}

function clear_map() {
    map.eachLayer(function (layer) {
        map.removeLayer(layer);
    });
    osm.addTo(map)
}

function draw_map() {
    //get info to display
    var map_type = get_selection("map_type_select");
    var issue_date = get_selection("issue_date_select");
    var species = get_selection("species_select");
    var phenophase = get_selection("phenophase_select");
    

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
        var image_url = 'images/'+issue_date+'/'+species+'_'+phenophase+'_'+issue_date+'_map.png';
        map_image_layer = L.imageOverlay(image_url, map_image_bounds, {opacity: 0.7});
        map_image_layer.addTo(map);
    } else {
        //construct image url
        var image_url = 'images/'+issue_date+'/'+species+'_'+phenophase+'_'+issue_date+'.png';
        log_text('setting image: ' + image_url);
        //set image
        $('#static_map').attr('src',image_url);
    }
}
