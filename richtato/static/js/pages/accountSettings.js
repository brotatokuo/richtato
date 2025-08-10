// Modern Account Tiles Manager
class AccountTilesManager {
  constructor() {
    console.log('Initializing AccountTilesManager...');
    this.cardAccountsContainer = document.getElementById('card-accounts-tiles');
    this.checkingAccountsContainer = document.getElementById('checking-accounts-tiles');
    this.savingsAccountsContainer = document.getElementById('savings-accounts-tiles');
    this.investmentAccountsContainer = document.getElementById('investment-accounts-tiles');
    this.retirementAccountsContainer = document.getElementById('retirement-accounts-tiles');
    this.essentialCategoriesContainer = document.getElementById('essential-categories-tiles');
    this.nonessentialCategoriesContainer = document.getElementById('nonessential-categories-tiles');
    this.modal = document.getElementById('account-modal');
    this.currentAccount = null;
    this.currentAccountType = null;

    console.log('Card accounts container found:', !!this.cardAccountsContainer);
    console.log('Checking accounts container found:', !!this.checkingAccountsContainer);
    console.log('Savings accounts container found:', !!this.savingsAccountsContainer);
    console.log('Investment accounts container found:', !!this.investmentAccountsContainer);
    console.log('Retirement accounts container found:', !!this.retirementAccountsContainer);
    console.log('Essential categories container found:', !!this.essentialCategoriesContainer);
    console.log('Non-essential categories container found:', !!this.nonessentialCategoriesContainer);

    this.init();
  }

  async init() {
    this.setupEventListeners();
    await Promise.all([
      this.loadCardAccounts(),
      this.loadAccounts(),
      this.loadCategories()
    ]);
  }

