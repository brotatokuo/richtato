let timeseriesGraph = null;

document.addEventListener("DOMContentLoaded", async () => {
    timeseriesGraph = new TimeseriesGraph('lineChart', '/get-timeseries-data/');
    const monthsDropdown = document.getElementById("monthsDropdown");
    await timeseriesGraph.initialize(monthsDropdown.value);
    monthsDropdown.addEventListener("change", async () => {
        await timeseriesGraph.setTimeRange(monthsDropdown.value);
    });
});
