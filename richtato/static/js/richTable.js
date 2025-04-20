class RichTable {
  constructor(
    tableId,
    apiEndpoint,
    editableColumns,
    config = {},
    hiddenColumns = ["id"]
  ) {
    this.tableId = tableId;
    this.apiEndpoint = apiEndpoint;
    this.editableColumns = editableColumns;
    this.selectFields = {};
    this.data = null;
    this.fetchSelectFields();
    this.columns = null;
    this.hiddenColumns = hiddenColumns;

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
    this.instance = null;
    this.fetchData();
  }

  computeVisibleColumns() {
    this.visibleColumns = this.columns.filter(
      (col) => !this.hiddenColumns.includes(col.data)
    );
  }

  async fetchData() {
    try {
      console.log("Fetching data from:", this.apiEndpoint);
      const response = await fetch(this.apiEndpoint);
      const data = await response.json();
      this.data = data;

      if (this.data.length > 0) {
        this.columns = Object.keys(this.data[0]).map((key) => ({
          title: key.charAt(0).toUpperCase() + key.slice(1),
          data: key,
        }));
      }

      console.log("Fetched data:", this.data);
      this.renderTable();
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  }

  async fetchSelectFields() {
    try {
      const response = await fetch(`${this.apiEndpoint}field-choices/`);
      if (!response.ok) throw new Error("Failed to fetch select field data");

      const data = await response.json();
      this.selectFields = {};

      // Loop over the keys and build selectFields
      for (const [field, options] of Object.entries(data)) {
        this.selectFields[field] = options.map((opt) => ({
          value: opt.value,
          label: opt.label,
        }));
      }

      console.log("Fetched select fields:", this.selectFields);
    } catch (error) {
      console.error("Error loading select field data:", error);
    }
  }

  renderTable() {
    this.computeVisibleColumns();

    const tableElement = $(this.tableId);
    if ($.fn.DataTable.isDataTable(this.tableId)) {
      tableElement.DataTable().clear().destroy();
    }

    const thead = tableElement.find("thead");
    const tbody = tableElement.find("tbody");
    thead.empty();
    tbody.empty();

    const headerRow = $("<tr></tr>");
    headerRow.append($("<th></th>")); // Checkbox column

    this.columns.forEach((col) => {
      const th = $("<th></th>").text(col.title);
      if (this.hiddenColumns.includes(col.data)) {
        th.css("display", "none");
      }
      headerRow.append(th);
    });

    thead.append(headerRow);

    this.data.forEach((row) => {
      const tr = $("<tr></tr>");
      tr.append("<td></td>"); // Checkbox cell

      this.columns.forEach((col) => {
        const td = $("<td></td>").text(row[col.data] || "");
        if (this.hiddenColumns.includes(col.data)) {
          td.css("display", "none");
        }
        tr.append(td);
      });

      tbody.append(tr);
    });

    const allDTColumns = [
      {
        data: null,
        defaultContent: "",
        orderable: false,
        className: "select-checkbox",
      },
      ...this.columns.map((col) => ({
        data: col.data,
        visible: !this.hiddenColumns.includes(col.data),
      })),
    ];

    this.config.columns = allDTColumns;
    this.addTableButtons();
    this.instance = tableElement.DataTable(this.config);
  }

  addTableButtons() {
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
            this.handleDeleteEntry(rowData);
          } else {
            alert("Please select a row to delete.");
          }
        },
      },
    ];
  }

  handleAddEntry() {
    this.showAddModal(async (formData) => {
      try {
        const newEntry = await this.submitAddEntry(formData);
        this.instance.row.add(newEntry).draw();
        console.log("Created:", newEntry);
      } catch (err) {
        console.error("Add error:", err);
      }
    });
  }

  showAddModal(onSubmit) {
    const modalTitle = "Add New Entry";
    const modal = $(`
      <div class="custom-modal-overlay">
        <div class="custom-modal">
          <div class="custom-modal-header">
            <h3>${modalTitle}</h3>
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
    console.log("Form columns:", this.visibleColumns);

    this.visibleColumns.forEach((col) => {
      const field = $(`
        <div class="form-group">
          <label for="${col.data}">${col.title || col.data}</label>
          <input type="text" id="${col.data}" name="${
        col.data
      }" class="form-control" />
        </div>
      `);
      form.append(field);
    });

    $("body").append(modal);

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
      this.visibleColumns.forEach((col) => {
        formData[col.data] = form.find(`#${col.data}`).val();
      });

      await onSubmit(formData);
      modal.remove();
    });
  }

  async submitAddEntry(formData) {
    const response = await fetch(this.apiEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to add entry: ${error}`);
    }

    return await response.json();
  }

  handleEditEntry(rowData) {
    const editableSet = new Set(
      this.editableColumns.map((col) => col.toLowerCase())
    );
    const columnsToEdit = this.columns.filter((col) =>
      editableSet.has(col.title.toLowerCase())
    );

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
      let value = rowData[col.data] ?? "";

      const fieldGroup = $(`<div class="form-group"></div>`);
      fieldGroup.append(`<label for="${col.data}">${col.title}</label>`);

      if (this.selectFields[col.data]) {
        const options = this.selectFields[col.data];

        // If value is label, find matching value
        const found = options.find(
          (opt) => opt.label.toLowerCase() === value.toLowerCase()
        );
        if (found) {
          value = found.value;
        }

        const select = $(
          `<select id="${col.data}" name="${col.data}" class="form-control"></select>`
        );

        options.forEach((opt) => {
          const selected = opt.value === value ? "selected" : "";
          select.append(
            `<option value="${opt.value}" ${selected}>${opt.label}</option>`
          );
        });

        fieldGroup.append(select);
      } else {
        const input = $(
          `<input type="text" id="${col.data}" name="${col.data}" class="form-control" value="${value}" />`
        );
        fieldGroup.append(input);
      }

      form.append(fieldGroup);
    });

    $("body").append(modal);

    this.bindEditKeyboardEvents(modal);
    this.bindEditFormSubmission(modal, form, columnsToEdit, rowData);
  }

  bindEditKeyboardEvents(modal) {
    modal.find(".close-button").on("click", () => modal.remove());

    $(document).on("keydown.modalEscape", (e) => {
      if (e.key === "Escape") {
        modal.remove();
        $(document).off("keydown.modalEscape");
      }
    });
  }

  bindEditFormSubmission(modal, form, columnsToEdit, rowData) {
    modal.find(".save-button").on("click", async (e) => {
      e.preventDefault();
      const updatedData = {};

      columnsToEdit.forEach((col) => {
        updatedData[col.data] = form.find(`#${col.data}`).val();
      });
      console.log("Updated data:", updatedData);
      await this.submitEditEntry(rowData.id, updatedData);
      this.fetchData();
      modal.remove();
    });
  }

  async submitEditEntry(id, updatedData) {
    try {
      const response = await fetch(`${this.apiEndpoint}${id}/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify(updatedData),
      });

      if (!response.ok) {
        throw new Error("Failed to update entry");
      }

      const updated = await response.json();
      this.instance
        .row((_, data) => data.id === updated.id)
        .data(updated)
        .draw();
      console.log("Updated:", updated);
    } catch (err) {
      console.error("Edit error:", err);
    }
  }

  handleDeleteEntry() {
    const selectedRow = this.instance.row({ selected: true });
    const rowData = selectedRow.data();

    if (!rowData) {
      alert("Select a row to delete.");
      return;
    }

    if (
      confirm("Deleting this will delete all associated data. Are you sure?")
    ) {
      console.log("Deleting row with ID:", rowData.id);
      fetch(`${this.apiEndpoint}${rowData.id}/`, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": getCSRFToken(),
        },
      })
        .then((res) => {
          if (!res.ok) {
            throw new Error("Failed to delete entry");
          }
          // Success - remove from table
          selectedRow.remove().draw();
          console.log("Deleted row with ID:", rowData.id);
        })
        .catch((err) => console.error("Delete error:", err));
    }
  }
}
