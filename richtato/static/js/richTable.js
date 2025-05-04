class RichTable {
  constructor(
    tableId,
    apiEndpoint,
    editableColumnTitles = [],
    queryLimit = null,
    config = {},
    hiddenColumns = ["id"]
  ) {
    this.tableId = tableId;
    this.apiEndpoint = apiEndpoint;
    this.editableColumnTitles = editableColumnTitles;
    this.queryLimit = queryLimit;
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
    console.log("Input Editable columns:", this.editableColumnTitles);
    console.log("Columns:", this.columns);
    const editableSet = new Set(
      this.editableColumnTitles.map((col) => col.trim().toLowerCase())
    );

    this.editableColumns = this.columns
      .filter((col) => editableSet.has(col.title.trim().toLowerCase()))
      .map((col) => ({
        title: col.title,
        field: col.data,
      }));
  }

  async fetchData() {
    try {
      let endpoint = this.apiEndpoint;
      if (this.queryLimit !== null) {
        endpoint += `?limit=${this.queryLimit}`;
      }

      console.log("Fetching data from:", endpoint);
      const response = await fetch(endpoint);
      const data = await response.json();
      this.data = data.rows || [];

      // Always set columns (even if rows are empty)
      this.columns = (data.columns || []).map((col) => ({
        title: col.title,
        data: col.field,
      }));

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

      console.log("Select fields loaded:", this.selectFields);
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
    console.log("Opening add modal with columns:", this.editableColumns);
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
    console.log("Submitting form data:", formData);
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
          <div class="custom-modal-body"></div>
          <div class="custom-modal-footer">
            <button type="submit" class="save-button">Save</button>
          </div>
        </div>
      </div>
    `);

    const formBuilder = new RichForm(
      this.tableId,
      columns,
      initialData,
      this.selectFields
    );
    const form = formBuilder.generate();
    modal.find(".custom-modal-body").append(form);

    $("body").append(modal);

    const closeModal = () => {
      modal.remove();
      $(document).off("keydown.modalEscape.modalEnter");
    };

    // Handle Esc key to close
    $(document).on("keydown.modalEscape", (e) => {
      if (e.key === "Escape") closeModal();
    });

    // Handle Enter key to submit form
    $(document).on("keydown.modalEnter", (e) => {
      if (e.key === "Enter" && !$(e.target).is("textarea")) {
        e.preventDefault();
        form.trigger("submit");
      }
    });

    modal.find(".close-button").on("click", closeModal);

    form.on("submit", async (e) => {
      e.preventDefault();
      const formData = formBuilder.getData();

      try {
        await onSubmit(formData);
        closeModal();
      } catch (error) {
        alert(error.message);
      }
    });

    modal.find(".save-button").on("click", (e) => {
      e.preventDefault();
      form.trigger("submit");
    });
  }
}

class RichForm {
  constructor(formTableID, columns, initialData = {}, selectFields = {}) {
    this.formTableID = formTableID;
    this.columns = columns;
    this.initialData = initialData;
    this.selectFields = selectFields;
  }

  generate() {
    console.log("Form selectFields:", this.selectFields);
    console.log("Form columns:", this.columns);
    const form = $('<form class="custom-modal-form"></form>');

    this.columns.forEach((col) => {
      const fieldGroup = $('<div class="form-group"></div>');
      // Use the field property for the field name
      const fieldName = col.field;

      fieldGroup.append(`<label for="${fieldName}">${col.title}</label>`);

      // Check both the field name and data property in initialData
      const value = this.initialData[fieldName] ?? "";
      const input = this.createInput(col, value);
      fieldGroup.append(input);

      form.append(fieldGroup);

      // Special handling for specific fields
      if ((fieldName === "description") && (this.formTableID === "#expenseTable")) {
        input.on("blur", () => this.categorizeTransaction());
      }
      if (fieldName === "amount") {
        input.on("blur", () => this.computeAmount());
      }
    });

    this.form = form;
    return form;
  }

  createInput(col, value) {
    const fieldName = col.field;
    const key = fieldName.toLowerCase();

    // Handle select fields from the selectFields object
    if (this.selectFields[key]) {
      const select = $(
        `<select id="${fieldName}" name="${fieldName}" class="form-control"></select>`
      );
      const options = this.selectFields[key];

      // Match by value or label
      const match = options.find(
        (opt) => opt.label.toLowerCase() === String(value).toLowerCase() ||
          opt.value === value
      );

      if (match) {
        value = match.value;
      }

      // Add options to the select element
      options.forEach((opt) => {
        const selected = opt.value === value ? "selected" : "";
        select.append(
          `<option value="${opt.value}" ${selected}>${opt.label}</option>`
        );
      });

      return select;
    }

    // Handle date fields
    let type = "text";
    if (col.title.toLowerCase() === "date") {
      type = "date";
      if (!value) {
        const today = new Date();
        value = today.toISOString().split("T")[0];
        console.log("Setting date to today:", value);
      } else if (value) {
        try {
          value = new Date(value).toISOString().split("T")[0];
        } catch (e) {
          console.error("Invalid date value:", value);
          value = "";
        }
      }
    }

    // Prepare the value for HTML insertion by escaping it
    const safeValue = String(value).replace(/"/g, "&quot;");

    return $(
      `<input type="${type}" id="${fieldName}" name="${fieldName}" class="form-control" value="${safeValue}" />`
    );
  }

  getData() {
    const data = {};
    this.columns.forEach((col) => {
      // We use the field property for form element IDs
      const fieldName = col.field;

      // Find the form element and get its value
      const element = this.form.find(`#${fieldName}`);
      if (element.length > 0) {
        // Store the value using the field property as the key
        data[fieldName] = element.val();
      }
    });
    console.log("Collected form data:", data);
    return data;
  }

  async categorizeTransaction() {
    const description = this.form.find("#description").val();
    if (!description) return;

    try {
      const response = await fetch(`/api/expenses/categorize-transaction/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ description }),
      });

      const result = await response.json();
      console.log("Categorization result:", result);
      if (result.category) {
        // Use lowercase 'category' to match the field name
        const $categoryField = this.form.find("#Category");
        console.log(
          "Found category field:",
          $categoryField.length > 0,
          $categoryField
        );

        if ($categoryField.length === 0) {
          console.warn("⚠️ Category select field not found in the form!");
        } else {
          $categoryField.val(result.category);
          console.log("✅ Set category value to:", result.category);
          console.log(
            "🔍 Current selected option:",
            $categoryField.find("option:selected").text()
          );
        }
      }
    } catch (error) {
      console.error("Failed to categorize transaction:", error);
    }
  }

  computeAmount() {
    const amountInput = this.form.find("#amount");
    let balance = amountInput.val();

    if (!balance) return;

    if (balance.startsWith("=")) {
      try {
        balance = eval(balance.slice(1));
        console.log("Evaluated formula:", balance);
      } catch (error) {
        console.error("Invalid formula:", error);
        return;
      }
    } else {
      try {
        balance = eval(balance);
      } catch (error) {
        console.error("Invalid number input:", error);
        return;
      }
    }

    balance = parseFloat(balance).toFixed(2);
    amountInput.val(balance);
    console.log("Updated amount field with:", balance);
  }
}
