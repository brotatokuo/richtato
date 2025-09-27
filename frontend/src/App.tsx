import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { AssetDashboard } from './pages/AssetDashboard';
import { Cashflow } from './pages/Cashflow';
import { DataTable } from './pages/DataTable';
import { Login } from './pages/Login';
import { Profile } from './pages/Profile';
import { Register } from './pages/Register';
import { Settings } from './pages/Settings';
import { Dashboard } from './pages/TransactionDashboard';
import { Upload } from './pages/Upload';
import { Welcome } from './pages/Welcome';

function App() {
  return (
    <AuthProvider>
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
            <Route path="upload" element={<Upload />} />
            <Route path="profile" element={<Profile />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
