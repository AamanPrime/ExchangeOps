import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import api from '../api/axios';
import type { Incident } from '../types';

const Incidents = () => {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        const fetchIncidents = async () => {
            let url = '/incidents/';
            if (filter !== 'all') {
                url += `?status=${filter}`;
            }
            try {
                const res = await api.get(url);
                setIncidents(res.data.results);
            } catch (err) {
                console.error("Failed to fetch incidents", err);
            }
        };
        fetchIncidents();
    }, [filter]);

    return (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" fontWeight="bold" color="text.primary">
                    Incident Timeline
                </Typography>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Status Filter</InputLabel>
                    <Select
                        value={filter}
                        label="Status Filter"
                        onChange={(e) => setFilter(e.target.value)}
                    >
                        <MenuItem value="all">All</MenuItem>
                        <MenuItem value="open">Open</MenuItem>
                        <MenuItem value="resolved">Resolved</MenuItem>
                    </Select>
                </FormControl>
            </Box>

            <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: 2 }}>
                <Table>
                    <TableHead sx={{ backgroundColor: '#f8fafc' }}>
                        <TableRow>
                            <TableCell><b>Exchange</b></TableCell>
                            <TableCell><b>Severity</b></TableCell>
                            <TableCell><b>Status</b></TableCell>
                            <TableCell><b>Opened</b></TableCell>
                            <TableCell><b>Resolved</b></TableCell>
                            <TableCell><b>Auto Resolved</b></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {incidents.map((incident) => (
                            <TableRow key={incident.id}>
                                <TableCell>{incident.exchange_name}</TableCell>
                                <TableCell>
                                    <Chip 
                                        label={incident.severity} 
                                        color={incident.severity === 'HIGH' ? 'error' : (incident.severity === 'MEDIUM' ? 'warning' : 'info')} 
                                        size="small" 
                                    />
                                </TableCell>
                                <TableCell>
                                    {incident.resolved_at ? (
                                        <Chip label="RESOLVED" color="success" size="small" variant="outlined"/>
                                    ) : (
                                        <Chip label="OPEN" color="error" size="small" variant="outlined"/>
                                    )}
                                </TableCell>
                                <TableCell>{new Date(incident.opened_at).toLocaleString()}</TableCell>
                                <TableCell>{incident.resolved_at ? new Date(incident.resolved_at).toLocaleString() : '-'}</TableCell>
                                <TableCell>{incident.auto_resolved ? 'Yes' : 'No'}</TableCell>
                            </TableRow>
                        ))}
                        {incidents.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={6} align="center">No incidents found.</TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};

export default Incidents;
