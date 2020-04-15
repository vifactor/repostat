const recent_activity = {{recent_activity}}

// Setup the chart
nv.addGraph(function() {
	var chart = nv.models.historicalBarChart().options(recent_activity.config);
	chart.yAxis.options(recent_activity.yAxis);
	chart.xAxis.options(recent_activity.xAxis);
	d3.select('#chart_activity svg').datum(recent_activity.data).call(chart);
	return chart;
});

const commits_by_year = {{commits_by_year}}

// Setup the chart
nv.addGraph(function() {
	var chart = nv.models.historicalBarChart().options(commits_by_year.config);
	chart.xAxis.options(commits_by_year.xAxis);
	chart.yAxis.options(commits_by_year.yAxis);
	d3.select('#chart_commits_year svg').datum(commits_by_year.data).call(chart);
	return chart;
});

const commits_by_month = {{commits_by_month}}

// Setup the chart
nv.addGraph(function() {
	var chart = nv.models.historicalBarChart().options(commits_by_month.config);

	chart.yAxis.options(commits_by_month.yAxis);
	chart.xAxis.options(commits_by_month.xAxis);
	chart.xAxis
		.tickFormat(function(x) {
			const month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
			return month[x];
		});

	d3.select('#chart_commits_month svg').datum(commits_by_month.data).call(chart);
	return chart;
});
