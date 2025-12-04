import React, { useEffect, useState, useRef } from 'react';
import { Box, Typography, Grid, Card, CardContent, CardActions, Button, Chip, Snackbar, Alert } from '@mui/material';
import { useAuth } from '../context/AuthContext';
import type { Exchange } from '../types';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [exchanges, setExchanges] = useState<Exchange[]>([]);
    const [toast, setToast] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        const fetchExchanges = async () => {
            try {
                const res = await api.get('/exchanges/');
                // API returns a paginated response: { results: [...], count, next, previous }
                const data = res.data;
                setExchanges(Array.isArray(data) ? data : (data.results ?? []));
            } catch (err) {
                console.error("Failed to fetch exchanges", err);
            }
        };

        fetchExchanges();

        // Connect WebSocket – derive ws(s):// from the API base URL env var,
        // or fall back to localhost. Fails gracefully if ASGI server isn't running.
        const apiBase = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';
        const wsBase = apiBase
            .replace(/^https/, 'wss')
            .replace(/^http/, 'ws')
            .replace(/\/api\/?$/, '');
        const wsUrl = `${wsBase}/ws/monitoring/`;

        try {
            ws.current = new WebSocket(wsUrl);

            ws.current.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (Array.isArray(data) || data?.type === 'exchange_update') {
                    fetchExchanges();
                }
            };

            ws.current.onerror = () => {
                // ASGI not running – silently degrade to polling-only
                console.warn('WebSocket unavailable, using REST polling only.');
            };
        } catch {
            console.warn('WebSocket construction failed, using REST polling only.');
        }

        return () => {
            ws.current?.close();
        };
    }, []);

    const handleRestart = async (id: number) => {
        try {
            await api.post(`/exchanges/${id}/restart/`);
            setToast({ open: true, message: 'Restart command sent successfully', severity: 'success' });
        } catch (err) {
            setToast({ open: true, message: 'Failed to restart exchange', severity: 'error' });
        }
    };

    // We fetch the statuses from Simulator via another api call because Exchange model doesn't have status
    // Actually, poll_exchanges updates ConnectionEvents, but doesn't update Exchange.
    // So the latest status is in the latest ConnectionEvent.
    // I will fetch the latest ConnectionEvent per exchange.
    const [statuses, setStatuses] = useState<Record<number, any>>({});
    
    useEffect(() => {
        const fetchStatuses = async () => {
            const statusMap: Record<number, any> = {};
            for (let ex of exchanges) {
                try {
                    const res = await api.get(`/connection-events/?exchange=${ex.id}&limit=1`);
                    if (res.data.results && res.data.results.length > 0) {
                        statusMap[ex.id] = res.data.results[0];
                    }
                } catch (e) {
                    // Ignore
                }
            }
            setStatuses(statusMap);
        };
        if (exchanges.length > 0) fetchStatuses();
    }, [exchanges]);


    return (
        <Box>
            <Typography variant="h4" gutterBottom fontWeight="bold" color="text.primary">
                Connection Health
            </Typography>
            <Grid container spacing={3}>
                {exchanges.map((exchange) => {
                    const latestEvent = statuses[exchange.id];
                    const status = latestEvent?.status || 'UNKNOWN';
                    
                    let color: 'success' | 'warning' | 'error' | 'default' = 'default';
                    if (status === 'UP') color = 'success';
                    if (status === 'DEGRADED') color = 'warning';
                    if (status === 'DOWN') color = 'error';

                    const canRestart = user?.role === 'infra' || user?.role === 'ops' || user?.role === 'admin';

                    return (
                        <Grid item xs={12} sm={6} md={4} key={exchange.id}>
                            <Card sx={{ borderRadius: 2, boxShadow: 2 }}>
                                <CardContent>
                                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                                        <Typography variant="h6" fontWeight="bold">
                                            {exchange.name}
                                        </Typography>
                                        <Chip label={status} color={color} size="small" />
                                    </Box>
                                    <Typography variant="body2" color="text.secondary">
                                        Last Check: {latestEvent ? new Date(latestEvent.recorded_at).toLocaleTimeString() : 'N/A'}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Misses: {latestEvent?.consecutive_misses || 0}
                                    </Typography>
                                </CardContent>
                                <CardActions>
                                    <Button size="small" onClick={() => navigate(`/orderbook/${exchange.name}`)}>
                                        View Book
                                    </Button>
                                    {canRestart && (
                                        <Button size="small" color="secondary" onClick={() => handleRestart(exchange.id)}>
                                            Restart
                                        </Button>
                                    )}
                                </CardActions>
                            </Card>
                        </Grid>
                    );
                })}
            </Grid>

            <Snackbar open={toast.open} autoHideDuration={6000} onClose={() => setToast({ ...toast, open: false })}>
                <Alert onClose={() => setToast({ ...toast, open: false })} severity={toast.severity} sx={{ width: '100%' }}>
                    {toast.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default Dashboard;
