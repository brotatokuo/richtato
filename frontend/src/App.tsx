import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { HouseholdProvider } from './contexts/HouseholdContext';
import { PreferencesProvider } from './contexts/PreferencesContext';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Welcome } from './pages/Welcome';

const Dashboard = lazy(() =>
  import('./pages/BudgetDashboard').then(m => ({ default: m.Dashboard }))
);
const Cashflow = lazy(() =>
  import('./pages/Cashflow').then(m => ({ default: m.Cashflow }))
);
const DataTable = lazy(() =>
  import('./pages/DataTable').then(m => ({ default: m.DataTable }))
);
const ReportPage = lazy(() =>
  import('./pages/ReportPage').then(m => ({ default: m.ReportPage }))
);
const Upload = lazy(() =>
  import('./pages/Upload').then(m => ({ default: m.Upload }))
);
const Profile = lazy(() =>
  import('./pages/Profile').then(m => ({ default: m.Profile }))
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

function App() {
  return (
    <AuthProvider>
      <HouseholdProvider>
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
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/report" replace />} />
                <Route
                  path="budget"
                  element={
                    <Suspense fallback={null}>
                      <Dashboard />
                    </Suspense>
                  }
                />
                <Route
                  path="data"
                  element={
                    <Suspense fallback={null}>
                      <DataTable />
                    </Suspense>
                  }
                />
                <Route
                  path="cashflow"
                  element={
                    <Suspense fallback={null}>
                      <Cashflow />
                    </Suspense>
                  }
                />
                <Route
                  path="report"
                  element={
                    <Suspense fallback={null}>
                      <ReportPage />
                    </Suspense>
                  }
                />
                <Route
                  path="upload"
                  element={
                    <Suspense fallback={null}>
                      <Upload />
                    </Suspense>
                  }
                />
                <Route
                  path="profile"
                  element={
                    <Suspense fallback={null}>
                      <Profile />
                    </Suspense>
                  }
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
      </HouseholdProvider>
    </AuthProvider>
  );
}

export default App;
