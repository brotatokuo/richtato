class ChartPlotter {
  constructor(
    chartUrl,
    canvasId,
    tableID,
    tableUrl,
    year,
    editButton,
    saveTableEndpoint,
    yAxisFormat = "currency"
  ) {
    this.chartUrl = chartUrl; // URL for the chart data
    this.canvasId = canvasId; // Canvas ID where the chart will be plotted
    this.year = year; // Year filter for the data
    this.chartInstance = null; // Chart instance to manage chart lifecycle
    this.editButton = editButton;
    this.yAxisFormat = yAxisFormat; // Y-axis format, default is 'currency'

    // Initialize TableManager
    this.tableManager = new TableManager(
      tableID,
      tableUrl,
      editButton,
      saveTableEndpoint,
      this
    );
  }

  // Fetch chart data from the server
  async fetchData() {
    try {
      const response = await fetch(this.chartUrl);
      const data = await response.json();
      console.log("Fetched chart data:", data);
      return data;
    } catch (error) {
      console.error("Error fetching chart data:", error);
      throw error;
    }
  }

  // Plot the chart using the fetched data
  async plotChart() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }

    const data = await this.fetchData();
    const yAxisFormat = this.yAxisFormat; // Store reference to yAxisFormat
    const ctx = document.getElementById(this.canvasId).getContext("2d");

    // Create a new chart instance
    this.chartInstance = new Chart(ctx, {
      type: "bar",
      data: data,
      options: {
        responsive: true,
        scales: {
          x: {
            stacked: true,
            ticks: {
              color: "white",
            },
            grid: {
              color: "rgba(255, 255, 255, 0.2)", // Optional: grid line color
            },
          },
          y: {
            grid: {
              color: "rgba(255, 255, 255, 0.2)", // Optional: grid line color
            },
            beginAtZero: true,
            stacked: true,
            ticks: {
              color: "white",
              callback: function (value) {
                if (yAxisFormat === "percentage") {
                  console.log("Formatting as percentage");
                  return `${value}%`; // Format as percentage
                } else {
                  return value.toLocaleString("en-US", {
                    style: "currency",
                    currency: "USD",
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  });
                }
              },
            },
          },
        },
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: "white", // White text for legend labels
            },
          },
          tooltip: {
            titleColor: "white", // White text for tooltip title
            bodyColor: "white", // White text for tooltip body
            callbacks: {
              label: (tooltipItem) => {
                const label = tooltipItem.dataset.label || "";
                const value = tooltipItem.raw; // Get the raw value for that label
                const totalForMonth = data.datasets.reduce((acc, dataset) => {
                  return acc + dataset.data[tooltipItem.dataIndex];
                }, 0); // Sum up the values for all datasets in the current month

                if (yAxisFormat === "percentage") {
                  return `${label}: ${value}% (Total: ${totalForMonth}%)`;
                } else {
                  const formattedValue = value.toLocaleString("en-US", {
                    style: "currency",
                    currency: "USD",
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  });
                  const formattedTotal = totalForMonth.toLocaleString("en-US", {
                    style: "currency",
                    currency: "USD",
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  });
                  return `${label}: ${formattedValue} (Total: ${formattedTotal})`;
                }
              },
            },
          },
        },
        onClick: (event, elements) => this.handleChartClick(event, elements),
      },
    });
  }

  // Handle chart click events
  handleChartClick(event, elements) {
    if (elements.length > 0) {
      const datasetIndex = elements[0].datasetIndex;
      const index = elements[0].index;
      const datasetLabel = this.chartInstance.data.datasets[datasetIndex].label;
      const monthFilter = document.getElementById("month-filter");
      let month;
      if (monthFilter) {
        console.log("Month filter found:", monthFilter);
        month = monthFilter.value;
      } else {
        console.log("Month filter not found, using chart labels");
        month = this.chartInstance.data.labels[index];
      }
      // Log the clicked information
      console.log("Clicked:", this.year, month, datasetLabel);

      // Update table title
      const title1 = document.getElementById("detailed-table-title-1");
      const title2 = document.getElementById("detailed-table-title-2");
      title1.textContent = `${this.year} ${month}`;

      // Fetch and update the table data
      this.tableManager.fetchBarTableData(this.year, month, datasetLabel);
      this.tableManager.updateTableTitles(`${month}`, `${datasetLabel}`);
    }
  }
}
class TableManager {
  constructor(tableID, tableUrl, editButton, saveTableEndpoint, chartInstance) {
    this.tableID = tableID;
    this.tableUrl = tableUrl;
    this.saveTableEndpoint = saveTableEndpoint;
    this.table = document.getElementById(tableID);
    this.editButton = editButton;
    this.mode = "view"; // Initial mode is 'view'
    this.chartInstance = chartInstance || null;
    this.sortDirections = {}; // Track the current sorting order for each column
  }

