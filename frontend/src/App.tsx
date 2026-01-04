import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { PreferencesProvider } from './contexts/PreferencesContext';
import { AnnualAnalysisPage } from './pages/AnnualAnalysisPage';
import { AssetDashboard } from './pages/AssetDashboard';
import { Dashboard } from './pages/BudgetDashboard';
import { Cashflow } from './pages/Cashflow';
import { DataTable } from './pages/DataTable';
import { Login } from './pages/Login';
import { Preferences } from './pages/Preferences';
import { Profile } from './pages/Profile';
import { Register } from './pages/Register';
import { Setup } from './pages/Setup';
import { Upload } from './pages/Upload';
import { Welcome } from './pages/Welcome';

function App() {
  return (
    <AuthProvider>
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
              <Route index element={<Navigate to="/budget" replace />} />
              <Route path="budget" element={<Dashboard />} />
              <Route path="assets" element={<AssetDashboard />} />
              <Route path="data" element={<DataTable />} />
              <Route path="cashflow" element={<Cashflow />} />
              <Route path="annual-analysis" element={<AnnualAnalysisPage />} />
              <Route path="upload" element={<Upload />} />
              <Route path="profile" element={<Profile />} />
              <Route path="preferences" element={<Preferences />} />
              <Route path="setup" element={<Setup />} />
              <Route
                path="settings"
                element={<Navigate to="/preferences" replace />}
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </PreferencesProvider>
    </AuthProvider>
  );
}

export default App;
