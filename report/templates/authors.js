// Setup the chart
const contribution = {{contribution}}
nv.addGraph(function() {
	var chart = nv.models.pieChart()
		.x(function(d) { return d.key })
		.y(function(d) { return d.y })
		.options({
                    "padAngle": 0.01,
                    "cornerRadius": 5
                });
	chart.pie.donutLabelsOutside(true).donut(true);

	d3.select('#chart_contribution svg').datum(contribution.data).call(chart);
	return chart;
});

const lines_stats = {{lines_by_authors}}
// Setup the lines by author chart
nv.addGraph(function() {
	var chart = nv.models.lineChart()
		.useInteractiveGuideline(true);
	chart.yAxis.options({ "axisLabel": "Lines" });
	chart.xAxis
		.tickFormat(function(d) { return d3.time.format('%Y-%m')(new Date(d)); })
		.options({ "rotateLabels": -45 })

	d3.select('#chart_loc svg').datum(lines_stats.data).call(chart);
	return chart;
});

const commit_stats = {{commits_by_authors}}
// Setup the commits-by-author chart
nv.addGraph(function() {
	var chart = nv.models.lineChart()
		.x(function(d) { return d[0] })
		.y(function(d) { return d[1] })
		.useInteractiveGuideline(true);
	chart.yAxis.options({ "axisLabel": "Commits" });
	chart.xAxis
		.tickFormat(function(d) { return d3.time.format('%Y-%m')(new Date(d)); })
		.options({ "rotateLabels": -45 })

	d3.select('#chart_commits svg').datum(commit_stats.data).call(chart);
	return chart;
});

// Setup the streamgraph
nv.addGraph(function() {
	var chart = nv.models.stackedAreaChart()
		.x(function(d) { return d[0] })
		.y(function(d) { return d[2] })
		.options({
		        "useInteractiveGuideline": true,
		        "style": "stream-center",
                "showControls": false,
                "showLegend": false,
                });
	chart.yAxis.options({ "axisLabel": "Commits" });
	chart.xAxis
		.tickFormat(function(d) { return d3.time.format('%Y-%m')(new Date(d)); })
		.options({ "rotateLabels": -45 })

	d3.select('#chart_steam svg').datum(commit_stats.data).call(chart);
	return chart;
});

const domains = {{domains}}
// Setup the chart
nv.addGraph(function() {
	var chart = nv.models.pieChart()
		.x(function(d) { return d.key })
		.y(function(d) { return d.y })
		.options({
                "padAngle": 0.01,
                "cornerRadius": 5
            });
	chart.pie.donutLabelsOutside(true).donut(true);

	d3.select('#chart_domains svg').datum(domains.data).call(chart);
	return chart;
});
