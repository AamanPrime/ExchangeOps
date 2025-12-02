import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
    AppBar, Toolbar, Typography, Drawer, List, ListItem,
    ListItemButton, ListItemIcon, ListItemText, Box, Button,
    CssBaseline, Divider
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { useAuth } from '../context/AuthContext';

const drawerWidth = 240;

const Layout = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    if (!user) {
        return <Outlet />; // Allow login page to render without layout
    }

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const navItems = [
        { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard', roles: ['quant', 'infra', 'compliance', 'ops', 'admin'] },
        { text: 'Incidents', icon: <ReceiptLongIcon />, path: '/incidents', roles: ['quant', 'infra', 'compliance', 'ops', 'admin'] },
        { text: 'Audit Log', icon: <LibraryBooksIcon />, path: '/audit-log', roles: ['compliance', 'admin'] },
    ];

    return (
        <Box sx={{ display: 'flex' }}>
            <CssBaseline />
            <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, backgroundColor: '#1e293b' }}>
                <Toolbar>
                    <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
                        ExchangeOps Platform
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="body1">
                            {user.username} ({user.role.toUpperCase()})
                        </Typography>
                        <Button color="inherit" onClick={handleLogout} variant="outlined" size="small">
                            Logout
                        </Button>
                    </Box>
                </Toolbar>
            </AppBar>
            <Drawer
                variant="permanent"
                sx={{
                    width: drawerWidth,
                    flexShrink: 0,
                    [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box', backgroundColor: '#f8fafc' },
                }}
            >
                <Toolbar />
                <Box sx={{ overflow: 'auto', mt: 2 }}>
                    <List>
                        {navItems.map((item) => (
                            item.roles.includes(user.role) ? (
                                <ListItem key={item.text} disablePadding>
                                    <ListItemButton
                                        selected={location.pathname.startsWith(item.path)}
                                        onClick={() => navigate(item.path)}
                                    >
                                        <ListItemIcon sx={{ color: location.pathname.startsWith(item.path) ? '#1976d2' : 'inherit' }}>
                                            {item.icon}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={item.text}
                                            primaryTypographyProps={{
                                                fontWeight: location.pathname.startsWith(item.path) ? 'bold' : 'normal'
                                            }}
                                        />
                                    </ListItemButton>
                                </ListItem>
                            ) : null
                        ))}
                    </List>
                </Box>
            </Drawer>
            <Box component="main" sx={{ flexGrow: 1, p: 3, backgroundColor: '#f1f5f9', minHeight: '100vh' }}>
                <Toolbar />
                <Outlet />
            </Box>
        </Box>
    );
};

export default Layout;