  setupEventListeners() {
    // Modal event listeners
    const modalClose = document.getElementById('modal-close');
    const modalEdit = document.getElementById('modal-edit');
    const modalDelete = document.getElementById('modal-delete');

    // Close modal
    modalClose?.addEventListener('click', () => this.closeModal());
    this.modal?.addEventListener('click', (e) => {
      if (e.target === this.modal) this.closeModal();
    });

    // Handle edit and delete actions
    modalEdit?.addEventListener('click', () => this.handleEdit());
    modalDelete?.addEventListener('click', () => this.handleDelete());

    // ESC key to close modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal?.classList.contains('show')) {
        this.closeModal();
      }
    });
  }

  async loadCardAccounts() {
    try {
      console.log('Loading card accounts...');
      const response = await fetch('/api/card-accounts/');
      const data = await response.json();
      console.log('Card accounts data:', data);
      this.renderCardAccountTiles(data.rows || []);
    } catch (error) {
      console.error('Error loading card accounts:', error);
    }
  }

  async loadAccounts() {
    try {
      console.log('Loading accounts...');
      const response = await fetch('/api/accounts/');
      const data = await response.json();
      console.log('Accounts data:', data);
      this.renderAccountTiles(data.rows || []);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  }

  async loadCategories() {
    try {
      console.log('Loading categories...');
      const response = await fetch('/api/categories/');
      const data = await response.json();
      console.log('Categories data:', data);
      this.renderCategoryTiles(data.rows || []);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  }

  renderCardAccountTiles(cardAccounts) {
    console.log('Rendering card account tiles, container found:', !!this.cardAccountsContainer);
    console.log('Card accounts to render:', cardAccounts);

    if (!this.cardAccountsContainer) {
      console.error('Card accounts container not found!');
      return;
    }

    // Clear existing content
    this.cardAccountsContainer.innerHTML = '';

    // Add existing card accounts
    cardAccounts.forEach(card => {
      console.log('Creating tile for card:', card);
      const tile = this.createCardAccountTile(card);
      this.cardAccountsContainer.appendChild(tile);
    });

    // Add "Add New" tile
    const addTile = this.createAddAccountTile('card');
    this.cardAccountsContainer.appendChild(addTile);

    console.log('Finished rendering card account tiles');
  }

  renderAccountTiles(accounts) {
    console.log('Rendering grouped account tiles');
    console.log('Accounts to render:', accounts);

    const containers = {
      checking: this.checkingAccountsContainer,
      savings: this.savingsAccountsContainer,
      investment: this.investmentAccountsContainer,
      retirement: this.retirementAccountsContainer
    };

    // Check if all containers exist
    const missingContainers = Object.entries(containers)
      .filter(([type, container]) => !container)
      .map(([type]) => type);

    if (missingContainers.length > 0) {
      console.error('Account containers not found:', missingContainers);
      return;
    }

    // Clear existing content in all containers
    Object.values(containers).forEach(container => {
      container.innerHTML = '';
    });

    // Group accounts by type
    const groupedAccounts = {
      checking: [],
      savings: [],
      investment: [],
      retirement: []
    };

    accounts.forEach(account => {
      const type = account.type?.toLowerCase();
      if (groupedAccounts[type]) {
        groupedAccounts[type].push(account);
      } else {
        // Default to checking if type is unknown
        groupedAccounts.checking.push(account);
      }
    });

    // Render accounts in each group
    Object.entries(groupedAccounts).forEach(([type, typeAccounts]) => {
      const container = containers[type];

      // Add existing accounts for this type
      typeAccounts.forEach(account => {
        console.log(`Creating tile for ${type} account:`, account);
        const tile = this.createAccountTile(account);
        container.appendChild(tile);
      });

      // Add "Add New" tile for each type
      const addTile = this.createAddAccountTile('account', type);
      container.appendChild(addTile);
    });

    console.log('Finished rendering grouped account tiles');
  }

  renderCategoryTiles(categories) {
    console.log('Rendering category tiles');
    console.log('Essential container found:', !!this.essentialCategoriesContainer);
    console.log('Non-essential container found:', !!this.nonessentialCategoriesContainer);
    console.log('Categories to render:', categories);

    if (!this.essentialCategoriesContainer || !this.nonessentialCategoriesContainer) {
      console.error('Category containers not found!');
      return;
    }

    // Clear existing content
    this.essentialCategoriesContainer.innerHTML = '';
    this.nonessentialCategoriesContainer.innerHTML = '';

    // Separate categories by type - be more specific to avoid cross-matching
    const essentialCategories = categories.filter(cat => cat.type.toLowerCase() === 'essential');
    const nonessentialCategories = categories.filter(cat => cat.type.toLowerCase().includes('non'));

    console.log('Essential categories:', essentialCategories);
    console.log('Non-essential categories:', nonessentialCategories);

    // Add essential categories
    essentialCategories.forEach(category => {
      console.log('Creating tile for essential category:', category);
      const tile = this.createCategoryTile(category);
      this.essentialCategoriesContainer.appendChild(tile);
    });

    // Add non-essential categories
    nonessentialCategories.forEach(category => {
      console.log('Creating tile for non-essential category:', category);
      const tile = this.createCategoryTile(category);
      this.nonessentialCategoriesContainer.appendChild(tile);
    });

    // Add "Add New" tiles to both sections
    const addEssentialTile = this.createAddCategoryTile('essential');
    this.essentialCategoriesContainer.appendChild(addEssentialTile);

    const addNonessentialTile = this.createAddCategoryTile('nonessential');
    this.nonessentialCategoriesContainer.appendChild(addNonessentialTile);

    console.log('Finished rendering category tiles');
  }

  createCardAccountTile(cardAccount) {
    const tile = document.createElement('div');
    tile.className = 'account-tile card-account-tile';
    tile.onclick = () => this.showModal(cardAccount, 'card');

    tile.innerHTML = `
      <div class="account-tile-header">
        <div class="account-tile-icon card">
          <i class="fas fa-credit-card"></i>
        </div>
        <div class="account-tile-info">
          <h3>${cardAccount.name}</h3>
          <p>${cardAccount.bank}</p>
        </div>
      </div>
      <div class="account-tile-body">
        <div class="account-tile-type">Credit Card</div>
      </div>
      <div class="account-tile-footer">
        <div class="account-tile-status">Active</div>
      </div>
    `;

    return tile;
  }

  createAccountTile(account) {
    const tile = document.createElement('div');
    tile.className = 'account-tile';
    tile.onclick = () => this.showModal(account, 'account');

    const balance = account.balance && account.balance !== '$0.00' ? account.balance : 'No balance';

    tile.innerHTML = `
      <div class="account-tile-header">
        <div class="account-tile-icon bank">
          <i class="${this.getAccountTypeIcon(account.type.toLowerCase())}"></i>
        </div>
        <div class="account-tile-info">
          <h3>${account.name}</h3>
          <p>${account.entity}</p>
        </div>
      </div>
      <div class="account-tile-body">
        <div class="account-tile-balance">${balance}</div>
        <div class="account-tile-type">${account.type}</div>
      </div>
      <div class="account-tile-footer">
        <div class="account-tile-status">${account.date ? `Updated ${account.date}` : 'No recent update'}</div>
      </div>
    `;

    return tile;
  }

  createAddAccountTile(type, accountType = null) {
    const tile = document.createElement('div');
    tile.className = 'add-account-tile';

    if (type === 'card') {
      tile.onclick = () => this.showAddCardAccountModal();
      tile.innerHTML = `
        <i class="fas fa-plus"></i>
        <h3>Add Card Account</h3>
        <p>Add a new credit card</p>
      `;
    } else if (accountType) {
      const typeInfo = {
        checking: { icon: 'fas fa-university', title: 'Add Checking', desc: 'Add a checking account' },
        savings: { icon: 'fas fa-piggy-bank', title: 'Add Savings', desc: 'Add a savings account' },
        investment: { icon: 'fas fa-chart-pie', title: 'Add Investment', desc: 'Add an investment account' },
        retirement: { icon: 'fas fa-chart-line', title: 'Add Retirement', desc: 'Add a retirement account' }
      };

      const info = typeInfo[accountType] || typeInfo.checking;
      tile.onclick = () => this.showAddAccountModal(accountType);
      tile.innerHTML = `
        <i class="${info.icon}"></i>
        <h3>${info.title}</h3>
        <p>${info.desc}</p>
      `;
    } else {
      tile.onclick = () => this.showAddAccountModal();
      tile.innerHTML = `
        <i class="fas fa-plus"></i>
        <h3>Add Account</h3>
        <p>Add a new bank account</p>
      `;
    }

    return tile;
  }

  createCategoryTile(category) {
    const tile = document.createElement('div');
    tile.className = 'category-tile';
    tile.onclick = () => this.showModal(category, 'category');

    const typeClass = category.type.toLowerCase().replace(' ', '');
    const categoryIcon = this.getCategoryIcon(category.name);

    tile.innerHTML = `
      <div class="category-tile-header">
        <div class="category-tile-icon ${typeClass}">
          <i class="${categoryIcon}"></i>
        </div>
      </div>
      <div class="category-tile-body">
        <div class="category-tile-info">
          <h3>${category.name}</h3>
        </div>
      </div>
    `;

    return tile;
  }

  createAddCategoryTile(type = 'category') {
    const tile = document.createElement('div');
    tile.className = 'add-category-tile';
    tile.onclick = () => this.showAddCategoryModal(type);

    if (type === 'essential') {
      tile.innerHTML = `
        <i class="fas fa-plus"></i>
        <h3>Add Essential</h3>
        <p>Add necessary expense category</p>
      `;
    } else if (type === 'nonessential') {
      tile.innerHTML = `
        <i class="fas fa-plus"></i>
        <h3>Add Non-Essential</h3>
        <p>Add discretionary category</p>
      `;
    } else {
      tile.innerHTML = `
        <i class="fas fa-plus"></i>
        <h3>Add Category</h3>
        <p>Create a new expense category</p>
      `;
    }

    return tile;
  }

  getBankDisplayName(bankCode) {
    const bankNames = {
      'american_express': 'American Express',
      'bank_of_america': 'Bank of America',
      'bilt': 'BILT',
      'chase': 'Chase',
      'citibank': 'Citibank',
      'marcus': 'Marcus by Goldman Sachs',
      'other': 'Other'
    };
    return bankNames[bankCode] || bankCode;
  }

  getAccountTypeDisplayName(typeCode) {
    const typeNames = {
      'checking': 'Checking',
      'savings': 'Savings',
      'retirement': 'Retirement',
      'investment': 'Investment'
    };
    return typeNames[typeCode] || typeCode;
  }

  getAccountTypeIcon(typeCode) {
    const typeIcons = {
      'checking': 'fas fa-university',
      'savings': 'fas fa-piggy-bank',
      'retirement': 'fas fa-chart-line',
      'investment': 'fas fa-chart-pie'
    };
    return typeIcons[typeCode] || 'fas fa-university';
  }

  getCategoryIcon(categoryName) {
    const categoryIcons = {
      'Travel': 'fas fa-plane',
      'Shopping': 'fas fa-shopping-bag',
      'Online Shopping': 'fas fa-laptop',
      'Groceries': 'fas fa-shopping-cart',
      'Entertainment': 'fas fa-film',
      'Utilities': 'fas fa-bolt',
      'Housing': 'fas fa-home',
      'Medical': 'fas fa-medkit',
      'Education': 'fas fa-graduation-cap',
      'Savings': 'fas fa-piggy-bank',
      'Gifts': 'fas fa-gift',
      'Dining': 'fas fa-utensils',
      'Investments': 'fas fa-chart-line',
      'Subscriptions': 'fas fa-sync',
      'Charity': 'fas fa-heart',
      'Pet': 'fas fa-paw',
      'Wholesale': 'fas fa-boxes',
      'Car': 'fas fa-car',
      'Phone': 'fas fa-mobile-alt',
      'Miscellaneous': 'fas fa-ellipsis-h',
      'Payments': 'fas fa-credit-card',
      'Unknown': 'fas fa-question'
    };
    return categoryIcons[categoryName] || 'fas fa-tag';
  }


  showModal(account, type) {
    this.currentAccount = account;
    this.currentAccountType = type;

    const modalIcon = document.getElementById('modal-icon');
    const modalTitle = document.getElementById('modal-title');
    const modalSubtitle = document.getElementById('modal-subtitle');

    // Update modal content
    modalTitle.textContent = account.name;

    if (type === 'card') {
      modalIcon.className = 'account-modal-icon card';
      modalIcon.innerHTML = '<i class="fas fa-credit-card"></i>';
      modalSubtitle.textContent = account.bank;
    } else if (type === 'category') {
      modalIcon.className = 'account-modal-icon category';
      modalIcon.innerHTML = `<i class="${this.getCategoryIcon(account.name)}"></i>`;
      modalSubtitle.textContent = `${account.type} Category`;
    } else {
      modalIcon.className = 'account-modal-icon bank';
      modalIcon.innerHTML = `<i class="${this.getAccountTypeIcon(account.type.toLowerCase())}"></i>`;
      modalSubtitle.textContent = `${account.entity} • ${account.type}`;
    }

    // Show modal
    this.modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  closeModal() {
    this.modal.classList.remove('show');
    document.body.style.overflow = '';
    this.currentAccount = null;
    this.currentAccountType = null;
  }

  handleEdit() {
    if (!this.currentAccount) return;

    if (this.currentAccountType === 'card') {
      this.editCardAccount(this.currentAccount.id);
    } else {
      this.editAccount(this.currentAccount.id);
    }
    this.closeModal();
  }

  handleDelete() {
    if (!this.currentAccount) return;

    if (this.currentAccountType === 'card') {
      this.deleteCardAccount(this.currentAccount.id);
    } else {
      this.deleteAccount(this.currentAccount.id);
    }
    this.closeModal();
  }

  showAddCardAccountModal() {
    const modal = document.getElementById('add-card-modal');
    if (modal) {
      // Load bank options for the dropdown
      this.loadCardBankOptions();

      // Set up event listeners if not already done
      this.setupAddCardModalEventListeners();
      modal.style.display = 'flex';
    }
  }

  showAddAccountModal(accountType = null) {
    const modal = document.getElementById('add-account-modal');
    if (modal) {
      // Load account type options for the dropdown
      this.loadAccountTypeOptions().then(() => {
        // Pre-select account type if provided after options are loaded
        if (accountType) {
          const typeSelect = document.getElementById('account-type');
          if (typeSelect) {
            typeSelect.value = accountType;
          }
        }
      });

      // Set up event listeners if not already done
      this.setupAddAccountModalEventListeners();
      modal.style.display = 'flex';
    }
  }

  showAddCategoryModal(type = 'category') {
    const modal = document.getElementById('add-category-modal');
    if (modal) {
      // Pre-select category type if provided
      if (type === 'essential' || type === 'nonessential') {
        const typeSelect = document.getElementById('category-type');
        if (typeSelect) {
          typeSelect.value = type;
        }
      }

      // Set up event listeners if not already done
      this.setupAddCategoryModalEventListeners();
      modal.style.display = 'flex';
    }
  }

  editCardAccount(id) {
    console.log('Edit card account:', id);
    // TODO: Implement edit functionality
  }

  deleteCardAccount(id) {
    if (confirm('Are you sure you want to delete this card account?')) {
      console.log('Delete card account:', id);
      // TODO: Implement delete functionality
    }
  }

  editAccount(id) {
    console.log('Edit account:', id);
    // TODO: Implement edit functionality
  }

  deleteAccount(id) {
    if (confirm('Are you sure you want to delete this account?')) {
      console.log('Delete account:', id);
      // TODO: Implement delete functionality
    }
  }

  setupAddAccountModalEventListeners() {
    if (this.addAccountListenersSetup) return;

    const modal = document.getElementById('add-account-modal');
    const closeBtn = document.getElementById('add-account-modal-close');
    const cancelBtn = document.getElementById('add-account-cancel');
    const form = document.getElementById('add-account-form');

    // Close modal events
    closeBtn?.addEventListener('click', () => this.closeAddAccountModal());
    cancelBtn?.addEventListener('click', () => this.closeAddAccountModal());

    // Close on outside click
    modal?.addEventListener('click', (e) => {
      if (e.target === modal) this.closeAddAccountModal();
    });

    // Form submission
    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.submitAddAccountForm();
    });

    this.addAccountListenersSetup = true;
  }

  setupAddCardModalEventListeners() {
    if (this.addCardListenersSetup) return;

    const modal = document.getElementById('add-card-modal');
    const closeBtn = document.getElementById('add-card-modal-close');
    const cancelBtn = document.getElementById('add-card-cancel');
    const form = document.getElementById('add-card-form');

    // Close modal events
    closeBtn?.addEventListener('click', () => this.closeAddCardModal());
    cancelBtn?.addEventListener('click', () => this.closeAddCardModal());

    // Close on outside click
    modal?.addEventListener('click', (e) => {
      if (e.target === modal) this.closeAddCardModal();
    });

    // Form submission
    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.submitAddCardForm();
    });

    this.addCardListenersSetup = true;
  }

  setupAddCategoryModalEventListeners() {
    if (this.addCategoryListenersSetup) return;

    const modal = document.getElementById('add-category-modal');
    const closeBtn = document.getElementById('add-category-modal-close');
    const cancelBtn = document.getElementById('add-category-cancel');
    const form = document.getElementById('add-category-form');

    // Close modal events
    closeBtn?.addEventListener('click', () => this.closeAddCategoryModal());
    cancelBtn?.addEventListener('click', () => this.closeAddCategoryModal());

    // Close on outside click
    modal?.addEventListener('click', (e) => {
      if (e.target === modal) this.closeAddCategoryModal();
    });

    // Form submission
    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.submitAddCategoryForm();
    });

    this.addCategoryListenersSetup = true;
  }

  closeAddAccountModal() {
    const modal = document.getElementById('add-account-modal');
    const form = document.getElementById('add-account-form');
    if (modal) modal.style.display = 'none';
    if (form) form.reset();
  }

  closeAddCardModal() {
    const modal = document.getElementById('add-card-modal');
    const form = document.getElementById('add-card-form');
    if (modal) modal.style.display = 'none';
    if (form) form.reset();
  }

  closeAddCategoryModal() {
    const modal = document.getElementById('add-category-modal');
    const form = document.getElementById('add-category-form');
    if (modal) modal.style.display = 'none';
    if (form) form.reset();
  }

  async submitAddAccountForm() {
    const form = document.getElementById('add-account-form');
    if (!form) return;

    const formData = new FormData(form);
    const accountData = {
      name: formData.get('name'),
      type: formData.get('type'),
      entity: formData.get('entity'),
      balance: parseFloat(formData.get('balance')) || 0
    };

    // Validate required fields
    if (!accountData.name || !accountData.type || !accountData.entity) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      const response = await fetch('/api/accounts/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(accountData)
      });

      if (response.ok) {
        console.log('Account created successfully');
        this.closeAddAccountModal();
        await this.loadAccounts(); // Refresh accounts display
      } else {
        throw new Error('Failed to create account');
      }
    } catch (error) {
      console.error('Error creating account:', error);
      alert('Failed to create account. Please try again.');
    }
  }

  async submitAddCardForm() {
    const form = document.getElementById('add-card-form');
    if (!form) return;

    const formData = new FormData(form);
    const cardData = {
      name: formData.get('name'),
      bank: formData.get('bank'),
      last_four: formData.get('last_four') || null
    };

    // Validate required fields
    if (!cardData.name || !cardData.bank) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      const response = await fetch('/api/card-accounts/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(cardData)
      });

      if (response.ok) {
        console.log('Card account created successfully');
        this.closeAddCardModal();
        await this.loadCardAccounts(); // Refresh card accounts display
      } else {
        throw new Error('Failed to create card account');
      }
    } catch (error) {
      console.error('Error creating card account:', error);
      alert('Failed to create card account. Please try again.');
    }
  }

  async submitAddCategoryForm() {
    const form = document.getElementById('add-category-form');
    if (!form) return;

    const formData = new FormData(form);
    const categoryData = {
      name: formData.get('name'),
      type: formData.get('type'),
      icon: formData.get('icon') || 'fas fa-tag',
      color: formData.get('color') || '#98cc2c'
    };

    // Validate required fields
    if (!categoryData.name || !categoryData.type) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      const response = await fetch('/api/categories/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(categoryData)
      });

      if (response.ok) {
        console.log('Category created successfully');
        this.closeAddCategoryModal();
        await this.loadCategories(); // Refresh categories display
      } else {
        throw new Error('Failed to create category');
      }
    } catch (error) {
      console.error('Error creating category:', error);
      alert('Failed to create category. Please try again.');
    }
  }

  loadCardBankOptions() {
    const bankSelect = document.getElementById('card-bank');
    if (!bankSelect) return;

    // Fetch bank options from the API
    fetch('/api/card-accounts/field-choices/')
      .then(response => response.json())
      .then(data => {
        bankSelect.innerHTML = '<option value="">Select bank</option>';
        if (data.bank) {
          data.bank.forEach(bank => {
            const option = document.createElement('option');
            option.value = bank.value;
            option.textContent = bank.label;
            bankSelect.appendChild(option);
          });
        }
      })
      .catch(error => {
        console.error('Error loading bank options:', error);
      });
  }

  async loadAccountTypeOptions() {
    const typeSelect = document.getElementById('account-type');
    if (!typeSelect) return;

    try {
      // Fetch account type options from the API
      const response = await fetch('/api/accounts/field-choices/');
      const data = await response.json();

      typeSelect.innerHTML = '<option value="">Select account type</option>';
      if (data.type) {
        data.type.forEach(type => {
          const option = document.createElement('option');
          option.value = type.value;
          option.textContent = type.label;
          typeSelect.appendChild(option);
        });
      }
    } catch (error) {
      console.error('Error loading account type options:', error);
    }
  }

}

