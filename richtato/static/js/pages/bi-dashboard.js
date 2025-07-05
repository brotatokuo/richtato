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

    // Fetch real data from backend
    fetch('/dashboard/api/cash-flow/')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching cash flow data:', data.error);
                return;
            }

            new Chart(ctx, {
                type: 'line',
                data: data,
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
        })
        .catch(error => {
            console.error('Error fetching cash flow data:', error);
        });
}

// 2. Expense Categories Pie Chart
function initExpensePieChart() {
    const ctx = document.getElementById('expensePieChart');
    if (!ctx) return;

    // Fetch real data from backend
    fetch('/dashboard/api/expense-categories/')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching expense categories data:', data.error);
                return;
            }

            new Chart(ctx, {
                type: 'doughnut',
                data: data,
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
        })
        .catch(error => {
            console.error('Error fetching expense categories data:', error);
        });
}

// 3. Income vs Expenses Bar Chart
function initIncomeExpenseChart() {
    const ctx = document.getElementById('incomeExpenseChart');
    if (!ctx) return;

    // Fetch real data from backend
    fetch('/dashboard/api/income-expenses/')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching income vs expenses data:', data.error);
                return;
            }

            new Chart(ctx, {
                type: 'bar',
                data: data,
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
        })
        .catch(error => {
            console.error('Error fetching income vs expenses data:', error);
        });
}

// 4. Savings Accumulation Chart
function initSavingsChart() {
    const ctx = document.getElementById('savingsChart');
    if (!ctx) return;

    // Fetch real data from backend
    fetch('/dashboard/api/savings/')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching savings data:', data.error);
                return;
            }

            new Chart(ctx, {
                type: 'line',
                data: data,
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
        })
        .catch(error => {
            console.error('Error fetching savings data:', error);
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

    // Fetch real budget data from backend
    fetch('/dashboard/api/budget-progress/')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching budget progress data:', data.error);
                return;
            }

            const budgets = data.budgets || [];
            const colors = ['#98CC2C', '#4CAF50', '#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E8'];

            let progressHTML = '';
            budgets.forEach((item, index) => {
                const percentage = item.percentage;
                const status = percentage > 90 ? 'warning' : percentage > 100 ? 'over' : 'good';
                const color = colors[index % colors.length];

                progressHTML += `
                    <div class="budget-item">
                        <div class="budget-header">
                            <span class="budget-category">${item.category}</span>
                            <span class="budget-amount">$${item.spent.toLocaleString()} / $${item.budget.toLocaleString()}</span>
                        </div>
                        <div class="budget-bar">
                            <div class="budget-fill ${status}" style="width: ${Math.min(percentage, 100)}%; background-color: ${color}"></div>
                        </div>
                        <div class="budget-percentage">${percentage.toFixed(1)}%</div>
                    </div>
                `;
            });

            container.innerHTML = progressHTML;

            // Add CSS for budget progress if not already added
            if (!document.getElementById('budget-progress-styles')) {
                const style = document.createElement('style');
                style.id = 'budget-progress-styles';
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
        })
        .catch(error => {
            console.error('Error fetching budget progress data:', error);
        });
}

// 7. Top Merchants List
function initTopMerchants() {
    const container = document.getElementById('top-merchants');
    if (!container) return;

    // Fetch real merchant data from backend
    fetch('/dashboard/api/top-merchants/')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching top merchants data:', data.error);
                return;
            }

            const merchants = data.merchants || [];

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
                            <div class="merchant-amount">$${merchant.amount.toLocaleString()}</div>
                            <div class="merchant-count">${merchant.transactions} transactions</div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = merchantHTML;

            // Add CSS for merchant list if not already added
            if (!document.getElementById('merchant-list-styles')) {
                const style = document.createElement('style');
                style.id = 'merchant-list-styles';
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
        })
        .catch(error => {
            console.error('Error fetching top merchants data:', error);
        });
}
