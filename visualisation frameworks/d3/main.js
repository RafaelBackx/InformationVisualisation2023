import * as d3 from 'https://unpkg.com/d3?module'

// 🤮🤮🤮🤮🤮🤮🤮

// Generate random values
let values = []
let n = 100
for (let i=0;i<n;i++){
    values.push(Math.floor(Math.random() * 10))
}

console.log(values)
let width  = 300
let barwidth = 30
let barheight = 30

// Create the graph element
var graph = d3.select('div')
                .append('svg')
                .attr('width', width)
                .attr('height', barwidth * n)
// bar element + bar number
var bar = graph.selectAll('g')
            .data(values)
            .enter()
            .append('g')
            .attr('transform' , function(d,i) {
                return `translate (0, ${i*barheight})`
            })
// create the rectangle bar chart
bar.append('rect')
            .attr('width',function(d){
                return d*20;
            })
            .attr('height', barheight-1)

bar.append("text")
.attr("x", function(d) { return (d*20); })
.attr("y", barheight / 2)
.attr("dy", ".35em")
.text(function(d) { return d; });

