<template>
        <Bar
      id="my-chart-id"
      :options="chartOptions"
      :data="data"
    />
</template>

<script>

import {Bar} from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

export default {
    props: ['data'], 
    components: {
        Bar
    },
    data(){
        return {
            chartOptions: {
                responsive: true
            }
        }
    }
}
</script>

<style scoped>

</style>