document.addEventListener("DOMContentLoaded", () => {
  // Initialize modern tiles
  new AccountTilesManager();

  // Keep existing tables as fallback (hidden by default)
  let cardsTable = new RichTable(
    "#settings-card-table",
    "/api/card-accounts/",
    ["Name", "Bank"]
  );
  let accountsTable = new RichTable(
    "#settings-accounts-table",
    "/api/accounts/",
    ["Name", "Type", "Entity"]
  );

  let categoryTable = new RichTable(
    "#settings-categories-table",
    "/api/categories/",
    ["Name", "Type"]
  );

  // Enhanced Budget Management - Initialize budget tiles instead of table

  // Initialize enhanced budget features
  initEnhancedBudgetSettings();
});

// Enhanced Budget Settings Functions
function initEnhancedBudgetSettings() {
  initBudgetYearDropdown();
  initBudgetOverview();
  initBudgetTiles();
  initBudgetControls();

  // Set current month as default
  const currentMonth = new Date().getMonth() + 1;
  const monthSelect = document.getElementById('settings-budget-month');
  if (monthSelect) {
    monthSelect.value = currentMonth.toString();
  }
}

function initBudgetYearDropdown() {
  const yearSelect = document.getElementById('settings-budget-year');
  if (!yearSelect) return;

  // Fetch available years from backend
  fetch('/dashboard/api/expense-years/')
    .then(response => response.json())
    .then(data => {
      if (data.years && data.years.length > 0) {
        yearSelect.innerHTML = data.years
          .map(year => `<option value="${year}">${year}</option>`)
          .join('');
        yearSelect.value = data.years[0]; // Default to latest year

        // Load budget overview, tiles, and table for default selection
        loadBudgetOverview();
        loadBudgetTiles();
        loadPastBudgetsTable();
      }
    })
    .catch(error => console.error('Error loading years:', error));
}

