# Richtato - Personal Finance Management Platform

A comprehensive personal finance management application built with Django, featuring expense tracking, income management, budget planning, and advanced analytics with interactive visualizations.

## 🚀 Features

- **Expense & Income Tracking**: Categorize and track all financial transactions
- **Budget Management**: Set and monitor budgets by category with visual progress indicators
- **Interactive Dashboards**: Real-time analytics with Chart.js and Plotly.js visualizations
- **Sankey Diagrams**: Advanced cash flow visualization showing money movement
- **Account Management**: Multiple account types (checking, savings, investment, retirement)
- **Statement Import**: Automated import from bank statements and credit cards
- **AI-Powered Insights**: Intelligent financial analysis and recommendations
- **Responsive Design**: Modern, mobile-friendly interface
- **Demo Mode**: Try the application with sample data

## 🏗️ Project Structure

```
richtato/
├── richtato/                    # Main Django project
│   ├── apps/                   # Django applications
│   │   ├── account/           # Account management
│   │   ├── budget/            # Budget planning and tracking
│   │   ├── dashboard/         # Dashboard views and analytics
│   │   ├── expense/           # Expense tracking and categorization
│   │   ├── income/            # Income management
│   │   ├── richtato_user/     # User management and profiles
│   │   └── settings/          # Application settings
│   ├── categories/            # Expense categorization system
│   │   ├── categories.py      # Category definitions with icons and colors
│   │   └── categories_manager.py
│   ├── statement_imports/     # Bank statement import system
│   │   ├── accounts/          # Account-specific importers
│   │   └── cards/             # Credit card importers
│   │       ├── american_express.py
│   │       ├── bank_of_america.py
│   │       ├── chase.py
│   │       ├── citi.py
│   │       └── card_canonicalizer.py
│   ├── artificial_intelligence/ # AI features and insights
│   │   └── ai.py
│   ├── utilities/             # Utility functions and helpers
│   │   ├── postgres/          # PostgreSQL utilities
│   │   └── tools.py
│   ├── static/                # Static assets (CSS, JS, images)
│   │   ├── css/              # Stylesheets
│   │   ├── js/               # JavaScript files
│   │   ├── images/           # Image assets
│   │   └── webfonts/         # Font files
│   ├── pages/                 # HTML templates
│   └── richtato/              # Django project settings
├── pyproject.toml             # Python project configuration
├── run.sh                     # Development server script
├── create_or_reset_demo.sh    # Demo data setup script
└── README.md                  # This file
```

## 🛠️ Technology Stack

### Backend

- **Django 4.x**: Web framework
- **PostgreSQL**: Primary database
- **Python 3.9+**: Programming language
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations

### Frontend

- **HTML5/CSS3**: Structure and styling
- **JavaScript (ES6+)**: Client-side functionality
- **Chart.js**: Chart visualizations
- **Plotly.js**: Advanced charts and Sankey diagrams
- **Font Awesome**: Icons
- **DataTables**: Enhanced table functionality

### AI & Integrations

- **OpenAI**: AI-powered insights and analysis
- **Custom AI Models**: Built-in intelligent categorization

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Node.js (for frontend assets)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd richtato
   ```

2. **Set up Python environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Configure database**

   ```bash
   # Create PostgreSQL database
   createdb richtato_db

   # Run migrations
   python richtato/manage.py migrate
   ```

4. **Set up environment variables**

   ```bash
   # Create .env file with your configuration
   cp .env.example .env
   # Edit .env with your database and API credentials
   ```

5. **Run the development server**

   ```bash
   ./run.sh
   # Or manually:
   python richtato/manage.py runserver
   ```

6. **Access the application**
   - Open http://localhost:8000
   - Create a demo account or sign up

## 🎯 Key Components

### Expense Categorization System

- **Smart Categorization**: AI-powered automatic categorization
- **Custom Categories**: 20+ predefined categories with icons and colors
- **Keyword Matching**: Intelligent transaction matching
- **Visual Indicators**: Color-coded categories in charts and tables

### Dashboard Analytics

- **Income vs Expenses**: Monthly comparison charts
- **Cash Flow Sankey**: Interactive money flow visualization
- **Budget Progress**: Real-time budget tracking
- **Top Categories**: Spending analysis by category
- **Savings Trends**: Investment and savings tracking

### Statement Import System

- **Multi-format Support**: CSV, Excel, PDF imports
- **Bank Integration**: Support for major banks
- **Credit Card Support**: American Express, Chase, Citi, Bank of America
- **Automated Processing**: Smart transaction extraction and categorization
- **File Upload**: Direct file upload interface

### Budget Management

- **Category Budgets**: Set limits by expense category
- **Progress Tracking**: Visual progress bars and alerts
- **Monthly/Annual Views**: Flexible budget periods
- **Overspending Alerts**: Real-time notifications

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/richtato_db

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Django
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database Configuration

The application uses PostgreSQL for optimal performance with financial data. Key features:

- JSON fields for flexible data storage
- Full-text search capabilities
- Efficient indexing for large datasets
- Transaction support for data integrity

## 🚀 Deployment

### Production Setup

1. **Configure production database**
2. **Set up static file serving** (nginx recommended)
3. **Configure environment variables**
4. **Set up SSL certificates**
5. **Configure backup strategy**

### Docker Deployment (Single Service: Frontend + Backend + Nginx)

You can deploy with a single container that serves the React SPA via Nginx and proxies API requests to Django (Gunicorn) at `/api`.

```bash
# Build the multi-stage Docker image (inject the API base URL used by Vite build)
./build.sh richtato:latest https://your-hostname/api

