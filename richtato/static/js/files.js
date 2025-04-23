async function getCardTypes() {
  try {
    const response = await fetch("/api/card-banks/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch card banks. Status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Fetched card banks:", data);
    return data;
  } catch (error) {
    console.error("Error fetching card banks:", error);
    return [];
  }
}

async function initializeFileManager() {
  const cardBanks = await getCardTypes();

  // Create the fileManager instance after fetching cardBanks
  const fileManager = new FileManager(
    "files-boxes",
    "files-statistics",
    cardBanks
  );

  // Define the handleFiles function inside to ensure fileManager is available
  function handleFiles(files) {
    Array.from(files).forEach((file) => fileManager.addFile(file));
  }

  // Now, set up event listeners after fileManager is initialized
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragging");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragging");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragging");
    const files = e.dataTransfer.files;
    handleFiles(files);
  });

  dropZone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    const files = fileInput.files;
    handleFiles(files);
  });

  const fileUploadButton = document.getElementById("file-upload-button");
  fileUploadButton.addEventListener("click", () => {
    fileManager.uploadFiles();
  });
}

// Initialize the file manager
initializeFileManager();

class File {
  constructor(file, cardBanks, onRemoveCallback) {
    this.path = URL.createObjectURL(file); // Temporary path for preview
    this.name = file.name;
    this.file_size = file.size;
    this.file = file;
    this.cardBanks = cardBanks;
    this.onRemoveCallback = onRemoveCallback;
    this.fileBox = null;
    this.processingSpinner = null;
  }

  // Create a dropdown for selecting the card account
  createDropdown() {
    const dropdown = document.createElement("select");
    dropdown.classList.add("card-account-dropdown");

    this.cardBanks.forEach(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      dropdown.appendChild(option);
    });

    return dropdown;
  }

  // Create a remove button for this file
  createRemoveButton() {
    const removeButton = document.createElement("button");
    removeButton.innerHTML = "&times;";
    removeButton.classList.add("remove-button");

    // Use the callback provided by FileManager
    removeButton.addEventListener("click", (e) => {
      e.stopPropagation();
      if (this.onRemoveCallback) {
        this.onRemoveCallback(this);
      }
    });

    return removeButton;
  }

  // Create the file box element with file details and a remove button
  createFileBox() {
    const fileBox = document.createElement("div");
    fileBox.id = `file-box-${this.name}`;
    fileBox.classList.add("file-box");
    fileBox.style.position = "relative";
    this.fileBox = fileBox;

    // Create the remove button (X mark)
    const removeButton = this.createRemoveButton();
    fileBox.appendChild(removeButton);

    const cardBody = document.createElement("div");
    cardBody.classList.add("file-box-card-body");
    this.cardBody = cardBody;

    const img = document.createElement("img");
    if (this.name.endsWith(".xls") || this.name.endsWith(".xlsx")) {
      img.src = "../static/images/excel.svg";
    } else {
      img.src = "../static/images/csv.svg";
    }
    img.alt = this.name;

    const fileName = document.createElement("p");
    fileName.textContent = this.name;

    const fileSize = document.createElement("p");
    fileSize.textContent = `${(this.file_size / 1024).toFixed(2)} KB`;
    fileSize.classList.add("file-size");

    // Create dropdown from this instance
    this.dropdown = this.createDropdown();

    // Append elements to the cardBody
    cardBody.appendChild(img);
    cardBody.appendChild(fileName);
    cardBody.appendChild(fileSize);
    cardBody.appendChild(this.dropdown);

    // Append the cardBody to the fileBox
    fileBox.appendChild(cardBody);

    return fileBox;
  }

  setProcessing() {
    if (!this.processingSpinner) {
      this.processingSpinner = document.createElement("p");
      this.processingSpinner.classList.add("spinner");
      this.processingSpinner.innerText = "Processing...";
      this.cardBody.appendChild(this.processingSpinner);
    }
  }

  clearProcessing() {
    if (this.processingSpinner) {
      this.processingSpinner.remove();
      this.processingSpinner = null;
    }
  }
}

class FileManager {
  constructor(filesContainerId, statisticsContainerId, cardBanks) {
    this.filesContainer = document.getElementById(filesContainerId);
    this.statisticsContainer = document.getElementById(statisticsContainerId);
    this.uploadedFiles = []; // Stores instances of File
    this.cardBanks = cardBanks;
  }

  // Validate if the file is of a valid type (Excel or CSV)
  isValidFileType(file) {
    const validTypes = [
      "application/vnd.ms-excel", // .xls
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
      "text/csv", // .csv
    ];
    return validTypes.includes(file.type);
  }

  // Check if the file is a duplicate (based on name and size)
  isDuplicateFile(file) {
    return this.uploadedFiles.some(
      (f) => f.name === file.name && f.file_size === file.size
    );
  }

  // Add a new file and display it in the UI
  addFile(file) {
    if (!this.isValidFileType(file)) {
      alert(`${file.name} is not a valid Excel or CSV file.`);
      return;
    }

    if (this.isDuplicateFile(file)) {
      alert(`${file.name} has already been uploaded.`);
      return;
    }

    // Create a new File instance with a callback to removeFile
    const newFile = new File(file, this.cardBanks, (fileToRemove) => {
      this.removeFile(fileToRemove);
    });
    this.uploadedFiles.push(newFile);

    // Use the File's createFileBox method to generate the UI element
    const fileBox = newFile.createFileBox();
    this.filesContainer.appendChild(fileBox);

    // Show the statistics container if there are files
    this.updateStatisticsVisibility();
  }

  removeFile(file) {
    this.uploadedFiles = this.uploadedFiles.filter((f) => f !== file);

    // Remove the file box from the UI
    const fileBox = document.getElementById(`file-box-${file.name}`);
    if (fileBox) {
      fileBox.remove();
    }

    // Update the visibility of the statistics container
    this.updateStatisticsVisibility();
  }

  // Update the visibility of the statistics container based on file count
  updateStatisticsVisibility() {
    if (this.uploadedFiles.length === 0) {
      this.statisticsContainer.style.display = "none";
    } else {
      this.statisticsContainer.style.display = "flex";
    }
  }

  async uploadFiles() {
    const csrftoken = getCSRFToken();
    for (let fileObj of this.uploadedFiles.slice()) {
      fileObj.setProcessing();

      const formData = new FormData();
      formData.append("files", fileObj.file);
      formData.append("card_banks", fileObj.dropdown.value);
      formData.append("file_names", fileObj.name);
      formData.append(
        "card_names",
        fileObj.dropdown.options[fileObj.dropdown.selectedIndex].textContent
      );

      try {
        const response = await fetch("/expense/upload-card-statements/", {
          method: "POST",
          body: formData,
          headers: {
            "X-CSRFToken": csrftoken,
          },
          credentials: "include",
        });

        if (!response.ok) {
          throw new Error(
            `Failed to upload ${fileObj.name}: ${response.status}`
          );
        }

        // Remove from UI and memory after successful upload
        this.removeFile(fileObj);
      } catch (error) {
        console.error("Upload failed for file:", fileObj.name, error);
        fileObj.clearProcessing(); // Let user retry or remove
        alert(`Failed to upload ${fileObj.name}. Please try again.`);
      }
    }
    alert("All files have been uploaded successfully!");
  }
}