function initBudgetControls() {
  const yearSelect = document.getElementById('settings-budget-year');
  const monthSelect = document.getElementById('settings-budget-month');
  const addBudgetBtn = document.getElementById('add-budget-btn');

  // Add event listeners for year/month changes
  if (yearSelect) {
    yearSelect.addEventListener('change', function() {
      loadBudgetOverview();
      loadBudgetTiles();
      loadPastBudgetsTable();
    });
  }

  if (monthSelect) {
    monthSelect.addEventListener('change', function() {
      loadBudgetOverview();
      loadBudgetTiles();
      loadPastBudgetsTable();
    });
  }

  // Add budget button functionality
  if (addBudgetBtn) {
    addBudgetBtn.addEventListener('click', showAddBudgetForm);
  }
}

function initBudgetOverview() {
  loadBudgetOverview();
}

function loadBudgetOverview() {
  const yearSelect = document.getElementById('settings-budget-year');
  const monthSelect = document.getElementById('settings-budget-month');
  const activeBudgetsContainer = document.getElementById('active-budget-tiles');

  if (!yearSelect || !monthSelect || !activeBudgetsContainer) return;

  const year = yearSelect.value;
  const monthNum = monthSelect.value;

  if (!year || !monthNum) return;

  // Convert numeric month to month abbreviation
  const monthAbbr = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][parseInt(monthNum)];

  // Fetch both budget rankings and budget list to get IDs
  const rankingsUrl = `/get-budget-rankings/?year=${year}&month=${monthAbbr}`;
  const budgetsUrl = `/api/budget/`;

  Promise.all([
    fetch(rankingsUrl).then(response => response.json()),
    fetch(budgetsUrl).then(response => response.json())
  ])
    .then(([rankingsData, budgetsData]) => {
      const rankings = rankingsData.category_rankings || [];
      const budgets = budgetsData.rows || [];

      // Merge the data to include IDs
      const mergedBudgets = rankings.map(ranking => {
        const matchingBudget = budgets.find(b =>
          (b.category_name || b.category) === ranking.name
        );
        return {
          ...ranking,
          id: matchingBudget ? matchingBudget.id : null
        };
      });

      renderBudgetOverview(mergedBudgets, activeBudgetsContainer);
    })
    .catch(error => {
      console.error('Error loading budget overview:', error);
      activeBudgetsContainer.innerHTML = `
        <div class="no-data-message">
          <i class="fa-solid fa-exclamation-triangle" style="font-size: 2rem; color: var(--red-color); opacity: 0.7; margin-bottom: 10px;"></i>
          <p style="color: var(--title-color); text-align: center; margin: 0; font-size: 14px;">
            Unable to load budget overview
          </p>
        </div>
      `;
    });
}

