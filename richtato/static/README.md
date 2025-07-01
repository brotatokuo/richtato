# Static Files Organization

This directory contains all static assets for the Richtato application, organized for production readiness and maintainability.

## Directory Structure

```
static/
├── css/                    # Stylesheets
│   ├── variables.css       # CSS custom properties (colors, spacing, etc.)
│   ├── base.css           # Base styles and resets
│   ├── components.css     # Reusable component styles
│   ├── layout.css         # Layout and navigation styles
│   ├── navbar.css         # Navigation bar specific styles
│   ├── main.css           # Main stylesheet (imports all others)
│   ├── core-legacy.css    # Legacy core styles (for reference)
│   └── style-legacy.css   # Legacy main styles (for reference)
├── js/                    # JavaScript files
│   ├── components/        # Reusable components
│   │   ├── navigation.js  # Navigation and sidebar management
│   │   ├── richTable.js   # DataTables enhancements
│   │   ├── budgetRenderer.js  # Budget visualization
│   │   └── timeseriesGraph.js # Time series charts
│   ├── pages/             # Page-specific scripts
│   │   ├── dashboard.js   # Dashboard functionality
│   │   ├── table.js       # Table page
│   │   ├── input.js       # Input forms
│   │   ├── upload.js      # File upload handling
│   │   ├── budget.js      # Budget management
│   │   ├── graph.js       # Graph visualizations
│   │   ├── assets.js      # Assets management
│   │   ├── accountSettings.js # Account settings
│   │   └── welcome.js     # Welcome page
│   └── utils/             # Utility functions
│       ├── api.js         # API client and HTTP utilities
│       ├── helpers.js     # Common helper functions
│       └── common.js      # Legacy common utilities
├── images/                # Image assets
├── media/                 # Media files (videos, gifs, etc.)
├── webfonts/             # Font files
├── all.min.css           # Font Awesome CSS
└── README.md             # This file
```

## CSS Architecture

### Import Order (in main.css)
1. `variables.css` - CSS custom properties
2. `base.css` - Resets and base styles
3. `components.css` - Reusable component styles
4. `layout.css` - Layout and navigation
5. `navbar.css` - Navigation specific styles

### CSS Naming Conventions
- Use BEM methodology where appropriate
- Prefix component classes consistently
- Use semantic class names

### CSS Variables
All colors, spacing, and common values are defined in `variables.css` using CSS custom properties for easy theming and maintenance.

## JavaScript Architecture

### Module Organization
- **Components**: Reusable UI components and widgets
- **Pages**: Page-specific functionality
- **Utils**: Shared utilities and helpers

### Key Features
- ES6+ classes for better organization
- Event delegation for performance
- Throttled scroll/resize handlers
- Centralized API client
- Toast notifications system
- Form validation utilities

### Dependencies
- jQuery 3.6.0
- DataTables 1.13.6
- Chart.js (latest)
- Font Awesome 6.2.0

## Production Considerations

### Performance
- CSS is organized for minimal blocking
- JavaScript uses event delegation
- Throttled event handlers for scroll/resize
- Efficient DOM queries with caching

### Maintainability
- Clear separation of concerns
- Modular architecture
- Consistent naming conventions
- Documented utility functions

### Browser Support
- Modern browsers (ES6+ features used)
- Graceful degradation for older browsers
- Responsive design throughout

## Usage

### Including Styles
Main stylesheet is included in base template:
```html
<link rel="stylesheet" href="{% static 'css/main.css' %}" />
```

### Including Scripts
Core utilities and navigation are included in base template. Page-specific scripts should be included in individual templates:
```html
<script src="{% static 'js/pages/dashboard.js' %}"></script>
```

### Adding New Components
1. Create new file in appropriate directory
2. Follow existing naming conventions
3. Export/expose functionality appropriately
4. Update documentation

## Migration Notes

Legacy files have been preserved with `-legacy` suffix for reference during migration. These can be safely removed once all functionality is confirmed working with the new structure.
