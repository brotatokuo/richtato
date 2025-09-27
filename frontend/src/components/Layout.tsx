import {
  CloudUpload,
  PieChart,
  Settings,
  Table,
  TrendingUp,
  Wallet,
} from 'lucide-react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';

// Route to page title and icon mapping
const routeConfig: Record<
  string,
  { title: string; icon: React.ComponentType<{ className?: string }> }
> = {
  '/budget': { title: 'Budget', icon: Wallet },
  '/assets': { title: 'Assets', icon: PieChart },
  '/data': { title: 'Data', icon: Table },
  '/cashflow': { title: 'Cashflow', icon: TrendingUp },
  '/upload': { title: 'Upload', icon: CloudUpload },
  '/settings': { title: 'Settings', icon: Settings },
};

export function Layout() {
  const location = useLocation();

  // Get the current page config based on the route
  const currentPageConfig =
    routeConfig[location.pathname] || routeConfig['/dashboard'];
  const IconComponent = currentPageConfig.icon;

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
          <div className="mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <IconComponent className="h-8 w-8 text-foreground" />
                <h1 className="text-2xl font-semibold text-foreground">
                  {currentPageConfig.title}
                </h1>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto scrollbar-thin">
          <div className="mx-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