  updateTableTitles(title1, title2) {
    const titleElement1 = document.getElementById("detailed-table-title-1");
    if (titleElement1) {
      titleElement1.value = title1;
      console.log("Title 1 value set:", titleElement1.value);
    } else {
      console.log("Element not found:", title1);
    }
    const titleElement2 = document.getElementById("detailed-table-title-2");
    console.log("Updating table titles:", title1, title2);

    // Check if the dropdowns exist before setting their value
    if (titleElement1 && titleElement2) {
      titleElement1.value = title1; // Sets the selected value
      titleElement2.value = title2; // Sets the selected value

      console.log("Title 1 value set:", titleElement1.value);
      console.log("Title 2 value set:", titleElement2.value);
    }
  }

  fetchBarTableData(year, month, label) {
    this.tableUrl = `${this.tableUrl}?year=${year}&label=${encodeURIComponent(
      label
    )}&month=${month}`;
    this.editButton.onclick = this.toggleEditMode.bind(this, this.tableUrl);
    this.loadTableData();
  }

  loadTableData() {
    const table = document.getElementById(this.tableID);
    if (!table) {
      console.error(`Table with ID "${this.tableID}" not found.`);
      return;
    }

    // Fetch data from the API
    fetch(this.tableUrl)
      .then((response) => response.json())
      .then((data) => {
        if (data && data.length > 0) {
          console.log("Fetched table data:", data);
          this.modifyTableData(data);
          this.showTable();
        }
        else
        {
          console.log("No data found", this.tableID);
          table.style.display = "none";
          this.editButton.style.display = "none";
        }
      })
      .catch((error) => console.error("Error fetching table data:", error));
  }

  modifyTableData(data) {
    if (data && data.length > 0) {
      const tableHead = this.table.querySelector("thead");
      const tableBody = this.table.querySelector("tbody");

      // Clear existing table content
      tableBody.innerHTML = "";
      tableHead.innerHTML = "";

      // Create and append header row
      const headerRow = document.createElement("tr");

      // Add 'Delete' column (hidden by default)
      const deleteHeader = document.createElement("th");
      deleteHeader.textContent = "Delete";
      deleteHeader.style.display = "none"; // Initially hide the Delete column
      headerRow.appendChild(deleteHeader);

      // Generate headers from the data keys (skip the ID column)
      Object.keys(data[0]).forEach((header, index) => {
        const th = document.createElement("th");
        th.textContent = header.charAt(0).toUpperCase() + header.slice(1);
        if (index === 0) th.style.display = "none"; // Hide the ID column
        headerRow.appendChild(th);

        // Add event listener to handle sorting
        th.addEventListener("click", () => {
          const direction =
            this.sortDirections[header] === "asc" ? "desc" : "asc";
          console.log("Sorting by:", header, direction);
          console.log("sorting directions:", this.sortDirections);
          this.sortDirections[header] = direction; // Toggle sort direction
          this.sortTable(data, index, direction); // Sort by the clicked column

          // Update header arrows
          this.updateSortArrows(headerRow, index, direction);
        });
      });

      tableHead.appendChild(headerRow);

      // Create and append data rows
      data.forEach((item) => {
        const row = document.createElement("tr");

        // Add hidden checkbox column
        const checkboxCell = document.createElement("td");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkboxCell.style.display = "none"; // Initially hide the Delete column
        checkboxCell.appendChild(checkbox);
        row.appendChild(checkboxCell);

        // Populate row cells (skip the ID column)
        Object.keys(item).forEach((key, index) => {
          const cell = document.createElement("td");
          cell.textContent = item[key];
          if (index === 0) cell.style.display = "none"; // Hide the ID column
          row.appendChild(cell);
        });

        tableBody.appendChild(row);
      });
    }
  }

  showTable() {
    const detailedTable = document.querySelector(".detailed-table");
    if (detailedTable) {
      detailedTable.style.display = "block";
    }
  }

  updateSortArrows(headerRow, sortedIndex, direction) {
    // Get all headers (th elements) in the header row
    const headers = headerRow.querySelectorAll("th");

    headers.forEach((header, index) => {
      if (index > 0) {
        // Skip the delete column (index 0 is hidden)
        const actualIndex = index - 1; // Adjust index for sorting (skip the delete column)
        if (actualIndex === sortedIndex) {
          // If this is the sorted column, add the arrow (▲ or ▼)
          const arrow = direction === "asc" ? " ▲" : " ▼";
          header.textContent = header.textContent.replace(/[▲▼]/g, "") + arrow; // Remove any existing arrow and append the new one
        } else {
          // Remove arrow from other columns
          header.textContent = header.textContent.replace(/[▲▼]/g, "");
        }
      }
    });
  }

