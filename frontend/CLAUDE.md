# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Neuron v2 Frontend is a **React-based datacenter asset management interface** built with modern web technologies. It provides a comprehensive dashboard for managing electrical infrastructure in datacenters, complementing the Django backend API.

## Development Commands

### Core Development

```bash
# Install dependencies
yarn install

# Start development server (runs on port 5927)
yarn dev

# Build for production
yarn build

# Preview production build
yarn preview

# Type checking
yarn type-check
```

### Code Quality

```bash
# Run ESLint
yarn lint

# Run ESLint with auto-fix
yarn lint:fix

# Format code with Prettier
yarn format

# Check code formatting
yarn format:check
```

### Testing

```bash
# Run tests in watch mode
yarn test

# Run tests once
yarn test:run

# Run tests with coverage report
yarn test:coverage

# Open interactive Vitest UI
yarn test:ui
```

### Docker Development

```bash
# Using helper script
./docker-dev.sh build    # Build Docker image
./docker-dev.sh start    # Start container
./docker-dev.sh logs     # View logs
./docker-dev.sh shell    # Open shell in container
./docker-dev.sh stop     # Stop container
./docker-dev.sh restart  # Restart container

# Direct docker-compose commands
docker-compose up frontend -d
docker-compose logs frontend
docker-compose down
```

## Architecture Overview

### Tech Stack

- **React 19.1.1** with TypeScript for the UI layer
- **React Router 7.1.1** for client-side routing with nested routes
- **Vite 7.1.6** as build tool with HMR and fast development
- **Tailwind CSS 3.4.17** for utility-first styling
- **Shadcn/UI** component library for consistent design system
- **Vitest 2.1.8** for testing with jsdom environment
- **ESLint 9** with flat config and TypeScript support

### Application Structure

#### Routing Architecture

The app uses React Router 7 with a nested route structure:

- **Layout Route**: Wraps all pages with sidebar navigation
- **Index Route**: Redirects to `/dashboard`
- **Feature Routes**: Dashboard, Organization, Facility, Power Flow, Energy Storage, Maintenance, Logs, Users, Asset Management, Settings

#### Component Architecture

- **`src/App.tsx`**: Root component with BrowserRouter and route definitions
- **`src/components/Layout.tsx`**: Main layout wrapper with sidebar and outlet
- **`src/components/Sidebar.tsx`**: Collapsible navigation with state management
- **`src/components/ui/`**: Shadcn/UI component library (Button, Card, etc.)
- **`src/pages/`**: Page-level route components
- **`src/lib/utils.ts`**: Utility functions including Tailwind class merging

#### Key Features

- **Collapsible Sidebar**: State-managed navigation that toggles between full and icon-only modes
- **Path Aliases**: `@/` mapped to `src/` for clean imports
- **Theme System**: CSS custom properties with Tailwind integration
- **Responsive Design**: Mobile-first approach with Tailwind responsive classes

### Testing Architecture

#### Test Configuration

- **Vitest** with jsdom environment for DOM testing
- **Testing Library** for React component testing
- **Coverage** with V8 provider and multiple output formats
- **Setup Files**: Global test utilities and DOM mocks

#### Test Structure

```
tests/
├── components/         # Component tests
├── pages/             # Page component tests
├── test-utils/        # Testing utilities and setup
│   ├── setup.ts       # Global test setup and mocks
│   ├── providers.tsx  # Test providers wrapper
│   └── utils.tsx      # Custom render functions
└── App.test.tsx       # App-level integration tests
```

#### Test Utilities

- **DOM Mocks**: matchMedia, ResizeObserver, IntersectionObserver
- **Custom Providers**: Wrapper for context providers in tests
- **Jest DOM**: Extended matchers for DOM assertions

## Development Patterns

### Component Development

1. Use functional components with TypeScript interfaces for props
2. Leverage Shadcn/UI components for consistency
3. Apply Tailwind classes with `cn()` utility for conditional styling
4. Use Lucide React for icons throughout the application

### State Management

- React Router's `useLocation` for route-aware components
- Local component state with `useState` for UI interactions
- No global state management library currently implemented

### Styling Patterns

- **Utility-First**: Tailwind CSS classes for styling
- **Component Variants**: Use `class-variance-authority` for component styling
- **CSS Custom Properties**: Theme system with HSL color values
- **Responsive Design**: Mobile-first breakpoints

### Testing Patterns

- **Component Testing**: Test user interactions and rendering
- **Setup Files**: Global mocks and test environment configuration
- **Coverage Requirements**: Comprehensive test coverage with V8 reporting

## Configuration Files

### Build Configuration

- **`vite.config.ts`**: Vite build configuration with React plugin and path aliases
- **`vitest.config.ts`**: Test configuration with jsdom and coverage setup
- **`tsconfig.json`**: TypeScript configuration with strict mode and path mapping

### Code Quality

- **`eslint.config.js`**: ESLint flat config with TypeScript and React rules
- **`tailwind.config.js`**: Tailwind configuration with custom theme extension
- **`postcss.config.js`**: PostCSS configuration for Tailwind processing

### Package Management

- **Yarn** is the preferred package manager (version 1.22.22)
- **Node.js 24.0.0** for Docker environment compatibility

## Development Server

The application runs on **port 5927** in development mode with:

- Hot Module Replacement (HMR) for instant updates
- Source maps enabled for debugging
- Host binding enabled for Docker compatibility

## Important Files

- **`src/App.tsx`**: Main application component with routing configuration
- **`src/components/Layout.tsx`**: Layout wrapper with sidebar integration
- **`src/components/Sidebar.tsx`**: Navigation component with collapse functionality
- **`package.json`**: Dependencies and development scripts
- **`vite.config.ts`**: Build tool configuration
- **`vitest.config.ts`**: Test framework configuration
- **`tests/test-utils/setup.ts`**: Global test setup and browser API mocks
