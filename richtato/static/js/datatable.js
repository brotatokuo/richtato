class NewTable {
    constructor(tableId, tableUrl, config = {}, options = {}) {
        this.tableId = tableId;
        this.tableUrl = tableUrl;
        this.data = null;
        this.columns = null;
        this.config = {
            paging: false,
            searching: false,
            info: false,
            lengthChange: false,
            ...config  // Merge any passed config with the default
        };
        this.options = options;
        this.instance = null;
        this.init();
    }

    async fetchData() {
        try {
            console.log("Fetching data from URL:", this.tableUrl);
            const response = await fetch(this.tableUrl);
            const data = await response.json();
            this.data = data.data;
            this.columns = data.columns;
            this.renderTable();
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    renderTable() {
        const tableElement = $(this.tableId);
        // Clear any existing table data (important for re-rendering)
        if (tableElement.DataTable()) {
            tableElement.DataTable().clear().destroy();
        }

        const thead = $(this.tableId).find('thead');
        thead.empty(); // Clear existing header rows
        const headerRow = $('<tr></tr>');
        if (this.columns && this.columns.length > 0) {
            this.columns.forEach(col => {
                const th = $('<th></th>').text(col.title);
                headerRow.append(th);
            });
        } else {
            console.error("No columns available to render!");
        }

        thead.append(headerRow);

        // Populate the table body dynamically
        const tbody = $(this.tableId).find('tbody');
        this.data.forEach((row, rowIndex) => {
            const tr = $('<tr></tr>')
            this.columns.forEach((col, colIndex) => {
                const td = $('<td></td>').text(row[col.data]);
                tr.append(td);
            });

            tbody.append(tr);
        });

        tableElement.DataTable(this.config);
    }
    init() {
        this.fetchData();
    }
}
