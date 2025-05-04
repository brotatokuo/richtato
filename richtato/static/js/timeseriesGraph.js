class TimeseriesGraph {
  constructor(canvasId, endpointBaseUrl) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.endpointBaseUrl = endpointBaseUrl;
    this.chart = null;
  }

  /**
   * Initialize the chart with a default time range
   * @param {string} defaultRange - The default time range to use
   */
  async init() {
    await this.updateChart();
  }

  /**
   * Fetches data from the endpoint and updates the chart
   */
  async updateChart() {
    try {
      const data = await this.fetchData();
      if (this.chart) {
        this.chart.destroy();
      }
      this.createChart(data);
    } catch (error) {
      console.error("Error updating chart:", error);
    }
  }

  /**
   * Fetches time series data from the endpoint
   * @returns {Object} Chart data from the API
   */
  async fetchData() {
    const response = await fetch(this.endpointBaseUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const chartData = await response.json();
    console.log("Fetched chart data:", chartData);
    return chartData;
  }

  /**
   * Creates the Chart.js chart with the provided data
   * @param {Object} chartData - Data to display in the chart
   */
  createChart(chartData) {
    const textColor =
      getComputedStyle(document.documentElement)
        .getPropertyValue("--text-color")
        .trim() || "#fff";

    this.chart = new Chart(this.ctx, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: chartData.datasets.map((dataset) => ({
          label: dataset.label,
          data: dataset.data,
          backgroundColor: dataset.borderColor,
          borderColor: dataset.borderColor,
          borderWidth: dataset.borderWidth || 2,
          fill: dataset.fill !== undefined ? dataset.fill : false,
          tension: dataset.tension !== undefined ? dataset.tension : 0.1,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              color: textColor,
            },
            grid: {
              color: "rgba(255, 255, 255, 0.2)",
            },
          },
          y: {
            beginAtZero: true,
            ticks: {
              color: textColor,
              callback: function (value) {
                const roundedValue = Math.round(value);
                return new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0,
                }).format(roundedValue);
              },
            },
            grid: {
              color: "rgba(255, 255, 255, 0.2)",
            },
          },
        },
        plugins: {
          legend: {
            labels: {
              color: textColor,
            },
            onClick: this.handleLegendClick.bind(this),
          },
          zoom: {
            zoom: {
              mode: "x",
              drag: {
                enabled: true,
              },
              wheel: {
                enabled: true,
              },
              pinch: {
                enabled: true,
              },
            },
            pan: {
              mode: "x",
              enabled: true,
            },
          },
        },
      },
    });

    return this.chart;
  }

  /**
   * Custom legend click handler for toggling datasets visibility
   */
  handleLegendClick(e, legendItem, legend) {
    const index = legendItem.datasetIndex;
    const ci = legend.chart;

    // Check if only this dataset is currently visible
    const isOnlyVisibleDataset = ci.data.datasets.every((dataset, i) => {
      if (i === index) return !ci.getDatasetMeta(i).hidden;
      return ci.getDatasetMeta(i).hidden;
    });

    if (isOnlyVisibleDataset) {
      // If clicked dataset is the only one visible, show all datasets
      ci.data.datasets.forEach((dataset, i) => {
        const meta = ci.getDatasetMeta(i);
        meta.hidden = false;
      });
    } else {
      // Otherwise, hide all and show only the clicked one
      ci.data.datasets.forEach((dataset, i) => {
        const meta = ci.getDatasetMeta(i);
        meta.hidden = i !== index;
      });
    }

    // Ensure animations are preserved
    ci.update("show");
  }

  /**
   * Reset zoom level to default
   */
  resetZoom() {
    if (this.chart) {
      this.chart.resetZoom();
    }
  }
}

class SimpleTimeseriesGraph {
  constructor(ctx, endpointUrl, options = {}) {
    this.ctx = ctx;
    this.endpointUrl = endpointUrl;
    this.chart = null;
    this.options = options;
  }

  async init() {
    try {
      const chartData = await this.fetchData();
      this.renderChart(chartData);
    } catch (error) {
      console.error("Error initializing chart:", error);
    }
  }

  async fetchData() {
    const response = await fetch(this.endpointUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  }

  renderChart(chartData) {
    const dataset = chartData.datasets[0];

    this.chart = new Chart(this.ctx, {
      type: "line",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: dataset.label,
            data: dataset.data,
            backgroundColor: dataset.backgroundColor,
            borderColor: dataset.borderColor,
            borderWidth: dataset.borderWidth,
            fill: dataset.fill !== undefined ? dataset.fill : true,
            tension: dataset.tension !== undefined ? dataset.tension : 0.1,
          },
        ],
      },
      options: this.getChartOptions(),
    });
  }

  getChartOptions() {
    const textColor =
      getComputedStyle(document.documentElement)
        .getPropertyValue("--text-color")
        .trim() || "#fff";

    return {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            color: textColor,
          },
          grid: {
            color: "rgba(255, 255, 255, 0.2)",
          },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: textColor,
            callback: function (value) {
              const roundedValue = Math.round(value);
              return new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0,
              }).format(roundedValue);
            },
          },
          grid: {
            color: "rgba(255, 255, 255, 0.2)",
          },
        },
      },
      plugins: {
        legend: {
          display: this.options.showLegend || false,
        },
      },
    };
  }
}
class BackgroundTimeseriesGraph {
  constructor(elementId, endpointUrl) {
    const canvas = document.getElementById(elementId);
    if (!canvas) {
      throw new Error(`Element with ID "${elementId}" not found.`);
    }

    this.ctx = canvas.getContext("2d");
    this.endpointUrl = endpointUrl;
    this.chart = null;
  }

  async fetchData() {
    const response = await fetch(this.endpointUrl);
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.json();
  }

  async render() {
    try {
      const chartData = await this.fetchData();

      this.chart = new Chart(this.ctx, {
        type: "line",
        data: {
          labels: chartData.labels,
          datasets: chartData.datasets.map((dataset) => ({
            label: dataset.label,
            data: dataset.data,
            backgroundColor: dataset.backgroundColor,
            borderColor: dataset.borderColor,
            borderWidth: dataset.borderWidth || 2,
            fill: dataset.fill !== undefined ? dataset.fill : false,
            tension: dataset.tension !== undefined ? dataset.tension : 0.3,
            pointRadius:
              dataset.pointRadius !== undefined ? dataset.pointRadius : 0,
            pointHoverRadius:
              dataset.pointHoverRadius !== undefined
                ? dataset.pointHoverRadius
                : 0,
          })),
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              display: false,
            },
            y: {
              display: false,
            },
          },
          plugins: {
            legend: {
              display: false,
            },
          },
          animation: {
            x: {
              from: 0,
            },
            y: {
              from: 50,
            },
          },
        },
      });
    } catch (error) {
      console.error("Error rendering background timeseries graph:", error);
    }
  }
}
