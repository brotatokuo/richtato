class RichTable {
  constructor(
    tableId,
    apiEndpoint,
    editableColumnTitles = [],
    config = {},
    hiddenColumns = ["id"]
  ) {
    this.tableId = tableId;
    this.apiEndpoint = apiEndpoint;
    this.editableColumnTitles = editableColumnTitles;
    this.selectFields = {};
    this.fetchSelectFields();
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

  computeEditableColumns() {
    const editableSet = new Set(
      this.editableColumnTitles.map((col) => col.toLowerCase())
    );
    this.editableColumns = this.columns.filter((col) =>
      editableSet.has(col.title.toLowerCase())
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
    this.computeEditableColumns();

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
        action: () => this.openAddModal(),
      },
      {
        text: "Edit",
        action: () => {
          const selectedData = this.instance.row({ selected: true }).data();
          if (selectedData) {
            this.openEditModal(selectedData);
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

  openAddModal(onSubmit) {
    this.showEntryModal({
      title: "Add New Entry",
      columns: this.editableColumns,
      initialData: {},
      onSubmit: async (formData) => {
        try {
          const added = await this.submitAddEntry(formData);
          this.fetchData(); // Optional: or update UI immediately
          onSubmit?.(added);
        } catch (error) {
          alert(error.message);
        }
      },
    });
  }

  openEditModal(rowData) {
    this.showEntryModal({
      title: "Edit Entry",
      columns: this.editableColumns,
      initialData: rowData,
      onSubmit: async (updatedData) => {
        try {
          await this.submitEditEntry(rowData.id, updatedData);
        } catch (error) {
          alert(error.message);
        }
      },
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
      this.fetchData();
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

  showEntryModal({ title, columns, initialData = {}, onSubmit }) {
    const modal = $(`
      <div class="custom-modal-overlay">
        <div class="custom-modal">
          <div class="custom-modal-header">
            <h3>${title}</h3>
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

    columns.forEach((col) => {
      let value = initialData[col.data] ?? "";

      const fieldGroup = $(`<div class="form-group"></div>`);
      fieldGroup.append(`<label for="${col.data}">${col.title}</label>`);

      if (this.selectFields[col.data]) {
        const options = this.selectFields[col.data];

        const match = options.find(
          (opt) => opt.label.toLowerCase() === value?.toLowerCase()
        );
        if (match) value = match.value;

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

    const closeModal = () => {
      modal.remove();
      $(document).off("keydown.modalEscape");
    };

    $(document).on("keydown.modalEscape", (e) => {
      if (e.key === "Escape") closeModal();
    });

    modal.find(".close-button").on("click", closeModal);

    // Handle form submit (Enter key or Save button)
    form.on("submit", async (e) => {
      e.preventDefault();
      const formData = {};
      columns.forEach((col) => {
        formData[col.data] = form.find(`#${col.data}`).val();
      });

      try {
        await onSubmit(formData);
        closeModal();
      } catch (error) {
        alert(error.message);
      }
    });

    // Optional: still bind Save button in case default behavior is overridden
    modal.find(".save-button").on("click", (e) => {
      e.preventDefault();
      form.trigger("submit");
    });
  }
}
