document.addEventListener("DOMContentLoaded", async () => {
    const timeseriesGraph = new TimeseriesGraph('lineChart', '/api/timeseries-data/');
    timeseriesGraph.init();
});
