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
    const columnsToRender = this.columns.filter(
      (col) => col.data.toLowerCase() !== "id"
    );
    console.log("Columns to Render", columnsToRender);

    // Create modal overlay
    const modalTitle = "Add New Entry";
    const modal = $(`
        <div class="custom-modal-overlay">
          <div class="custom-modal">
            <div class="custom-modal-header">
              <h3>${modalTitle}</h3>
              <span class="close-button">&times;</span>
            </div>
            <form class="custom-modal-form">
              <!-- Form content goes here -->
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
    modal.find(".close-button").on("click", () => modal.remove());
    $(document).on("keydown.modalEscape", (e) => {
      if (e.key === "Escape") {
        modal.remove();
        $(document).off("keydown.modalEscape");
      }
    });

    modal.find(".save-button").on("click", async (e) => {
      e.preventDefault();
      const formData = {};
      columnsToRender.forEach((col) => {
        formData[col.data] = form.find(`#${col.data}`).val();
      });

      try {
        const response = await fetch("/account/entry/create/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
          },
          body: JSON.stringify(formData),
        });
        const newEntry = await response.json();
        this.instance.row.add(newEntry).draw();
        console.log("Created:", newEntry);
      } catch (err) {
        console.error("Add error:", err);
      }

      modal.remove();
    });
  }

  handleEditEntry(rowData) {
    const columnsToEdit = this.columns.filter(
      (col) => col.data.toLowerCase() !== "id"
    );
    const updatedRow = { ...rowData };

    const modal = $(`
      <div class="custom-modal-overlay">
        <div class="custom-modal">
          <div class="custom-modal-header">
            <h3>Edit Entry</h3>
            <span class="close-button">&times;</span>
          </div>
          <form class="custom-modal-form"></form>
          <div class="custom-modal-footer">
            <button type="submit" class="save-button">Save</button>
          </div>
        </div>
      </div>
    `);

    const form = modal.find("form");

    columnsToEdit.forEach((col) => {
      const field = $(`
        <div class="form-group">
          <label for="${col.data}">${col.title}</label>
          <input type="text" id="${col.data}" name="${
        col.data
      }" class="form-control" value="${rowData[col.data]}" />
        </div>
      `);
      form.append(field);
    });

    $("body").append(modal);
    modal.find(".close-button").on("click", () => modal.remove());

    modal.find(".save-button").on("click", async (e) => {
      e.preventDefault();
      columnsToEdit.forEach((col) => {
        updatedRow[col.data] = form.find(`#${col.data}`).val();
      });

      try {
        const response = await fetch(`/api/entry/update/${rowData.id}/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
          },
          body: JSON.stringify(updatedRow),
        });
        const updated = await response.json();
        this.instance
          .row((_, data) => data.id === updated.id)
          .data(updated)
          .draw();
        console.log("Updated:", updated);
      } catch (err) {
        console.error("Edit error:", err);
      }

      modal.remove();
    });
  }

  handleDeleteEntry() {
    const selectedRow = this.instance.row({ selected: true });
    const rowData = selectedRow.data();

    if (!rowData) {
      alert("Select a row to delete.");
      return;
    }

    if (confirm("Are you sure you want to delete this row?")) {
      fetch(`/api/entry/delete/${rowData.id}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
        },
      })
        .then((res) => res.json())
        .then((result) => {
          selectedRow.remove().draw();
          console.log("Deleted:", result);
        })
        .catch((err) => console.error("Delete error:", err));
    }
  }
}
