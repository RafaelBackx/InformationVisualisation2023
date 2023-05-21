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
            const {classes, colorscale, style, active_state, ratio_map} = context.props.hideout;  // get props from hideout
            let state = feature['properties']['ISO_1'];
            const value = ratio_map[state]  // get value the determines the color
            for (let i = 0; i < classes.length; ++i) {
                if (value > classes[i]) {
                    style.fillColor = colorscale[i];  // set the fill color according to the class
                }
            }
            if (state == active_state){
                style.weight = 5
                style.dashArray = '5'
            }else{
                style.weight = 2
                style.dashArray = ''
            }
            return style;
        },
        draw_countries: function(feature,context){
            const {classes, colorscale, style,current_year, ratio_map} = context.props.hideout;  // get props from hideout
            let country = feature['properties']['ISO_A3'];
            const year_data = ratio_map[current_year]
            let value = year_data[country]  // get value the determines the color
            if (value === undefined) {
                value = 0
            }
            for (let i = 0; i < classes.length; ++i) {
                if (value >= classes[i]) {
                    style.fillColor = colorscale[i];  // set the fill color according to the class
                }
            }
            return style;
            },
            
        }

    
});