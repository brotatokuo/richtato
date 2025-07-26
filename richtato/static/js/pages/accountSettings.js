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
    console.log('Show add card account modal');
  }

  showAddAccountModal(accountType = null) {
    console.log('Show add account modal for type:', accountType);
  }

  showAddCategoryModal(type = 'category') {
    console.log('Show add category modal for type:', type);
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
  const overviewContainer = document.getElementById('budget-overview');

  if (!yearSelect || !monthSelect || !overviewContainer) return;

  const year = yearSelect.value;
  const month = monthSelect.value;

  if (!year || !month) return;

  const url = `/get-budget-rankings/?year=${year}&month=${month}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      renderBudgetOverview(data.category_rankings || [], overviewContainer);
    })
    .catch(error => {
      console.error('Error loading budget overview:', error);
      overviewContainer.innerHTML = `
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
      <div class="budget-overview-card">
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
  const tilesContainer = document.getElementById('active-budget-tiles');
  if (!tilesContainer) return;

  // Load all budgets and filter for active ones
  const url = `/api/budget/`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      const allBudgets = data.rows || [];
      const activeBudgets = filterActiveBudgets(allBudgets);
      renderActiveBudgetTiles(activeBudgets, tilesContainer);
    })
    .catch(error => {
      console.error('Error loading budget tiles:', error);
      tilesContainer.innerHTML = `
        <div class="budget-tile" style="width: 100%; text-align: center; padding: 40px;">
          <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <i class="fa-solid fa-exclamation-triangle" style="font-size: 2rem; color: var(--red-color); opacity: 0.7; margin-bottom: 15px;"></i>
            <p style="color: var(--title-color); margin: 0; font-size: 16px; font-weight: 500;">
              Unable to load active budgets
            </p>
            <p style="color: var(--title-color); margin: 8px 0 0 0; font-size: 14px; opacity: 0.7;">
              Please try refreshing the page
            </p>
          </div>
        </div>
      `;
    });
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
      <tr>
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

function showAddBudgetForm() {
  // This could open a modal or redirect to budget creation
  // For now, we'll scroll to the active budget tiles container
  const tilesContainer = document.getElementById('active-budget-tiles');
  if (tilesContainer) {
    tilesContainer.scrollIntoView({ behavior: 'smooth' });
    // You could also open an add budget modal here
  }
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
