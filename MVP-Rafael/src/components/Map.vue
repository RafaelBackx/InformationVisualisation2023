
<template>
  <div>
    <div id="mapid" class=""></div>
  </div>
</template>

<script>
import * as countries from '../../countries.geo.json'
import leaflet from "leaflet";


export default {
  components: {
  },
  data() {
    return {
      zoom: 2,
      map: undefined,
      geoJson: undefined,
      markers: []
    }
  },
  mounted(){

    this.map = leaflet.map("mapid", {
      maxBounds: [[-90,-180],   [90,180]],
      maxBoundsViscosity: 1.0,
      minZoom: 1,
      maxZoom: 19,
      bounceAtZoomLimits: true
    }).setView([42.5145, -83.0147], 9)

    leaflet.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
      maxZoom: 19,
    }).addTo(this.map)
    this.geojson = leaflet.geoJson(countries,{
      onEachFeature: this.mapEventHandler
    }).addTo(this.map)
  },
  methods: {
    generateRandomCoord(north,east,south,west){
      let width = east - west
      let height = north - south

      let x = Math.floor(Math.random() * width)
      let y = Math.floor(Math.random() * height)

      return [south + y, west + x]
    },
    mapEventHandler(feature, layer){
      layer.on({
        mouseover: this.mapOnMouseOver,
        mouseout: this.mapOnMouseOut,
        click: this.mapOnClick
      })
    },
    mapOnMouseOver(event){
      let layer = event.target;
      layer.setStyle({
        weight: 5,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.7
      })
      layer.bringToFront()
    },
    mapOnMouseOut(event){
      this.geojson.resetStyle(event.target)
    },
    mapOnClick(event){

      let myIcon = L.icon({ 
        iconUrl: '/src/assets/marker.png',
        iconSize: [32, 32],
      });

      let bounds = event.target.getBounds() 
      let west = bounds.getWest()
      let east = bounds.getEast()
      let north = bounds.getNorth()
      let south = bounds.getSouth()

      for (let marker of this.markers){
        this.map.removeLayer(marker)
      }

      for (let i = 0; i<5; i++){
        let point = this.generateRandomCoord(north,east,south,west)
        let marker = leaflet.marker(point, {icon: myIcon}).on('click', this.markerClick).addTo(this.map)
        this.markers.push(marker)
      }



      console.log(north,east,south,west)
      this.map.fitBounds(bounds)
      let country_iso = event.target.feature.id
      let country_name = event.target.feature.properties.name
      console.log(`${country_name} - ${country_iso}`)
      this.$emit("changeCountry",[country_name,country_iso])
    },
    markerClick(marker){
      console.log(marker.containerPoint)
    }
  }
}

</script>

<style scoped>
#mapid{
  width: 50vw;
  height: 50vh;
}
</style>
