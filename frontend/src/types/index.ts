export interface Exchange {
    id: number;
    name: string;
    simulator_base_url: string;
}

export interface Incident {
    id: number;
    exchange: number;
    exchange_name: string;
    opened_at: string;
    resolved_at: string | null;
    severity: string;
    auto_resolved: boolean;
}

export interface OrderBook {
    bids: { price: number; size: number }[];
    asks: { price: number; size: number }[];
}

export interface AuditLog {
    id: number;
    timestamp: string;
    username: string | null;
    action: string;
    target: string;
    metadata: any;
}
