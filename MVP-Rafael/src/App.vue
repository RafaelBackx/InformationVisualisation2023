<script>
import Map from './components/Map.vue'
import CountryData from './components/CountryData.vue';

export default {
  components: {
    Map,CountryData
  },
  data(){
    return {
      barData: []
    }
  },
  created(){
    this.barData = this.generateRandomData(5, 'USA')
  },
  methods: {
    changeCountry(values){
      let [name,iso] = values
      console.log(name,iso)
      // generate random data for now
      this.updateBar(this.generateRandomData(5, name))
    },    
    
    generateRandomData(n, countryName){
      let randomValues = []
      let labels = ['Earthquake','Tsunami', 'Volcano','Wild fires', 'Floods']
      for (let i=0; i< n ;i ++){
        let value = Math.floor(Math.random() * 100)
        randomValues.push(value)
      }
      return {labels: labels, datasets: [{data: randomValues, label: `Natural disasters - ${countryName}`, backgroundColor: ['#1c3a17', '#2542d1', '#db3f3f', '#e08918', '#21c6e0']}]}
    },
    
    updateBar(data){
      this.barData = data
    }

  }
}




</script>

<template>
  <div class="container">
    <Map @change-country="changeCountry"></Map>
    <CountryData :data="barData"></CountryData>
  </div>
</template>

<style scoped>
header {
  line-height: 1.5;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>
