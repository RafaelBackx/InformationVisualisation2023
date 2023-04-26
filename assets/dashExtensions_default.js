window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        draw_marker: function(feature, latlng) {
            const marker_sources = {
                "Geophysical": "https://img.icons8.com/ios-filled/50/C95B20/mountain.png",
                "Meteorological": "https://img.icons8.com/material-sharp/24/AbA4A4/cloud.png",
                "Hydrological": "https://img.icons8.com/material-sharp/24/0EB7E3/blur.png",
                "Climatological": "https://img.icons8.com/material-rounded/24/FFEE00/sun--v1.png"
            }
            const event_type = feature["properties"]["Disaster Subgroup"]
            const event = L.icon({
                iconUrl: `${marker_sources[event_type]}`,
                iconSize: [16, 16]
            });
            return L.marker(latlng, {icon: event})
        },
        draw_polygon: function(feature,context){
            console.log('hello from draw_polygon')
            let state = feature['properties']['ISO_1'];
            console.log(state);
            let colour_map = context.props.hideout;
            if (colour_map != undefined){
                let colour = colour_map[state]
                console.log(colour);
                return {weight: 2, color: colour, dashArray: ''};
            }
        }
    }
});