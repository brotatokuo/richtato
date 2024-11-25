function getUserID() {
    return fetch('get-user-id')
        .then(response => response.json())
        .then(data => data.userID);
}

function fetchBarTableData(tableID, tableUrl, year, month, label) {
    const urlWithParams = `${tableUrl}?year=${year}&label=${encodeURIComponent(label)}&month=${month}`;
    console.log("fetchBarTableData called with tableID:", tableID, "urlWithParams:", urlWithParams);
    const editButton = document.getElementById('detailsTableEditButton');
    if (editButton) {
        editButton.onclick = function () {
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
                detailedTableDiv.style.display = 'block';
            }

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
        } else if (tableID === 'details-table-budget') {
            apiUrl = "update-spendings/";
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
            toggleEditMode(tableID, editButton, 'Edit', '#98cc2c');
            if (tableID.includes("details-table")) {
                plotBarChart(lastChartUrl, lastCanvasId, lastTableID, lastTableUrl, lastYear);
            }

        })
        .catch(error => {
            console.error('Error saving data:', error);
        });
}