function renderBudgetOverview(budgets, container) {
  if (!budgets || budgets.length === 0) {
    container.innerHTML = `
      <div class="budget-overview-card" style="grid-column: 1 / -1; text-align: center; padding: 40px;">
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
          <i class="fa-solid fa-wallet" style="font-size: 2rem; color: var(--title-color); opacity: 0.5; margin-bottom: 15px;"></i>
          <p style="color: var(--title-color); margin: 0; font-size: 16px; font-weight: 500;">
            No budgets set for this period
          </p>
          <p style="color: var(--title-color); margin: 8px 0 0 0; font-size: 14px; opacity: 0.7;">
            Click "Add Budget" to create your first budget
          </p>
        </div>
      </div>
    `;
    return;
  }

  const categoryIcons = getCategoryIcons();

  container.innerHTML = budgets.map(budget => {
    // Handle both data structures - budget rankings vs budget list
    const budgetAmount = budget.budget || budget.budget_amount || 0;
    const spentAmount = budget.spent || budget.spent_amount || 0;
    const categoryName = budget.name || budget.category_name || 'Unknown Category';

    const percentage = budgetAmount > 0 ? (spentAmount / budgetAmount) * 100 : 0;
    const remaining = budgetAmount - spentAmount;
    const icon = categoryIcons[categoryName] || 'fa-solid fa-folder';

    let statusClass = 'good';
    if (percentage >= 100) statusClass = 'danger';
    else if (percentage >= 80) statusClass = 'warning';

    return `
      <div class="budget-overview-card" onclick="editBudget(${budget.id || 'null'})" style="cursor: pointer;">
        <div class="budget-overview-header">
          <div class="budget-overview-icon">
            <i class="${icon}"></i>
          </div>
          <div class="budget-overview-info">
            <h3>${categoryName}</h3>
            <p>${budget.start_date || ''} - ${budget.end_date || ''}</p>
          </div>
        </div>

        <div class="budget-overview-amounts">
          <div class="budget-amount">
            <span class="label">Budget</span>
            <span class="value">$${budgetAmount.toLocaleString()}</span>
          </div>
          <div class="spent-amount">
            <span class="label">Spent</span>
            <span class="value">$${spentAmount.toLocaleString()}</span>
          </div>
        </div>

        <div class="budget-progress-bar">
          <div class="budget-progress-fill ${percentage >= 100 ? 'over-budget' : ''}"
               style="width: ${Math.min(percentage, 100)}%"></div>
        </div>

        <div class="budget-status">
          <span class="budget-percentage ${statusClass}">${percentage.toFixed(1)}%</span>
          <span class="budget-remaining">
            ${remaining >= 0 ? `$${remaining.toLocaleString()} left` : `$${Math.abs(remaining).toLocaleString()} over`}
          </span>
        </div>
      </div>
    `;
  }).join('');
}

function initBudgetTiles() {
  // Load initial budget tiles and table
  loadBudgetTiles();
  loadPastBudgetsTable();
}

function loadBudgetTiles() {
  // This function is now handled by loadBudgetOverview()
  // which renders the budget data directly in the active-budget-tiles container
  loadBudgetOverview();
}