  sortTable(data, columnIndex, direction) {
    // Sort the data array
    data.sort((a, b) => {
      const keyA = Object.keys(a)[columnIndex];
      const keyB = Object.keys(b)[columnIndex];
      let valueA = a[keyA];
      let valueB = b[keyB];

      // If values are numeric, compare as numbers
      if (!isNaN(valueA) && !isNaN(valueB)) {
        valueA = Number(valueA);
        valueB = Number(valueB);
      }

      console.log("Sorting:", direction);

      if (direction === "asc") {
        return valueA > valueB ? 1 : -1;
      } else {
        return valueA < valueB ? 1 : -1;
      }
    });

    // After sorting, re-render the table with the sorted data
    this.modifyTableData(data);

    // Update the sorting arrows after sorting
    const tableHead = this.table.querySelector("thead");
    const headerRow = tableHead.querySelector("tr");
    this.updateSortArrows(headerRow, columnIndex, direction);
  }

  toggleEditMode() {
    if (this.mode === "view") {
      console.log("Mode is view, enabling editing");
      this.mode = "edit";
      this.editButton.textContent = "Save";
      this.editButton.style.backgroundColor = "gold";
      this.enableEditing();
    } else {
      console.log("Mode is edit, saving data");
      this.mode = "view";
      this.editButton.textContent = "Edit";
      this.editButton.style.backgroundColor = "#98cc2c";
      this.saveTable();
    }
  }

  // Method to enable or disable editing mode for table cells
  enableEditing() {
    const table = document.getElementById(this.tableID);
    const tableHead = table.querySelector("thead");
    const tableBody = table.querySelector("tbody");

    const headers = tableHead.querySelectorAll("th");
    const rows = tableBody.querySelectorAll("tr");
    // Toggle visibility for Delete and ID columns in the header
    if (headers.length >= 2) {
      const isHidden = headers[0].style.display === "none";
      headers[0].style.display = isHidden ? "" : "none"; // Toggle display for Delete column
    }

    // Toggle visibility for Delete and ID columns in each row
    rows.forEach((row) => {
      const cells = row.querySelectorAll("td");
      if (cells.length >= 2) {
        const isHidden = cells[0].style.display === "none";
        cells[0].style.display = isHidden ? "" : "none"; // Toggle display for Delete column
        // cells[1].style.display = isHidden ? '' : 'none'; // Toggle display for ID column
      }

      // Toggle between edit and non-edit modes for non-hidden cells
      for (let j = 2; j < cells.length; j++) {
        const cell = cells[j];

        const input = cell.querySelector("input");

        if (input) {
          const value = input.value;
          cell.innerHTML = value ? value : ""; // Set the value as plain text
        } else {
          const value = cell.textContent.trim();
          cell.innerHTML = `<input type="text" value="${value}">`;
        }
      }
    });
  }

  saveTable() {
    const rows = this.table.rows;
    const data = [];

    // Get the headers from the first row (the header row)
    const headers = [];
    const headerCells = this.table.rows[0].cells;

    for (let i = 0; i < headerCells.length; i++) {
      const headerText = headerCells[i].textContent
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "_");
      headers.push(headerText);
    }

    // Loop through each row (skipping the header row)
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const cells = row.cells;
      const row_data = {};

      for (let j = 0; j < cells.length; j++) {
        const header = headers[j];
        if (header === "delete") {
          row_data[header] = cells[j].querySelector(
            'input[type="checkbox"]'
          ).checked;
        } else {
          const inputElement = cells[j].querySelector("input");
          if (inputElement) {
            row_data[header] = inputElement.value;
          } else {
            row_data[header] = cells[j].textContent.trim();
          }
        }
      }

      // Add the filter value to the row data
      const filterElement = document.getElementById("detailed-table-title-2");
      if (filterElement) {
        const filter = filterElement.textContent.trim();
        row_data["filter"] = filter;
      }
      data.push(row_data);
    }

    const csrfToken = getCSRFToken();

    console.log("Saving endpoint:", this.saveTableEndpoint);
    console.log("Payload", data);

    fetch(this.saveTableEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(data),
    })
      .then((response) => response.json())
      .then((result) => {
        console.log("Data saved?:", result);
        this.loadTableData(this.tableUrl);
        if (this.chartInstance) {
          this.chartInstance.plotChart();
        }
      })
      .catch((error) => {
        console.error("Error saving data:", error);
      });
  }
}