# Run locally (expects a Postgres instance; update DATABASE_URL as needed)
./start.sh richtato:latest 10000

# Open the app
open http://localhost:10000
```

#### Environment Variables (Required)

Set these in your container or hosting environment:

```bash
# Django secret key
SECRET_KEY=your_django_secret

# Database connection (Render Postgres URL works; includes sslmode=require)
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require

# Deployment stage: PROD on Render, DEV/LOCAL for local
DEPLOY_STAGE=PROD

# Render sets this automatically; default to 10000 locally
PORT=10000
```

Vite frontend is built with `VITE_API_BASE_URL` passed as a build-arg and baked into the static assets. When using the single-container image with Nginx, use `/api` so the SPA and API share the same origin and cookies:

```bash
# Example build arg in CI/Render
VITE_API_BASE_URL=/api
```

#### Render (Docker) Deployment

1. Create a Render Web Service (Docker)

   - Root: repository root
   - Dockerfile: `Dockerfile`
   - Build Command: uses Dockerfile (no command needed)
   - Start Command: leave blank (Dockerfile CMD runs `/app/start.sh`)
   - Build Args:
     - `VITE_API_BASE_URL=/api`
   - Environment:
     - `SECRET_KEY=...`
     - `DATABASE_URL=...` (Render Postgres)
     - `DEPLOY_STAGE=PROD`

2. Ensure Allowed Hosts

   - Add your Render hostname to Django `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` if not already included.

3. Post-deploy
   - Migrations and collectstatic run automatically via the startup script.
   - Nginx listens on `$PORT` and proxies `/api` and `/admin` to Django on 8000.

## 📊 Data Models

### Core Models

- **User**: Extended user model with financial preferences
- **Account**: Bank accounts, credit cards, investment accounts
- **Expense**: Transaction records with categorization
- **Income**: Income sources and amounts
- **Category**: Expense categories with icons and colors
- **Budget**: Budget limits and tracking

### Relationships

- Users have multiple accounts
- Accounts have multiple transactions
- Transactions belong to categories
- Budgets are linked to categories and users

## 🎨 UI/UX Features

### Design System

- **Color Scheme**: Consistent color palette with category-specific colors
- **Typography**: Modern, readable fonts
- **Icons**: Font Awesome icons throughout
- **Responsive**: Mobile-first design approach

### Interactive Elements

- **Charts**: Interactive Chart.js visualizations
- **Sankey Diagrams**: Plotly.js cash flow diagrams
- **Tables**: Enhanced DataTables with sorting and filtering
- **Forms**: Real-time validation and feedback

## 🔒 Security

### Authentication

- Django's built-in authentication system
- Password reset functionality
- Session management
- CSRF protection

### Data Protection

- Encrypted sensitive data
- Secure API endpoints
- Input validation and sanitization
- SQL injection prevention

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python richtato/manage.py test

# Run specific app tests
python richtato/manage.py test richtato.apps.expense

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Structure

- Unit tests for models and utilities
- Integration tests for API endpoints
- Frontend tests for JavaScript components
- End-to-end tests for critical user flows

## 📈 Performance

### Optimization Strategies

- **Database Indexing**: Optimized queries for large datasets
- **Caching**: Redis caching for frequently accessed data
- **Static Assets**: Minified CSS and JavaScript
- **CDN**: Content delivery network for static files
- **Lazy Loading**: On-demand data loading

### Monitoring

- **Application Metrics**: Performance monitoring
- **Error Tracking**: Comprehensive error logging
- **User Analytics**: Usage pattern analysis

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards

- **Python**: PEP 8 style guide
- **JavaScript**: ESLint configuration
- **CSS**: Consistent naming conventions
- **Documentation**: Comprehensive docstrings

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Documentation

- [User Guide](docs/user-guide.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)

### Community

- [Issues](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)
- [Wiki](https://github.com/your-repo/wiki)

## 🔄 Changelog

### Version 1.0.0

- Initial release with core functionality
- Expense and income tracking
- Basic dashboard analytics
- Statement import system
- Budget management features

---

**Richtato** - Take control of your financial future with intelligent insights and powerful analytics.
