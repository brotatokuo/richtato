document.addEventListener("DOMContentLoaded", async () => {
    const timeseriesGraph = new TimeseriesGraph('cashFlowLineChart', '/api/timeseries-data/');
    timeseriesGraph.init();
});
