import { useEffect, useState } from 'react';
import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import api from '../api/axios';
import type { AuditLog } from '../types';

const AuditLogPage = () => {
    const [logs, setLogs] = useState<AuditLog[]>([]);

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await api.get('/audit-logs/');
                setLogs(res.data.results);
            } catch (err) {
                console.error("Failed to fetch audit logs", err);
            }
        };
        fetchLogs();
    }, []);

    return (
        <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'text.primary', mb: 3 }}>
                System Audit Log
            </Typography>

            <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: 2 }}>
                <Table>
                    <TableHead sx={{ backgroundColor: '#f8fafc' }}>
                        <TableRow>
                            <TableCell><b>Timestamp</b></TableCell>
                            <TableCell><b>User</b></TableCell>
                            <TableCell><b>Action</b></TableCell>
                            <TableCell><b>Target</b></TableCell>
                            <TableCell><b>Metadata</b></TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {logs.map((log) => (
                            <TableRow key={log.id}>
                                <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                                <TableCell>{log.username || 'System'}</TableCell>
                                <TableCell>{log.action}</TableCell>
                                <TableCell>{log.target}</TableCell>
                                <TableCell>
                                    <pre style={{ margin: 0, fontSize: '0.8rem' }}>
                                        {JSON.stringify(log.metadata, null, 2)}
                                    </pre>
                                </TableCell>
                            </TableRow>
                        ))}
                        {logs.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={5} align="center">No audit logs found.</TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>
        </Box>
    );
};

export default AuditLogPage;
