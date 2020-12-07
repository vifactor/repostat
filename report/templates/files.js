const dataset = {{json_data}}
// Setup the chart
nv.addGraph(function() {
	var chart = nv.models.multiChart()
		.margin({left: 60, right: 60});
	chart.yAxis1.options({axisLabel: "Files"});
	chart.yAxis2.options({axisLabel: "Lines"});
	chart.yDomain1([0, dataset.maxFiles]);
	chart.yDomain2([0, dataset.maxLines]);
	chart.xAxis
		.tickFormat(function(d) { return d3.time.format('%Y-%m')(new Date(d)); })
		.options({rotateLabels: -45})

	d3.select('#chart_files svg').datum(dataset.data).call(chart);
	return chart;
});
