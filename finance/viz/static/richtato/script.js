document.addEventListener('DOMContentLoaded', (event) => {
    // Swap GIF with a static image after 2 seconds
    var gif = document.getElementById('growth-gif');
    if (gif) {
        setTimeout(function() {
            document.querySelector('.typewriter-text').style.borderRight = 'none';
            gif.src = staticImagePath; // Use the variable defined in the HTML
        }, 2000);
    }

    const currencyInput = document.getElementById('balance-input');
    if (currencyInput) {
        currencyInput.addEventListener('blur', function(e) {           
            let value = parseFloat(e.target.value);
            // Ensure the value is a valid number before formatting
            if (!isNaN(value)) {
                e.target.value = value.toFixed(2); // Format to two decimal places
            } else {
                console.log("Invalid input:", e.target.value); // Handle invalid input
            }
        });
    }    
});

// Toggle password visibility
function togglePasswordVisibility(id, button) {
    console.log("togglePasswordVisibility called with id:", id);
    var passwordInput = document.getElementById(id);
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
        button.textContent = "Hide";
    } else {
        passwordInput.type = "password";
        button.textContent = "Show";
    }
}


function getCSRFToken() {
    const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)')?.pop();
    return cookieValue || '';
}

// Bar Chart
myChart = null;
let lastChartUrl = '';
let lastCanvasId = '';
let lastTableID = '';
let lastTableUrl = '';
let lastYear = '';

