class RichTable {
    constructor(tableId, tableUrl, config = {}, visibleColumns = null, invisibleColumns = null) {
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
        this.visibleColumns = visibleColumns;
        this.invisibleColumns = invisibleColumns;
        this.instance = null;
        this.fetchData();
    }

    async fetchData() {
        try {
            console.log("Fetching data from URL:", this.tableUrl);
            const response = await fetch(this.tableUrl);
            const data = await response.json();
            console.log("Data fetched:", data);
            this.data = data.data;
            this.columns = data.columns;
            this.renderTable();
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }
    
    getColumnsToShow() {
        const allColumns = this.columns.map(col => col.data);
    
        if (this.visibleColumns) {
            return this.visibleColumns.filter(col => col.toLowerCase() !== 'id');
        } else if (this.invisibleColumns) {
            return allColumns.filter(col => 
                !this.invisibleColumns.map(c => c.toLowerCase()).includes(col.toLowerCase()) &&
                col.toLowerCase() !== 'id'
            );
        } else {
            // Default: show everything except "id"
            return allColumns.filter(col => col.toLowerCase() !== 'id');
        }
    }
    

    renderTable() {
        const tableElement = $(this.tableId);
        if ($.fn.DataTable.isDataTable(this.tableId)) {
            tableElement.DataTable().clear().destroy();
        }

        const thead = tableElement.find('thead');
        const tbody = tableElement.find('tbody');

        thead.empty();
        tbody.empty();

        const headerRow = $('<tr></tr>');
        const columnsToShow = this.getColumnsToShow();

        console.log("Columns to show:", columnsToShow);

        this.columns.forEach((col) => {
            if (!columnsToShow.includes(col.data)) return;
            headerRow.append($('<th></th>').text(col.title));
        });

        thead.append(headerRow);

        this.data.forEach(row => {
            const tr = $('<tr></tr>');
            this.columns.forEach((col) => {
                if (!columnsToShow.includes(col.data)) return;
                tr.append($('<td></td>').text(row[col.data]));
            });
            tbody.append(tr);
        });

        const dt = tableElement.DataTable(this.config);

        // Hook rows into EditableRow
        dt.rows().every((i) => {
            const dtRow = dt.row(i);
            const $tr = $(dtRow.node());
            const rowData = dtRow.data();

            new EditableRow(
                rowData,
                this.columns,
                columnsToShow,
                $tr,
                dtRow,
                (updated) => console.log("Updated:", updated),
                (deleted) => console.log("Deleted:", deleted)
            );
        });
    }
}

class EditableRow {
    constructor(rowData, columnDefs, visibleColumns, tableRowElement, dataTableRow, onUpdate, onDelete) {
        this.data = rowData;
        this.columns = columnDefs;
        this.visibleColumns = visibleColumns;
        this.$tr = tableRowElement;
        this.dtRow = dataTableRow;
        this.onUpdate = onUpdate;
        this.onDelete = onDelete;

        this.attachClickHandler();
    }

    attachClickHandler() {
        this.$tr.off('click').on('click', () => this.expand());
    }

    expand() {
        // Collapse if already open
        if (this.$tr.hasClass('shown')) {
            this.dtRow.child.hide();
            this.$tr.removeClass('shown');
            return;
        }

        // Hide any others (optional depending on design)
        $('.shown').each(function () {
            $(this).removeClass('shown');
            $(this).next('tr').remove();
        });

        const hiddenCols = this.columns.filter(col =>
            !this.visibleColumns.includes(col.data) && col.data !== 'id'
        );

        const form = $('<div class="edit-form"></div>');

        hiddenCols.forEach((col) => {
            const input = $('<input type="text" class="form-control"/>')
                .val(this.data[col.data])
                .attr('data-field', col.data);

            const label = $('<label></label>').text(col.title + ': ');
            form.append($('<div class="form-group mb-2"></div>').append(label, input));
        });

        const editBtn = $('<button class="btn btn-sm btn-primary">Save</button>');
        const deleteBtn = $('<button class="btn btn-sm btn-danger ms-2">Delete</button>');
        const btnGroup = $('<div class="mt-2"></div>').append(editBtn, deleteBtn);
        form.append(btnGroup);

        editBtn.on('click', () => {
            const updatedData = { ...this.data };
            form.find('input').each(function () {
                const field = $(this).data('field');
                updatedData[field] = $(this).val();
            });

            this.dtRow.data(updatedData).draw();
            this.dtRow.child.hide();
            this.$tr.removeClass('shown');
            this.onUpdate(updatedData);
        });

        deleteBtn.on('click', () => {
            if (confirm("Are you sure you want to delete this row?")) {
                this.dtRow.remove().draw();
                this.onDelete(this.data);
            }
        });

        this.dtRow.child(form).show();
        this.$tr.addClass('shown');
    }
}

