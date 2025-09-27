# Neuron v2 Frontend

A modern React application built with TypeScript and Vite.

## Tech Stack

- **React 19.1.1** - Latest React with new features and optimizations
- **React Router 7.1.1** - Client-side routing with latest features
- **TypeScript 5.9.2** - Static type checking with latest features
- **Vite 7.1.6** - Ultra-fast build tool and dev server
- **Tailwind CSS 3.4.17** - Utility-first CSS framework
- **Shadcn/UI** - Beautiful and accessible component library
- **Lucide React** - Icon library with 1000+ icons
- **Vitest 2.1.8** - Fast unit testing framework
- **Testing Library** - React component testing utilities
- **Node.js 24.0.0** - Latest LTS Node.js runtime (Docker)
- **ESLint 9.35.0** - Code linting with flat config
- **Prettier 3.6.2** - Code formatting

## Getting Started

### Prerequisites

- Node.js (version 16 or higher)
- Yarn package manager

### Installation

1. Install dependencies:

   ```bash
   yarn install
   ```

2. Start the development server:

   ```bash
   yarn dev
   ```

3. Open your browser and navigate to `http://localhost:5927`

## Docker Development

The frontend can also be run using Docker for a consistent development environment.

### Prerequisites for Docker

- Docker and Docker Compose installed

### Docker Commands

Using the helper script:

```bash
# Build the Docker image
./docker-dev.sh build

# Start the container
./docker-dev.sh start

# View logs
./docker-dev.sh logs

# Stop the container
./docker-dev.sh stop

# Open shell in container
./docker-dev.sh shell

# Restart container
./docker-dev.sh restart
```

Or using docker-compose directly:

```bash
# From the project root
docker-compose up frontend -d
docker-compose logs frontend
docker-compose down
```

The Docker setup includes:

- Hot reloading with volume mounts
- Environment variable support
- Optimized build process
- Development server accessible on port 5927

## Available Scripts

- `yarn dev` - Start development server
- `yarn build` - Build for production
- `yarn preview` - Preview production build
- `yarn lint` - Run ESLint
- `yarn lint:fix` - Run ESLint with auto-fix
- `yarn format` - Format code with Prettier
- `yarn format:check` - Check code formatting
- `yarn type-check` - Run TypeScript type checking
- `yarn test` - Run tests in watch mode
- `yarn test:run` - Run tests once
- `yarn test:coverage` - Run tests with coverage report
- `yarn test:ui` - Open Vitest UI for interactive testing

## Project Structure

```
src/
├── App.tsx          # Main App component
├── App.css          # App styles
├── main.tsx         # Application entry point
├── index.css        # Global styles
└── vite-env.d.ts    # Vite type definitions
```

## Development

## Features

- **🚀 Modern UI** - Built with Shadcn/UI and Tailwind CSS
- **📱 Responsive Design** - Mobile-first responsive layout
- **🎨 Dark/Light Mode** - Theme support with CSS custom properties
- **🧭 Client-side Routing** - React Router 7 with nested routes
- **📊 Dashboard** - Comprehensive energy management dashboard
- **🏢 Multi-page Application** - Organization, Facility, Power Flow, Energy Storage, Maintenance, Logs, Users, Asset Management, and Settings
- **🔧 Collapsible Sidebar** - Space-efficient navigation with icons
- **⚡ Fast Development** - Hot Module Replacement (HMR)
- **🔒 Type Safety** - Full TypeScript support
- **📏 Code Quality** - ESLint and Prettier configuration
- **🎯 Path Aliases** - Clean imports with `@/` mapping to `src/`
- **🧪 Unit Testing** - Comprehensive test suite with Vitest
- **📊 Test Coverage** - Coverage reporting with V8
- **🔍 Test UI** - Interactive testing interface

## Project Structure

```
src/
├── components/
│   ├── ui/           # Shadcn/UI components
│   ├── Layout.tsx    # Main layout component
│   └── Sidebar.tsx   # Collapsible navigation sidebar
├── pages/            # Route components
│   ├── Dashboard.tsx
│   ├── Organization.tsx
│   ├── Facility.tsx
│   ├── PowerFlow.tsx
│   ├── EnergyStorage.tsx
│   ├── Maintenance.tsx
│   ├── Logs.tsx
│   ├── Users.tsx
│   ├── AssetManagement.tsx
│   └── Settings.tsx
├── lib/
│   └── utils.ts      # Utility functions
├── App.tsx           # Root component with routing
├── main.tsx          # Application entry point
└── index.css         # Global styles and Tailwind directives

tests/                # Test files (mirrors src structure)
├── components/
│   ├── ui/
│   │   ├── button.test.tsx
│   │   └── card.test.tsx
│   └── Sidebar.test.tsx
├── pages/
│   └── Dashboard.test.tsx
├── lib/
│   └── utils.test.ts
├── test-utils/       # Testing utilities
│   ├── setup.ts      # Test environment setup
│   ├── providers.tsx # Test providers
│   └── utils.tsx     # Custom render functions
└── App.test.tsx      # App-level tests
```

The project is configured with:

## Building

To build the project for production:

```bash
yarn build
```

The built files will be in the `dist/` directory.