function filterActiveBudgets(budgets) {
  const currentDate = new Date();
  const today = currentDate.toISOString().split('T')[0]; // YYYY-MM-DD format

  return budgets.filter(budget => {
    const startDate = budget.start_date;
    const endDate = budget.end_date;

    // Budget is active if:
    // 1. Start date is <= today
    // 2. End date is null (ongoing) OR end date is >= today
    const isAfterStart = !startDate || startDate <= today;
    const isBeforeEnd = !endDate || endDate >= today;

    return isAfterStart && isBeforeEnd;
  });
}

function filterPastBudgets(budgets) {
  const currentDate = new Date();
  const today = currentDate.toISOString().split('T')[0]; // YYYY-MM-DD format

  return budgets.filter(budget => {
    const endDate = budget.end_date;
    // Budget is past if it has an end date and end date is < today
    return endDate && endDate < today;
  });
}

function renderActiveBudgetTiles(budgets, container) {
  if (!budgets || budgets.length === 0) {
    container.innerHTML = `
      <div class="budget-tile" style="width: 100%; text-align: center; padding: 40px;">
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
          <i class="fa-solid fa-plus-circle" style="font-size: 2rem; color: var(--green-color); opacity: 0.7; margin-bottom: 15px;"></i>
          <p style="color: var(--title-color); margin: 0; font-size: 16px; font-weight: 500;">
            No active budgets
          </p>
          <p style="color: var(--title-color); margin: 8px 0 0 0; font-size: 14px; opacity: 0.7;">
            Click "Add Budget" to create your first budget
          </p>
        </div>
      </div>
    `;
    return;
  }

  const categoryIcons = getCategoryIcons();

  container.innerHTML = budgets.map(budget => {
    // Handle both data structures - budget API vs budget rankings
    const budgetAmount = budget.budget_amount || budget.budget || budget.amount || 0;
    const spentAmount = budget.spent_amount || budget.spent || 0;
    const categoryName = budget.category || budget.category_name || budget.name || 'Unknown Category';

    const percentage = budgetAmount > 0 ? (spentAmount / budgetAmount) * 100 : 0;
    const remaining = budgetAmount - spentAmount;
    const icon = categoryIcons[categoryName] || 'fa-solid fa-folder';

    let statusClass = 'good';
    if (percentage >= 100) statusClass = 'danger';
    else if (percentage >= 80) statusClass = 'warning';

    return `
      <div class="budget-tile" data-budget-id="${budget.id || ''}">
        <div class="budget-tile-header">
          <div class="budget-tile-icon">
            <i class="${icon}"></i>
          </div>
          <div class="budget-tile-info">
            <h3>${categoryName}</h3>
            <p>${budget.start_date || ''} - ${budget.end_date || 'Ongoing'}</p>
          </div>
        </div>

        <div class="budget-tile-body">
          <div class="budget-tile-amounts">
            <div class="budget-tile-amount">
              <span class="label">Budget</span>
              <span class="value">$${budgetAmount.toLocaleString()}</span>
            </div>
            <div class="budget-tile-spent">
              <span class="label">Spent</span>
              <span class="value">$${spentAmount.toLocaleString()}</span>
            </div>
          </div>

          <div class="budget-tile-progress">
            <div class="budget-tile-progress-fill ${percentage >= 100 ? 'over-budget' : ''}"
                 style="width: ${Math.min(percentage, 100)}%"></div>
          </div>
        </div>

        <div class="budget-tile-footer">
          <span class="budget-tile-percentage ${statusClass}">${percentage.toFixed(1)}%</span>
          <span class="budget-tile-remaining">
            ${remaining >= 0 ? `$${remaining.toLocaleString()} left` : `$${Math.abs(remaining).toLocaleString()} over`}
          </span>
        </div>
      </div>
    `;
  }).join('');
}

function loadPastBudgetsTable() {
  const tableBody = document.querySelector('#past-budgets-table tbody');
  if (!tableBody) return;

  // Load all budgets and filter for past ones
  const url = `/api/budget/`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      const allBudgets = data.rows || [];
      const pastBudgets = filterPastBudgets(allBudgets);
      renderPastBudgetsTable(pastBudgets, tableBody);
    })
    .catch(error => {
      console.error('Error loading past budgets:', error);
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" style="text-align: center; padding: 20px; color: var(--red-color);">
            <i class="fa-solid fa-exclamation-triangle" style="margin-right: 8px;"></i>
            Unable to load past budgets
          </td>
        </tr>
      `;
    });
}

function renderPastBudgetsTable(budgets, tableBody) {
  if (!budgets || budgets.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; padding: 20px; color: var(--title-color); opacity: 0.7;">
          <i class="fa-solid fa-history" style="margin-right: 8px;"></i>
          No past budgets found
        </td>
      </tr>
    `;
    return;
  }

  const categoryIcons = getCategoryIcons();

  tableBody.innerHTML = budgets.map(budget => {
    const budgetAmount = budget.budget_amount || budget.budget || budget.amount || 0;
    const categoryName = budget.category || budget.category_name || budget.name || 'Unknown Category';
    const icon = categoryIcons[categoryName] || 'fa-solid fa-folder';

    return `
      <tr onclick="editBudget(${budget.id})" style="cursor: pointer;" onmouseover="this.style.backgroundColor='var(--secondary-color)'" onmouseout="this.style.backgroundColor=''">
        <td>
          <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 30px; height: 30px; border-radius: 6px; display: flex; align-items: center; justify-content: center; background: var(--green-color); color: white; font-size: 14px;">
              <i class="${icon}"></i>
            </div>
            <span>${categoryName}</span>
          </div>
        </td>
        <td>$${budgetAmount.toLocaleString()}</td>
        <td>${budget.start_date || 'N/A'}</td>
        <td>${budget.end_date || 'N/A'}</td>
        <td>
          <span style="background: rgba(239, 68, 68, 0.2); color: var(--red-color); padding: 4px 8px; border-radius: 4px; font-size: 12px;">
            Ended
          </span>
        </td>
      </tr>
    `;
  }).join('');
}

