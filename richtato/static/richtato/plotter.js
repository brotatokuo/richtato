class ChartPlotter {
    constructor(chartUrl, canvasId, tableID, tableUrl, year, editButton, saveTableEndpoint) {
        this.chartUrl = chartUrl;  // URL for the chart data
        this.canvasId = canvasId;  // Canvas ID where the chart will be plotted
        this.year = year;          // Year filter for the data
        this.chartInstance = null; // Chart instance to manage chart lifecycle
        this.editButton = editButton;

        // Initialize TableManager
        this.tableManager = new TableManager(tableID, tableUrl, editButton, saveTableEndpoint, this);
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
        const ctx = document.getElementById(this.canvasId).getContext('2d');

        // Create a new chart instance
        this.chartInstance = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                scales: {
                    x: { stacked: true },
                    y: {
                        beginAtZero: true,
                        stacked: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString('en-US', { 
                                    style: 'currency', 
                                    currency: 'USD',
                                    minimumFractionDigits: 0,  
                                    maximumFractionDigits: 2   
                                });
                            }
                        }
                     }
                },
                plugins: {
                    legend: { position: 'top' }
                },
                onClick: (event, elements) => this.handleChartClick(event, elements)
            }
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
            } else{
                console.log("Month filter not found, using chart labels");
                month = this.chartInstance.data.labels[index];
            }
            
            console.log("Clicked:", this.year, month, datasetLabel);

            this.tableManager.fetchBarTableData(this.year, month, datasetLabel);
            this.tableManager.updateTableTitles(`${this.year} ${month}`, `${datasetLabel}`);
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
        this.mode = 'view'; // Initial mode is 'view'
        this.chartInstance = chartInstance || null;        
    }

    updateTableTitles(title1, title2) {
        document.getElementById('detailed-table-title-1').textContent = title1;
        document.getElementById('detailed-table-title-2').textContent = title2;
    }
    
    fetchBarTableData(year, month, label) {
        this.tableUrl = `${this.tableUrl}?year=${year}&label=${encodeURIComponent(label)}&month=${month}`;
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
            .then(response => response.json())
            .then(data => {
                console.log("Fetched table data:", data);
                this.modifyTableData(data);
                this.showTable();
            })
            .catch(error => console.error('Error fetching table data:', error));
    }

    modifyTableData(data) {
        if (data) {
            const tableHead = this.table.querySelector('thead');
            const tableBody = this.table.querySelector('tbody');
            
            // Clear existing table content
            tableBody.innerHTML = '';
            tableHead.innerHTML = '';
        
            // Create and append header row
            const headerRow = document.createElement('tr');
        
            // Add 'Delete' column (hidden by default)
            const deleteHeader = document.createElement('th');
            deleteHeader.textContent = 'Delete';
            deleteHeader.style.display = 'none'; // Initially hide the Delete column
            headerRow.appendChild(deleteHeader);
        
            // Generate headers from the data keys (skip the ID column)
            Object.keys(data[0]).forEach((header, index) => {
                const th = document.createElement('th');
                th.textContent = header.charAt(0).toUpperCase() + header.slice(1);
                if (index === 0) th.style.display = 'none'; // Hide the ID column
                headerRow.appendChild(th);
            });
        
            tableHead.appendChild(headerRow);
        
            // Create and append data rows
            data.forEach(item => {
                const row = document.createElement('tr');
        
                // Add hidden checkbox column
                const checkboxCell = document.createElement('td');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkboxCell.style.display = 'none'; // Initially hide the Delete column
                checkboxCell.appendChild(checkbox);
                row.appendChild(checkboxCell);
        
                // Populate row cells (skip the ID column)
                Object.keys(item).forEach((key, index) => {
                    const cell = document.createElement('td');
                    cell.textContent = item[key];
                    if (index === 0) cell.style.display = 'none'; // Hide the ID column
                    row.appendChild(cell);
                });
        
                tableBody.appendChild(row);
            });
        }
    }
    
    showTable() {
        const detailedTable = document.querySelector('.detailed-table');
        if (detailedTable) {
            detailedTable.style.display = 'block';
        }
    }

    toggleEditMode() {
        if (this.mode === 'view') {
            console.log("Mode is view, enabling editing");
            this.mode = 'edit';
            this.editButton.textContent = 'Save';
            this.editButton.style.backgroundColor = 'gold';
            this.enableEditing();
        } else {
            console.log("Mode is edit, saving data");
            this.mode = 'view';
            this.editButton.textContent = 'Edit';
            this.editButton.style.backgroundColor = '#98cc2c';
            this.saveTable();
        }
    }
    
    
    // Method to enable or disable editing mode for table cells
    enableEditing() {
        const table = document.getElementById(this.tableID);
        const tableHead = table.querySelector('thead');
        const tableBody = table.querySelector('tbody');
    
        const headers = tableHead.querySelectorAll('th');
        const rows = tableBody.querySelectorAll('tr');
        // Toggle visibility for Delete and ID columns in the header
        if (headers.length >= 2) {
            const isHidden = headers[0].style.display === 'none';
            headers[0].style.display = isHidden ? '' : 'none'; // Toggle display for Delete column
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
    }


    saveTable() {
        const rows = this.table.rows;
        const data = [];
    
        // Get the headers from the first row (the header row)
        const headers = [];
        const headerCells = this.table.rows[0].cells;
    
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

            // Add the filter value to the row data
            const filterElement = document.getElementById('detailed-table-title-2');
            if (filterElement) {
                const filter = filterElement.textContent.trim();
                row_data['filter'] = filter;
            }

            data.push(row_data);
        }

        const csrfToken = getCSRFToken();
        
        console.log("Saving endpoint:", this.saveTableEndpoint);

        fetch(this.saveTableEndpoint, {
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
                this.loadTableData(this.tableUrl);
                if (this.chartInstance) {
                    this.chartInstance.plotChart();
                }
            })
            .catch(error => {
                console.error('Error saving data:', error);
            });
    }
}
