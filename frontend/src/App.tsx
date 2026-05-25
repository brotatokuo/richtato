import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import { DriveSetupGate } from './components/DriveSetupGate';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { DriveProvider } from './contexts/DriveContext';
import { HouseholdProvider } from './contexts/HouseholdContext';
import { PreferencesProvider } from './contexts/PreferencesContext';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Welcome } from './pages/Welcome';

const Dashboard = lazy(() =>
  import('./pages/BudgetDashboard').then(m => ({ default: m.Dashboard }))
);
const DataTable = lazy(() =>
  import('./pages/DataTable').then(m => ({ default: m.DataTable }))
);
const ReportPage = lazy(() =>
  import('./pages/ReportPage').then(m => ({ default: m.ReportPage }))
);
const Preferences = lazy(() =>
  import('./pages/Preferences').then(m => ({ default: m.Preferences }))
);
const Setup = lazy(() =>
  import('./pages/Setup').then(m => ({ default: m.Setup }))
);
const Accounts = lazy(() =>
  import('./pages/Accounts').then(m => ({ default: m.Accounts }))
);
const More = lazy(() =>
  import('./pages/More').then(m => ({ default: m.More }))
);
const HouseholdDashboard = lazy(() =>
  import('./pages/HouseholdDashboard').then(m => ({
    default: m.HouseholdDashboard,
  }))
);
const Formulas = lazy(() =>
  import('./pages/Formulas').then(m => ({ default: m.Formulas }))
);
const BankAgent = lazy(() =>
  import('./pages/BankAgent').then(m => ({ default: m.BankAgent }))
);
function App() {
  return (
    <AuthProvider>
      <HouseholdProvider>
        <DriveProvider>
          <PreferencesProvider>
            <Toaster position="top-right" richColors closeButton />
            <BrowserRouter>
              <Routes>
                <Route path="/welcome" element={<Welcome />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route
                  path="/"
                  element={
                    <ProtectedRoute>
                      <DriveSetupGate>
                        <Layout />
                      </DriveSetupGate>
                    </ProtectedRoute>
                  }
                >
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route
                    path="budget"
                    element={
                      <Suspense fallback={null}>
                        <Dashboard />
                      </Suspense>
                    }
                  />
                  <Route
                    path="transactions"
                    element={
                      <Suspense fallback={null}>
                        <DataTable />
                      </Suspense>
                    }
                  />
                  <Route
                    path="cashflow"
                    element={<Navigate to="/dashboard" replace />}
                  />
                  <Route
                    path="dashboard"
                    element={
                      <Suspense fallback={null}>
                        <ReportPage />
                      </Suspense>
                    }
                  />
                  <Route
                    path="profile"
                    element={<Navigate to="/preferences" replace />}
                  />
                  <Route
                    path="preferences"
                    element={
                      <Suspense fallback={null}>
                        <Preferences />
                      </Suspense>
                    }
                  />
                  <Route
                    path="setup"
                    element={
                      <Suspense fallback={null}>
                        <Setup />
                      </Suspense>
                    }
                  />
                  <Route
                    path="accounts"
                    element={
                      <Suspense fallback={null}>
                        <Accounts />
                      </Suspense>
                    }
                  />
                  <Route
                    path="household"
                    element={
                      <Suspense fallback={null}>
                        <HouseholdDashboard />
                      </Suspense>
                    }
                  />
                  <Route
                    path="formulas"
                    element={
                      <Suspense fallback={null}>
                        <Formulas />
                      </Suspense>
                    }
                  />
                  <Route
                    path="bank-agent"
                    element={
                      <Suspense fallback={null}>
                        <BankAgent />
                      </Suspense>
                    }
                  />
                  <Route
                    path="bank-automation"
                    element={<Navigate to="/bank-agent" replace />}
                  />
                  <Route
                    path="settings"
                    element={<Navigate to="/preferences" replace />}
                  />
                  <Route
                    path="more"
                    element={
                      <Suspense fallback={null}>
                        <More />
                      </Suspense>
                    }
                  />
                </Route>
              </Routes>
            </BrowserRouter>
          </PreferencesProvider>
        </DriveProvider>
      </HouseholdProvider>
    </AuthProvider>
  );
}

export default App;