function renderBudgetTiles(budgets, container) {
  if (!budgets || budgets.length === 0) {
    container.innerHTML = `
      <div class="budget-tile" style="grid-column: 1 / -1; text-align: center; padding: 40px;">
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
          <i class="fa-solid fa-plus-circle" style="font-size: 2rem; color: var(--green-color); opacity: 0.7; margin-bottom: 15px;"></i>
          <p style="color: var(--title-color); margin: 0; font-size: 16px; font-weight: 500;">
            No budgets for this period
          </p>
          <p style="color: var(--title-color); margin: 8px 0 0 0; font-size: 14px; opacity: 0.7;">
            Click "Add Budget" to create your first budget
          </p>
        </div>
      </div>
    `;
    return;
  }

  const categoryIcons = getCategoryIcons();

  container.innerHTML = budgets.map(budget => {
    // Handle both data structures - budget API vs budget rankings
    const budgetAmount = budget.budget_amount || budget.budget || budget.amount || 0;
    const spentAmount = budget.spent_amount || budget.spent || 0;
    const categoryName = budget.category || budget.category_name || budget.name || 'Unknown Category';

    const percentage = budgetAmount > 0 ? (spentAmount / budgetAmount) * 100 : 0;
    const remaining = budgetAmount - spentAmount;
    const icon = categoryIcons[categoryName] || 'fa-solid fa-folder';

    let statusClass = 'good';
    if (percentage >= 100) statusClass = 'danger';
    else if (percentage >= 80) statusClass = 'warning';

    return `
      <div class="budget-tile" data-budget-id="${budget.id || ''}">
        <div class="budget-tile-header">
          <div class="budget-tile-icon">
            <i class="${icon}"></i>
          </div>
          <div class="budget-tile-info">
            <h3>${categoryName}</h3>
            <p>${budget.start_date || ''} - ${budget.end_date || ''}</p>
          </div>
        </div>

        <div class="budget-tile-body">
          <div class="budget-tile-amounts">
            <div class="budget-tile-amount">
              <span class="label">Budget</span>
              <span class="value">$${budgetAmount.toLocaleString()}</span>
            </div>
            <div class="budget-tile-spent">
              <span class="label">Spent</span>
              <span class="value">$${spentAmount.toLocaleString()}</span>
            </div>
          </div>

          <div class="budget-tile-progress">
            <div class="budget-tile-progress-fill ${percentage >= 100 ? 'over-budget' : ''}"
                 style="width: ${Math.min(percentage, 100)}%"></div>
          </div>
        </div>

        <div class="budget-tile-footer">
          <span class="budget-tile-percentage ${statusClass}">${percentage.toFixed(1)}%</span>
          <span class="budget-tile-remaining">
            ${remaining >= 0 ? `$${remaining.toLocaleString()} left` : `$${Math.abs(remaining).toLocaleString()} over`}
          </span>
        </div>
      </div>
    `;
  }).join('');
}

let budgetModalListenersSetup = false;

function showAddBudgetForm() {
  const modal = document.getElementById('budget-modal');
  if (modal) {
    // Load categories for the dropdown
    loadBudgetCategories();

    // Set default start date to today
    const today = new Date().toISOString().split('T')[0];
    const startDateInput = document.getElementById('budget-start-date');
    if (startDateInput) {
      startDateInput.value = today;
    }

    // Set up event listeners only once
    if (!budgetModalListenersSetup) {
      setupBudgetModalEventListeners();
      budgetModalListenersSetup = true;
    }

    // Show the modal
    modal.style.display = 'flex';  // Use flex since we have flexbox centering
  }
}

function loadBudgetCategories() {
  const categorySelect = document.getElementById('budget-category');
  if (!categorySelect) return Promise.resolve();

  // Fetch categories from the API
  return fetch('/api/budget/field-choices/')
    .then(response => response.json())
    .then(data => {
      categorySelect.innerHTML = '<option value="">Select a category</option>';
      if (data.category) {
        data.category.forEach(cat => {
          const option = document.createElement('option');
          option.value = cat.value;
          option.textContent = cat.label;
          categorySelect.appendChild(option);
        });
      }
    })
    .catch(error => {
      console.error('Error loading categories:', error);
    });
}

function setupBudgetModalEventListeners() {
  const modal = document.getElementById('budget-modal');
  const closeBtn = document.getElementById('budget-modal-close');
  const cancelBtn = document.getElementById('budget-cancel');
  const form = document.getElementById('budget-form');

  // Close modal events
  if (closeBtn) {
    closeBtn.addEventListener('click', function(e) {
      e.preventDefault();
      closeBudgetModal();
    });
  }
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function(e) {
      e.preventDefault();
      closeBudgetModal();
    });
  }

  // Close on outside click
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeBudgetModal();
      }
    });
  }

  // Form submission
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      submitBudgetForm();
    });
  }
}


function editBudget(budgetId) {
  if (!budgetId || budgetId === 'null' || budgetId === null) {
    console.log('No budget ID provided - this budget may not be editable');
    alert('This budget cannot be edited. Please try creating a new budget instead.');
    return;
  }

  // Fetch budget details
  fetch(`/api/budget/${budgetId}/`)
    .then(response => response.json())
    .then(budget => {
      showEditBudgetForm(budget);
    })
    .catch(error => {
      console.error('Error loading budget for editing:', error);
      alert('Failed to load budget details');
    });
}

