class RichTable {
  constructor(
    tableId,
    tableUrl,
    config = {},
    visibleColumns = null,
    invisibleColumns = null
  ) {
    this.tableId = tableId;
    this.tableUrl = tableUrl;
    this.data = null;
    this.columns = null;
    this.config = {
      paging: false,
      searching: false,
      info: false,
      lengthChange: false,
      dom: "Bfrtip",
      buttons: [],
      select: {
        style: "os",
        selector: "td.select-checkbox",
      },
      columnDefs: [
        {
          targets: 0,
          orderable: false,
          className: "select-checkbox custom-checkbox",
          defaultContent: "",
        },
      ],
      order: [[1, "asc"]],
      ...config,
    };
    this.visibleColumns = visibleColumns;
    this.invisibleColumns = invisibleColumns;
    this.instance = null;
    this.fetchData();
  }

  async fetchData() {
    try {
      const response = await fetch(this.tableUrl);
      const data = await response.json();
      this.data = data.data;
      this.columns = data.columns;
      this.renderTable();
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  }

  getColumnsToShow() {
    const allColumns = this.columns.map((col) => col.data);
    if (this.visibleColumns) {
      return this.visibleColumns.filter((col) => col.toLowerCase() !== "id");
    } else if (this.invisibleColumns) {
      return allColumns.filter(
        (col) =>
          !this.invisibleColumns
            .map((c) => c.toLowerCase())
            .includes(col.toLowerCase()) && col.toLowerCase() !== "id"
      );
    } else {
      return allColumns.filter((col) => col.toLowerCase() !== "id");
    }
  }

  renderTable() {
    const tableElement = $(this.tableId);
    if ($.fn.DataTable.isDataTable(this.tableId)) {
      tableElement.DataTable().clear().destroy();
    }

    const thead = tableElement.find("thead");
    const tbody = tableElement.find("tbody");
    thead.empty();
    tbody.empty();

    const headerRow = $("<tr></tr>");
    headerRow.append($("<th></th>")); // For checkbox
    const columnsToShow = this.getColumnsToShow();

    columnsToShow.forEach((col) => {
      const colObj = this.columns.find((c) => c.data === col);
      headerRow.append($("<th></th>").text(colObj?.title || col));
    });

    thead.append(headerRow);

    this.data.forEach((row) => {
      const tr = $("<tr></tr>");
      tr.append("<td></td>"); // checkbox column
      columnsToShow.forEach((col) => {
        tr.append($("<td></td>").text(row[col]));
      });
      tbody.append(tr);
    });

    // Set columns with checkbox and visible ones
    const allDTColumns = [
      {
        data: null,
        defaultContent: "",
        orderable: false,
        className: "select-checkbox",
      },
      ...columnsToShow.map((col) => ({ data: col })),
    ];

    this.config.columns = allDTColumns;
    this.config.buttons = [
      {
        text: "Add",
        action: () => this.handleAddEntry(),
      },
      {
        text: "Edit",
        action: () => {
          const selectedData = this.instance.row({ selected: true }).data();
          if (selectedData) {
            this.handleEditEntry(selectedData);
          } else {
            alert("Please select a row to edit.");
          }
        },
      },
      {
        text: "Delete",
        action: () => {
          const selectedRow = this.instance.row({ selected: true });
          const rowData = selectedRow.data();
          if (rowData) {
            if (confirm("Are you sure you want to delete this row?")) {
              selectedRow.remove().draw();
              console.log("Deleted:", rowData);
              // TODO: Sync deletion with server
            }
          } else {
            alert("Please select a row to delete.");
          }
        },
      },
    ];

    this.instance = tableElement.DataTable(this.config);
  }
  handleAddEntry() {
    const columnsToRender = this.columns;
    console.log("Columns to Render", columnsToRender);

    // Create modal overlay
    const modal = $(`
        <div class="custom-modal-overlay">
            <div class="custom-modal">
            <div class="custom-modal-header">
                <h3>Add New Entry</h3>
                <span class="close-button">&times;</span>
            </div>
            <form class="custom-modal-form">
            </form>
            <div class="custom-modal-footer">
                <button type="submit" class="save-button">Save</button>
            </div>
            </div>
        </div>
        `);

    const form = modal.find("form");

    // Dynamically create input fields
    columnsToRender.forEach((col) => {
      const field = $(`
          <div class="form-group">
            <label for="${col.data}">${col.title}</label>
            <input type="text" id="${col.data}" name="${col.data}" class="form-control" />
          </div>
        `);
      form.append(field);
    });

    // Add modal to body
    $("body").append(modal);

    // Event: Close modal
    modal
      .find(".close-button, .cancel-button")
      .on("click", () => modal.remove());

    // Event: Submit
    modal.find(".save-button").on("click", (e) => {
      e.preventDefault();
      const newRow = {};
      columnsToRender.forEach((col) => {
        newRow[col] = form.find(`#${col}`).val();
      });

      this.instance.row.add(newRow).draw();
      console.log("Created:", newRow);
      // TODO: Send newRow to server via AJAX
      modal.remove();
    });
  }

  handleEditEntry(rowData) {
    const columnsToShow = this.getColumnsToShow();
    const updatedRow = { ...rowData };

    columnsToShow.forEach((col) => {
      const newValue = prompt(`Edit ${col}:`, rowData[col]);
      if (newValue !== null) updatedRow[col] = newValue;
    });

    const row = this.instance.row((idx, data) => data === rowData);
    row.data(updatedRow).draw();
    console.log("Edited:", updatedRow);
    // TODO: Send updatedRow to server
  }
}
