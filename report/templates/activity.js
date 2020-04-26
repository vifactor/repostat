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

nv.addGraph(function() {
  var chart = nv.models.discreteBarChart()
      .x(function(d) { return d.label })    //Specify the data accessors.
      .y(function(d) { return d.value })
      .color(["#9400D3"])
      .staggerLabels(true)    //Too many bars and not enough room? Try staggering labels.
      .showValues(true)       //...instead, show the bar value right on top of each bar.
      ;
  chart.yAxis.options({"axisLabel": "Commits count"})

  d3.select('#review_time_chart svg')
      .datum([{
        key: "Cumulative Return",
        color: "#9400D3",
        values: {{ review_duration }}
       }
  ]).call(chart);

  nv.utils.windowResize(chart.update);

  return chart;
});


