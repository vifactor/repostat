const dataset = {{json_data}}

// Setup the chart
nv.addGraph(function() {
	var chart = nv.models.multiChart()
		.margin({left: 60, right: 60});
	chart.yAxis1.options(dataset.yAxis1);
	chart.yAxis2.options(dataset.yAxis2);
	chart.xAxis
		.tickFormat(function(d) { return d3.time.format('%Y-%m')(new Date(d)); })
		.options(dataset.xAxis)

	d3.select('#chart_files svg').datum(dataset.data).call(chart);
	return chart;
});
