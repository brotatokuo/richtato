import DataTable from 'datatables.net';
import 'datatables.net-dt/css/jquery.dataTables.min.css';

class NewTable {
    constructor(tableId, tableUrl, options = {}) {
        this.tableId = tableId;
        this.tableUrl = tableUrl;
        this.data = null;
        this.columns = null;
        this.options = options;
        this.instance = null;
    }

    async fetchData() {
        try {
            const response = await fetch(this.tableUrl);
            const data = await response.json();
            this.data = data.data;
            this.columns = data.columns;
            console.log('Fetched data:', this.data, this.columns);
            this.renderTable();
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    renderTable() {
        $(this.tableId).DataTable({
            data: this.data,
            columns: this.columns,
            paging: true,
            searching: true
        });
    }

    init() {
        this.fetchData();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const tableDropdown = document.getElementById("tableOption");
    let tableOption = tableDropdown.value;
    let pageNumber = 1;
    var tableUrl = `/get-table-data/?option=${encodeURIComponent(tableOption)}&page=${pageNumber}`;
    console.log(tableUrl);
    const table = new NewTable('fullTable', tableUrl, {
        paging: true,
        searching: true
    });
    table.init();
});
