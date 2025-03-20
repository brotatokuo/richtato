const currencyInputs = document.getElementsByClassName('currency-input');
Array.from(currencyInputs).forEach(currencyInput => {

    currencyInput.addEventListener('input', () => {
        const value = currencyInput.value;
        const validCharacters = /^[0-9+\-*/().=]*$/;
        if (!validCharacters.test(value)) {
            currencyInput.value = value.replace(/[^0-9+\-*/().=]/g, '');
        }
    });

    currencyInput.addEventListener('blur', () => {
        let balance = currencyInput.value;

        if (balance) {
            let newBalance = computeBalance(balance);

            if (newBalance) {
                currencyInput.value = newBalance;
                console.log('New balance:', newBalance);
            }
        }
    });
});

const descriptionInput = document.getElementById('expense-description');
descriptionInput.addEventListener('blur', () => {
    const description = descriptionInput.value;
    guessCategoryFromDescription(description);
});

document.addEventListener('DOMContentLoaded', () => {
    const expenseLineChart = document.getElementById('expenseLineChart').getContext('2d');
    plotExpenseLineChart(expenseLineChart, '/expense/get_line_graph_data/');
    const incomeLineChart = document.getElementById('incomeLineChart').getContext('2d');
    plotExpenseLineChart(incomeLineChart, '/income/get_line_graph_data/');

    const expenseTable = new Table(
        "expenseTable",
        "/expense/get_recent_entries/",
        document.getElementById("editExpenseTable"),
        "/expense/update/",
        null
    );

    const incomeTable = new Table(
        "incomeTable",
        "/income/get_recent_entries/",
        document.getElementById("editIncomeTable"),
        "/income/update/",
        null
    );
});

async function plotExpenseLineChart(ctx, endpointUrl) {
    try {
        const response = await fetch(endpointUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const chartData = await response.json();
        const dataset = chartData.datasets[0];
        const myLineChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels, // Use the labels from the response
                datasets: [{
                    label: dataset.label,
                    data: dataset.data, // Use the data from the response
                    backgroundColor: dataset.backgroundColor,  // Semi-transparent background color
                    borderColor: dataset.borderColor,             // Border color for the line
                    borderWidth: dataset.borderWidth,
                    fill: dataset.fill !== undefined ? dataset.fill : true,
                    tension: dataset.tension !== undefined ? dataset.tension : 0.1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false // Set to true if you want to display the legend
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error fetching or plotting data:', error);
    }
}


function guessCategoryFromDescription(description) {
    console.log('Guessing category for:', description);
    // Encode the description before sending it
    const url = `/expense/guess-category/?description=${encodeURIComponent(description)}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.category) {
                console.log('Category found:', data.category);
                const categoryInput = document.getElementById('category');
                categoryInput.value = data.category;
            } else {
                console.log('No category found');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });


}

function computeBalance(balance) {
    if (balance.startsWith('=')) {
        try {
            balance = eval(balance.slice(1));
            console.log('Evaluated formula:', balance);
        } catch (error) {
            console.error('Invalid formula:', error);
            return;
        }
    }
    else {
        balance = eval(balance);;
    }
    balance = parseFloat(balance).toFixed(2);
    return balance;
}

class Table {
    constructor(tableID, tableUrl, editButton, saveTableEndpoint) {
        this.tableID = tableID;
        this.tableUrl = tableUrl;
        this.saveTableEndpoint = saveTableEndpoint;
        this.table = document.getElementById(tableID);
        this.editButton = editButton;
        this.mode = "view"; // Initial mode is 'view'
        this.sortDirections = {}; // Track the current sorting order for each column
        this.loadTableData();
        this.editButton.onclick = this.toggleEditMode.bind(this);
    }

    fetchBarTableData(year, month, label) {
        this.tableUrl = `${this.tableUrl}?year=${year}&label=${encodeURIComponent(
            label
        )}&month=${month}`;
        this.loadTableData();
        this.editButton.onclick = this.toggleEditMode.bind(this, this.tableUrl);
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
                else {
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
            this.enableEditing();
            this.mode = "edit";
            this.editButton.textContent = "Save";
            this.editButton.style.backgroundColor = "gold";

        } else {
            console.log("Mode is edit, saving data");
            this.saveTable();
            this.mode = "view";
            this.editButton.textContent = "Edit";
            this.editButton.style.backgroundColor = "#0075ff";
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