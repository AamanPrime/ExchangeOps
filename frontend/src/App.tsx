import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import OrderBookPage from './pages/OrderBook';
import AuditLogPage from './pages/AuditLog';
import { ThemeProvider, createTheme } from '@mui/material/styles';

const theme = createTheme({
    palette: {
        primary: {
            main: '#1e293b',
        },
        secondary: {
            main: '#3b82f6',
        },
        background: {
            default: '#f8fafc',
        }
    },
    typography: {
        fontFamily: 'Inter, sans-serif',
    }
});

function App() {
    return (
        <ThemeProvider theme={theme}>
            <AuthProvider>
                <BrowserRouter>
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/" element={<Layout />}>
                            <Route index element={<Navigate to="/dashboard" replace />} />
                            <Route path="dashboard" element={<Dashboard />} />
                            <Route path="incidents" element={<Incidents />} />
                            <Route path="orderbook/:exchangeName" element={<OrderBookPage />} />
                            <Route path="audit-log" element={<AuditLogPage />} />
                        </Route>
                    </Routes>
                </BrowserRouter>
            </AuthProvider>
        </ThemeProvider>
    );
}

export default App;
