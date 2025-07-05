// BI Dashboard JavaScript - Common Personal Finance Graphs

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    // Initialize all charts and components
    initCashFlowChart();
    initExpensePieChart();
    initIncomeExpenseChart();
    initSavingsChart();
    initSpendingHeatmap();
    initBudgetProgress();
    initTopMerchants();
}

// 1. Cash Flow Trend Chart (Line Chart)
function initCashFlowChart() {
    const ctx = document.getElementById('cashFlowChart');
    if (!ctx) return;

    // Sample data - replace with actual data from backend
    const cashFlowData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Net Cash Flow',
            data: [1200, 1800, -500, 2200, 1600, 2400],
            borderColor: '#98CC2C',
            backgroundColor: 'rgba(152, 204, 44, 0.1)',
            fill: true,
            tension: 0.4
        }, {
            label: 'Income',
            data: [5000, 5200, 4800, 5500, 5100, 5400],
            borderColor: '#4CAF50',
            backgroundColor: 'transparent',
            borderDash: [5, 5]
        }, {
            label: 'Expenses',
            data: [3800, 3400, 5300, 3300, 3500, 3000],
            borderColor: '#FF6B6B',
            backgroundColor: 'transparent',
            borderDash: [5, 5]
        }]
    };

    new Chart(ctx, {
        type: 'line',
        data: cashFlowData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#ffffff'
                    }
                },
                zoom: {
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'x',
                    },
                    pan: {
                        enabled: true,
                        mode: 'x',
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#ffffff',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// 2. Expense Categories Pie Chart
function initExpensePieChart() {
    const ctx = document.getElementById('expensePieChart');
    if (!ctx) return;

    const expenseData = {
        labels: ['Housing', 'Food', 'Transportation', 'Entertainment', 'Healthcare', 'Other'],
        datasets: [{
            data: [1200, 600, 400, 300, 200, 300],
            backgroundColor: [
                '#98CC2C',
                '#4CAF50',
                '#81C784',
                '#A5D6A7',
                '#C8E6C9',
                '#E8F5E8'
            ],
            borderWidth: 2,
            borderColor: '#fff'
        }]
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: expenseData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        color: '#ffffff'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// 3. Income vs Expenses Bar Chart
function initIncomeExpenseChart() {
    const ctx = document.getElementById('incomeExpenseChart');
    if (!ctx) return;

    const incomeExpenseData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Income',
            data: [5000, 5200, 4800, 5500, 5100, 5400],
            backgroundColor: '#98CC2C',
            borderRadius: 4
        }, {
            label: 'Expenses',
            data: [3800, 3400, 5300, 3300, 3500, 3000],
            backgroundColor: '#FF6B6B',
            borderRadius: 4
        }]
    };

    new Chart(ctx, {
        type: 'bar',
        data: incomeExpenseData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#ffffff',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// 4. Savings Accumulation Chart
function initSavingsChart() {
    const ctx = document.getElementById('savingsChart');
    if (!ctx) return;

    const savingsData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Total Savings',
            data: [10000, 11200, 10700, 12900, 14500, 16900],
            borderColor: '#98CC2C',
            backgroundColor: 'rgba(152, 204, 44, 0.1)',
            fill: true,
            tension: 0.4
        }, {
            label: 'Monthly Savings',
            data: [1200, 1200, -500, 2200, 1600, 2400],
            type: 'bar',
            backgroundColor: '#4CAF50',
            borderRadius: 4
        }]
    };

    new Chart(ctx, {
        type: 'line',
        data: savingsData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#ffffff'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#ffffff',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// 5. Spending Patterns Heatmap
function initSpendingHeatmap() {
    const container = document.getElementById('spendingHeatmap');
    if (!container) return;

    // Simple heatmap representation
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const categories = ['Food', 'Transport', 'Shopping', 'Entertainment'];

    let heatmapHTML = '<div class="heatmap-grid">';
    heatmapHTML += '<div class="heatmap-header"><div></div>';
    days.forEach(day => {
        heatmapHTML += `<div class="day-label">${day}</div>`;
    });
    heatmapHTML += '</div>';

    categories.forEach(category => {
        heatmapHTML += `<div class="heatmap-row">`;
        heatmapHTML += `<div class="category-label">${category}</div>`;
        days.forEach(() => {
            const intensity = Math.random();
            const opacity = 0.2 + (intensity * 0.8);
            heatmapHTML += `<div class="heatmap-cell" style="background-color: rgba(152, 204, 44, ${opacity})" title="$${Math.round(intensity * 200)}"></div>`;
        });
        heatmapHTML += '</div>';
    });
    heatmapHTML += '</div>';

    container.innerHTML = heatmapHTML;

    // Add CSS for heatmap
    const style = document.createElement('style');
    style.textContent = `
        .heatmap-grid {
            display: grid;
            grid-template-columns: 100px repeat(7, 1fr);
            gap: 2px;
        }
        .heatmap-header {
            display: contents;
        }
        .day-label, .category-label {
            font-size: 0.8rem;
            padding: 8px;
            text-align: center;
            font-weight: 500;
        }
        .heatmap-row {
            display: contents;
        }
        .heatmap-cell {
            height: 30px;
            border-radius: 4px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .heatmap-cell:hover {
            transform: scale(1.1);
        }
    `;
    document.head.appendChild(style);
}

// 6. Budget Progress Bars
function initBudgetProgress() {
    const container = document.getElementById('budget-progress');
    if (!container) return;

    const budgets = [
        { category: 'Housing', spent: 1200, budget: 1500, color: '#98CC2C' },
        { category: 'Food', spent: 600, budget: 700, color: '#4CAF50' },
        { category: 'Transportation', spent: 350, budget: 400, color: '#81C784' },
        { category: 'Entertainment', spent: 280, budget: 300, color: '#FF6B6B' }
    ];

    let progressHTML = '';
    budgets.forEach(item => {
        const percentage = (item.spent / item.budget) * 100;
        const status = percentage > 90 ? 'warning' : percentage > 100 ? 'over' : 'good';

        progressHTML += `
            <div class="budget-item">
                <div class="budget-header">
                    <span class="budget-category">${item.category}</span>
                    <span class="budget-amount">$${item.spent.toLocaleString()} / $${item.budget.toLocaleString()}</span>
                </div>
                <div class="budget-bar">
                    <div class="budget-fill ${status}" style="width: ${Math.min(percentage, 100)}%; background-color: ${item.color}"></div>
                </div>
                <div class="budget-percentage">${percentage.toFixed(1)}%</div>
            </div>
        `;
    });

    container.innerHTML = progressHTML;

    // Add CSS for budget progress
    const style = document.createElement('style');
    style.textContent = `
        .budget-item {
            margin-bottom: 20px;
        }
        .budget-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        .budget-category {
            font-weight: 500;
        }
        .budget-amount {
            color: var(--text-color);
        }
        .budget-bar {
            height: 12px;
            background: var(--main-color);
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 5px;
        }
        .budget-fill {
            height: 100%;
            transition: width 0.3s ease;
            border-radius: 6px;
        }
        .budget-fill.warning {
            opacity: 0.8;
        }
        .budget-fill.over {
            background-color: #FF6B6B !important;
        }
        .budget-percentage {
            text-align: right;
            font-size: 0.8rem;
            color: var(--text-color);
        }
    `;
    document.head.appendChild(style);
}

// 7. Top Merchants List
function initTopMerchants() {
    const container = document.getElementById('top-merchants');
    if (!container) return;

    const merchants = [
        { name: 'Amazon', amount: 245, transactions: 8, category: 'Shopping' },
        { name: 'Starbucks', amount: 156, transactions: 12, category: 'Food' },
        { name: 'Shell Gas Station', amount: 180, transactions: 6, category: 'Transportation' },
        { name: 'Netflix', amount: 15, transactions: 1, category: 'Entertainment' },
        { name: 'Whole Foods', amount: 320, transactions: 4, category: 'Food' }
    ];

    let merchantHTML = '';
    merchants.forEach((merchant, index) => {
        merchantHTML += `
            <div class="merchant-item">
                <div class="merchant-rank">#${index + 1}</div>
                <div class="merchant-info">
                    <div class="merchant-name">${merchant.name}</div>
                    <div class="merchant-category">${merchant.category}</div>
                </div>
                <div class="merchant-stats">
                    <div class="merchant-amount">$${merchant.amount}</div>
                    <div class="merchant-count">${merchant.transactions} transactions</div>
                </div>
            </div>
        `;
    });

    container.innerHTML = merchantHTML;

    // Add CSS for merchant list
    const style = document.createElement('style');
    style.textContent = `
        .merchant-item {
            display: flex;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid var(--main-color);
        }
        .merchant-item:last-child {
            border-bottom: none;
        }
        .merchant-rank {
            width: 30px;
            height: 30px;
            background: var(--green-color);
            color: #000;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.8rem;
            margin-right: 15px;
        }
        .merchant-info {
            flex: 1;
        }
        .merchant-name {
            font-weight: 500;
            margin-bottom: 3px;
        }
        .merchant-category {
            font-size: 0.8rem;
            color: var(--text-color);
        }
        .merchant-stats {
            text-align: right;
        }
        .merchant-amount {
            font-weight: 600;
            color: var(--title-color);
        }
        .merchant-count {
            font-size: 0.8rem;
            color: var(--text-color);
        }
    `;
    document.head.appendChild(style);
}
