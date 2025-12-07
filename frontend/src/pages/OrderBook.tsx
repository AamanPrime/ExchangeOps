import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Typography, Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import type { OrderBook } from '../types';

const OrderBookPage = () => {
    const { exchangeName } = useParams();
    const navigate = useNavigate();
    const [orderBook, setOrderBook] = useState<OrderBook | null>(null);

    useEffect(() => {
        // Fetch orderbook from simulator directly or via Django proxy.
        // We can just hit the Simulator URL since it's on localhost:8088, but CORS might be an issue if not configured.
        // Let's assume we can hit it directly since the guide says "proxied through Django or directly from simulator".
        // The Go server has CheckOrigin: return true.
        const fetchOrderBook = async () => {
            try {
                const res = await fetch(`http://localhost:8088/exchanges/${exchangeName}/orderbook`);
                if (res.ok) {
                    const data = await res.json();
                    setOrderBook(data);
                }
            } catch (err) {
                console.error("Failed to fetch order book", err);
            }
        };

        fetchOrderBook();
        const interval = setInterval(fetchOrderBook, 2000);
        return () => clearInterval(interval);
    }, [exchangeName]);

    return (
        <Box>
            <Box display="flex" alignItems="center" mb={3}>
                <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)} sx={{ mr: 2 }}>
                    Back
                </Button>
                <Typography variant="h4" fontWeight="bold">
                    Order Book: {exchangeName}
                </Typography>
            </Box>

            <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" color="success.main" gutterBottom>
                            Bids (Buy)
                        </Typography>
                        <TableContainer>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell><b>Price</b></TableCell>
                                        <TableCell align="right"><b>Size</b></TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {orderBook?.bids.map((b, i) => (
                                        <TableRow key={i}>
                                            <TableCell sx={{ color: 'success.main', fontWeight: 'bold' }}>{b.price.toFixed(2)}</TableCell>
                                            <TableCell align="right">{b.size}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" color="error.main" gutterBottom>
                            Asks (Sell)
                        </Typography>
                        <TableContainer>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell><b>Price</b></TableCell>
                                        <TableCell align="right"><b>Size</b></TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {orderBook?.asks.map((a, i) => (
                                        <TableRow key={i}>
                                            <TableCell sx={{ color: 'error.main', fontWeight: 'bold' }}>{a.price.toFixed(2)}</TableCell>
                                            <TableCell align="right">{a.size}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default OrderBookPage;