async function plotBarChart(chartUrl, canvasId, tableID, tableUrl, year) {
    try {
        const response = await fetch(chartUrl);  // Fetch data from the provided chartUrl
        const data = await response.json();
        console.log("Data received from API:", data, "filter by year:", year);
        const filteredDataByYear = data.filter(item => item.year === parseInt(year));
        console.log("Filtered data:", filteredDataByYear);
        
        const ctx = document.getElementById(canvasId).getContext('2d');

        lastChartUrl = chartUrl;
        lastCanvasId = canvasId;
        lastTableID = tableID;
        lastTableUrl = tableUrl;
        lastYear = year;
        
        // Destroy existing chart instance if it exists
        if (myChart) {
            myChart.destroy();
        }

        myChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: filteredDataByYear.map(d => d.labels).flat(),  // Ensure your data structure supports this
                datasets: filteredDataByYear.map(d => d.data).flat()  // Adjust if your data structure is different
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        beginAtZero: true,
                        stacked: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        var datasetIndex = elements[0].datasetIndex;
                        var index = elements[0].index;
                        var datasetLabel = myChart.data.datasets[datasetIndex].label;
                        var month = myChart.data.labels[index];
                        console.log("Clicked:", year, month, datasetLabel);
                        
                        fetchBarTableData(tableID, tableUrl, year, month, datasetLabel);
                        


                        const title_1 = document.getElementById('detailed-table-title-1');
                        const title_2 = document.getElementById('detailed-table-title-2');

                        if (title_1 && title_2) {
                            title_1.textContent = `${year} ${month}`;
                            title_2.textContent = `${datasetLabel}`;
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}

async function plotBudgetBarChart(chartUrl, canvasId, tableID, tableUrl, year, month) {
    try {
        const response = await fetch(chartUrl);  // Fetch data from the provided chartUrl
        const data = await response.json();
        console.log("Data received from API:", data);
        const filteredDataByYear = data.filter(item => item.year === parseInt(year))[0];
        console.log("Filtered data by year:", filteredDataByYear);
        const filteredDataByMonth = filteredDataByYear.data.find(monthData => monthData.month === parseInt(month));
        console.log("Filtered data by month:", filteredDataByMonth);
        const plotData = filteredDataByMonth.data;
        console.log("Plot data:", plotData);

        const ctx = document.getElementById(canvasId).getContext('2d');

        lastChartUrl = chartUrl;
        lastCanvasId = canvasId;
        lastTableID = tableID;
        lastTableUrl = tableUrl;
        lastYear = year;
        
        // Destroy existing chart instance if it exists
        if (myChart) {
            myChart.destroy();
        }

        // Generate chart data: categories as labels, amounts as data
        const labels = plotData.map(d => d.label);  // Extract 'label' for labels
        const amounts = plotData.map(d => d.data);  // Extract 'data' for amounts
        console.log("Labels:", labels, "Amounts:", amounts);
        
        // Create the chart
        myChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,  // Use categories as labels
                datasets: [{
                    label: labels,
                    data: amounts,  // Use amounts as data
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',  // Bar color
                    borderColor: 'rgba(75, 192, 192, 1)',        // Border color
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        beginAtZero: true,
                        stacked: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';  // Append '%' to each y-axis tick label
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        var datasetLabel = myChart.data.datasets[0].label;
                        console.log("Clicked:", year, month, datasetLabel);
                        
                        fetchBarTableData(tableID, tableUrl, year, month, datasetLabel);
                    

                        const title_1 = document.getElementById('detailed-table-title-1');
                        const title_2 = document.getElementById('detailed-table-title-2');

                        if (title_1 && title_2) {
                            title_1.textContent = `${year} ${month}`;
                            title_2.textContent = `${datasetLabel}`;
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching stacked chart data:", error);
    }
}

// Table functions
function fetchBarTableData(tableID, tableUrl, year, month, label){
    const urlWithParams = `${tableUrl}?year=${year}&label=${encodeURIComponent(label)}&month=${month}`;
    console.log("fetchBarTableData called with tableID:", tableID, "urlWithParams:", urlWithParams);
    const editButton = document.getElementById('detailsTableEditButton');
    if (editButton) {
        editButton.onclick = function() {
            editTable(tableID, 'detailsTableEditButton', urlWithParams);
        };
    }
    loadTableData(tableID, urlWithParams)
}

function loadTableData(tableID, apiUrl) {
    const table = document.getElementById(tableID);
    console.log("loadTableData called with tableID:", tableID, "and apiUrl:", apiUrl);
    if (!table) {
        console.error(`Table with ID "${tableID}" not found.`);
        return;
    }

    const tableHead = table.querySelector('thead');
    const tableBody = table.querySelector('tbody');

    // Clear any existing rows
    tableBody.innerHTML = '';
    tableHead.innerHTML = '';

    // Fetch data from the API
    fetch(apiUrl)
        .then(response => {
            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                throw new Error("Response is not JSON");
            }
            return response.json(); // Parse JSON if content-type is correct
        })
        .then(data => {
            console.log("Data received from API:", data);

            // Select the detailed-table div
            const detailedTableDiv = document.querySelector('.detailed-table');
            if (tableID.includes("details-table")) {
                console.log("details-table detected, showing the div");
                detailedTableDiv.style.display = 'block';}

            // Dynamically generate the headers based on the first object's keys
            const headerRow = document.createElement('tr');

            // Add 'Delete' column as the first header
            const deleteHeader = document.createElement('th');
            deleteHeader.textContent = 'Delete';
            deleteHeader.style.fontWeight = 'bold';
            deleteHeader.style.display = 'none'; // Hide the Delete column initially
            headerRow.appendChild(deleteHeader);

            // Generate other headers based on the keys of the first object and hide the ID column
            const headers = Object.keys(data[0]);
            console.log("headers", headers);

            headers.forEach((header, index) => {
                const th = document.createElement('th');
                th.textContent = header.charAt(0).toUpperCase() + header.slice(1);
                th.style.fontWeight = 'bold';

                if (index === 0) {
                    th.style.display = 'none'; // Hide the ID column
                }

                headerRow.appendChild(th);
            });

            tableHead.appendChild(headerRow);

            // Loop through the data to create table rows
            data.forEach(item => {
                const row = document.createElement('tr');

                // Add the checkbox as the first column and hide it
                const checkboxCell = document.createElement('td');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkboxCell.appendChild(checkbox);
                checkboxCell.style.display = 'none'; // Hide the checkbox column initially
                row.appendChild(checkboxCell);

                // Add the rest of the item values as table columns
                headers.forEach((header, index) => {
                    const cell = document.createElement('td');
                    cell.textContent = item[header];

                    if (index === 0) {
                        cell.style.display = 'none'; // Hide the ID column initially
                    }

                    row.appendChild(cell);
                });

                tableBody.appendChild(row);
            });
        }
        )
        .catch(error => {
            console.error('Error fetching data:', error);
        });
}

// Edit mode functions
function toggleEditMode(tableID, editButton, buttonText, buttonColor) {
    const table = document.getElementById(tableID);
    const tableHead = table.querySelector('thead');
    const tableBody = table.querySelector('tbody');

    const headers = tableHead.querySelectorAll('th');
    const rows = tableBody.querySelectorAll('tr');

    // Toggle visibility for Delete and ID columns in the header
    if (headers.length >= 2) {
        const isHidden = headers[0].style.display === 'none';
        headers[0].style.display = isHidden ? '' : 'none'; // Toggle display for Delete column
        // headers[1].style.display = isHidden ? '' : 'none'; // Toggle display for ID column
    }

    // Toggle visibility for Delete and ID columns in each row
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 2) {
            const isHidden = cells[0].style.display === 'none';
            cells[0].style.display = isHidden ? '' : 'none'; // Toggle display for Delete column
            // cells[1].style.display = isHidden ? '' : 'none'; // Toggle display for ID column
        }

        // Toggle between edit and non-edit modes for non-hidden cells
        for (let j = 2; j < cells.length; j++) {
            const cell = cells[j];

            // Special case for 'settings-accounts-table': Exclude the last two columns
            if (tableID === 'settings-accounts-table' && j >= cells.length - 2) {
                continue; // Skip the last two columns
            }

            const input = cell.querySelector('input');

            if (input) {
                const value = input.value;
                cell.innerHTML = value ? value : ''; // Set the value as plain text
            } else {
                const value = cell.textContent.trim();
                cell.innerHTML = `<input type="text" value="${value}">`;
            }
        }
    });

    // Update the button's text and color
    editButton.innerHTML = buttonText;
    editButton.style.backgroundColor = buttonColor;
}

function editTable(tableID, editButtonID, refreshUrl) {
    const editButton = document.getElementById(editButtonID);

    if (editButton.innerHTML === 'Edit') {
        toggleEditMode(tableID, editButton, 'Save', 'gold');
    } else {
        let apiUrl;  // Declare apiUrl outside the block
        
        // Assign the appropriate API URL based on the table ID
        if (tableID === 'settings-card-table') {
            apiUrl = "update-settings-card-account/";
        } else if (tableID === 'settings-accounts-table') {
            apiUrl = "update-settings-accounts/";
        } else if (tableID === 'settings-categories-table') {
            apiUrl = "update-settings-categories/";
        } else if (tableID === 'details-table-spendings') {
            apiUrl = "update-spendings/";
        } else if (tableID === 'details-table-earnings') {
            apiUrl = "update-earnings/";
        } else if (tableID === 'details-table-accounts') {
            apiUrl = "update-accounts/";
        }

        // Call saveTable with the correct apiUrl and refreshUrl
        if (apiUrl) {
            saveTable(tableID, editButton, apiUrl, refreshUrl);
        } else {
            console.error(`No API URL available for table ID "${tableID}"`);
        }
    }        
}

async function saveTable(tableID, editButton, apiUrl, refreshUrl) {
    const userID = await getUserID();
    console.log("userID:", userID);
    console.log("saveTable called with tableID:", tableID, "apiUrl:", apiUrl, "refreshUrl:", refreshUrl);
    const table = document.getElementById(tableID);
    const rows = table.rows;
    const data = [];

    // Get the headers from the first row (the header row)
    const headers = [];
    const headerCells = table.rows[0].cells;

    for (let i = 0; i < headerCells.length; i++) {
        const headerText = headerCells[i].textContent.trim().toLowerCase().replace(/\s+/g, '_');
        headers.push(headerText);
    }

    // Loop through each row (skipping the header row)
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.cells;
        const row_data = {};

        for (let j = 0; j < cells.length; j++) {
            const header = headers[j];
            if (header === 'delete') {
                row_data[header] = cells[j].querySelector('input[type="checkbox"]').checked;
            } else {
                const inputElement = cells[j].querySelector('input');
                if (inputElement) {
                    row_data[header] = inputElement.value;
                } else {
                    row_data[header] = cells[j].textContent.trim();
                }
            }
        }
        row_data['user'] = userID;
        console.log("row_data:", row_data);
        data.push(row_data);
    }

    const csrfToken = getCSRFToken();

    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        console.log("Data saved?:", result);
        loadTableData(tableID, refreshUrl);
        plotBarChart(lastChartUrl, lastCanvasId, lastTableID, lastTableUrl, lastYear);
        toggleEditMode(tableID, editButton, 'Edit', '#98cc2c');
    })
    .catch(error => {
        console.error('Error saving data:', error);
    });
}

function getUserID() {
    return fetch('get-user-id')
        .then(response => response.json())
        .then(data => data.userID);
}