function showEditBudgetForm(budget) {
  const modal = document.getElementById('budget-modal');
  if (!modal) return;

  // Remove any existing category displays immediately to prevent duplicates
  const existingCategoryDisplay = modal.querySelector('.budget-category-display');
  if (existingCategoryDisplay) {
    existingCategoryDisplay.remove();
  }

  // Load categories for the dropdown and wait for them to load
  loadBudgetCategories().then(() => {
    // Populate form with existing budget data after categories are loaded
    const categorySelect = document.getElementById('budget-category');
    const categoryFormGroup = categorySelect ? categorySelect.closest('.form-group') : null;
    const amountInput = document.getElementById('budget-amount');
    const startDateInput = document.getElementById('budget-start-date');
    const endDateInput = document.getElementById('budget-end-date');
    const form = document.getElementById('budget-form');

    // Get category name from budget data
    let categoryName = '';
    if (budget.category) {
      // If budget.category is an ID, we need to get the name from the select options
      if (categorySelect) {
        const option = categorySelect.querySelector(`option[value="${budget.category}"]`);
        categoryName = option ? option.textContent : 'Unknown Category';
      }
    }

    // Hide the category dropdown and create a visual category display
    if (categoryFormGroup) {
      categoryFormGroup.style.display = 'none';

      // Remove required attribute to prevent validation errors
      if (categorySelect) {
        categorySelect.removeAttribute('required');
      }

      // Create category display element
      const categoryDisplay = document.createElement('div');
      categoryDisplay.className = 'budget-category-display';
      categoryDisplay.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; padding: 15px; background: var(--secondary-color); border-radius: 8px; margin-bottom: 20px;">
          <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--green-color); display: flex; align-items: center; justify-content: center; font-size: 18px; color: #000;">
            <i class="${getCategoryIcon(categoryName)}"></i>
          </div>
          <div>
            <div style="font-weight: 600; color: var(--title-color); font-size: 16px;">${categoryName}</div>
            <div style="font-size: 12px; color: var(--text-color); opacity: 0.7;">Budget Category</div>
          </div>
        </div>
      `;

      // Insert the category display before the amount input
      const amountFormGroup = amountInput ? amountInput.closest('.form-group') : null;
      if (amountFormGroup) {
        amountFormGroup.parentNode.insertBefore(categoryDisplay, amountFormGroup);
      }
    }

    if (amountInput) amountInput.value = budget.amount;
    if (startDateInput) startDateInput.value = budget.start_date;
    if (endDateInput) endDateInput.value = budget.end_date || '';

    // Update modal title and subtitle
    const modalTitle = modal.querySelector('.account-modal-title h3');
    const modalSubtitle = modal.querySelector('.account-modal-title p');
    if (modalTitle) modalTitle.textContent = 'Edit Budget';
    if (modalSubtitle) modalSubtitle.textContent = `Update budget settings for ${categoryName}`;

    // Update submit button text
    const submitBtn = modal.querySelector('.account-modal-btn.edit');
    if (submitBtn) {
      submitBtn.innerHTML = '<i class="fas fa-save"></i> Update Budget';
    }

    // Store budget ID and category on form for submission
    if (form) {
      form.dataset.budgetId = budget.id;
      form.dataset.budgetCategory = budget.category;
    }

    // Set up event listeners only once
    if (!budgetModalListenersSetup) {
      setupBudgetModalEventListeners();
      budgetModalListenersSetup = true;
    }

    // Show the modal
    modal.style.display = 'flex';
  });
}

function submitBudgetForm() {
  const form = document.getElementById('budget-form');
  if (!form) return;

  const formData = new FormData(form);
  const budgetId = form.dataset.budgetId;
  const isEditing = budgetId && budgetId !== 'undefined';

  const budgetData = {
    category: isEditing ? form.dataset.budgetCategory : formData.get('category'),
    amount: parseFloat(formData.get('amount')),
    start_date: formData.get('start_date'),
    end_date: formData.get('end_date') || null
  };

  // Validate required fields
  if (!budgetData.category || !budgetData.amount || !budgetData.start_date) {
    alert('Please fill in all required fields');
    return;
  }

  const url = isEditing ? `/api/budget/${budgetId}/` : '/api/budget/';
  const method = isEditing ? 'PATCH' : 'POST';

  // Submit to API
  fetch(url, {
    method: method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(budgetData)
  })
  .then(response => {
    if (response.ok) {
      return response.json();
    }
    throw new Error(`Failed to ${isEditing ? 'update' : 'create'} budget`);
  })
  .then(data => {
    console.log(`Budget ${isEditing ? 'updated' : 'created'} successfully:`, data);
    closeBudgetModal();
    // Refresh budget displays
    loadBudgetOverview();
    loadBudgetTiles();
    loadPastBudgetsTable();
  })
  .catch(error => {
    console.error(`Error ${isEditing ? 'updating' : 'creating'} budget:`, error);
    alert(`Failed to ${isEditing ? 'update' : 'create'} budget. Please try again.`);
  });
}

function closeBudgetModal() {
  const modal = document.getElementById('budget-modal');
  if (modal) {
    modal.style.display = 'none';
    // Reset form
    const form = document.getElementById('budget-form');
    if (form) {
      form.reset();
      delete form.dataset.budgetId;
      delete form.dataset.budgetCategory;
    }

    // Remove category display if it exists
    const categoryDisplay = modal.querySelector('.budget-category-display');
    if (categoryDisplay) {
      categoryDisplay.remove();
    }

    // Show category dropdown again and restore required attribute
    const categoryFormGroup = modal.querySelector('#budget-category')?.closest('.form-group');
    const categorySelect = document.getElementById('budget-category');
    if (categoryFormGroup) {
      categoryFormGroup.style.display = '';
    }
    if (categorySelect) {
      categorySelect.setAttribute('required', '');
    }

    // Reset modal title and subtitle
    const modalTitle = modal.querySelector('.account-modal-title h3');
    const modalSubtitle = modal.querySelector('.account-modal-title p');
    if (modalTitle) modalTitle.textContent = 'Add Budget';
    if (modalSubtitle) modalSubtitle.textContent = 'Create a new budget for a category';

    const submitBtn = modal.querySelector('.account-modal-btn.edit');
    if (submitBtn) {
      submitBtn.innerHTML = '<i class="fas fa-plus"></i> Create Budget';
    }
  }
}

function getCategoryIcon(categoryName) {
  const icons = getCategoryIcons();
  const normalized = categoryName.toLowerCase().trim();
  return icons[normalized] || 'fa-folder';
}

function getCategoryIcons() {
  // Category icons mapping - this should match your category system
  return {
    'Food & Dining': 'fa-solid fa-utensils',
    'Groceries': 'fa-solid fa-shopping-cart',
    'Transportation': 'fa-solid fa-car',
    'Gas & Fuel': 'fa-solid fa-gas-pump',
    'Entertainment': 'fa-solid fa-film',
    'Shopping': 'fa-solid fa-shopping-bag',
    'Bills & Utilities': 'fa-solid fa-file-invoice-dollar',
    'Health & Medical': 'fa-solid fa-heart-pulse',
    'Travel': 'fa-solid fa-plane',
    'Home & Garden': 'fa-solid fa-house',
    'Education': 'fa-solid fa-graduation-cap',
    'Personal Care': 'fa-solid fa-spa',
    'Gifts & Donations': 'fa-solid fa-gift',
    'Business Services': 'fa-solid fa-briefcase',
    'Fees & Charges': 'fa-solid fa-receipt',
    'Taxes': 'fa-solid fa-landmark',
    'Other': 'fa-solid fa-question'
  };
}
