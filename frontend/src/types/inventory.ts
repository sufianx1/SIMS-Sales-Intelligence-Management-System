export interface InventoryItem {
  inventory_id: string;
  company_id: number;
  store_id: number;
  store_name: string;
  product_id: string;
  product_name: string;
  sku: string;
  category: string;
  quantity_on_hand: number;
  min_threshold: number;
  max_threshold: number;
  unit_cost: number;
  unit_price: number;
  valuation: number;
  status: 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK';
  last_updated: string;
}

export interface InventoryMovement {
  movement_id: string;
  company_id: number;
  from_store_id?: number | null;
  from_store_name?: string | null;
  to_store_id?: number | null;
  to_store_name?: string | null;
  product_id: string;
  product_name: string;
  quantity: number;
  movement_type: 'RECEIPT' | 'TRANSFER' | 'ADJUSTMENT';
  reason: string;
  performed_by: number;
  timestamp: string;
}

export interface InventoryAlert {
  product_id: string;
  product_name: string;
  store_id: number;
  store_name: string;
  quantity_on_hand: number;
  min_threshold: number;
  status: 'LOW_STOCK' | 'OUT_OF_STOCK';
}

export interface InventoryAdjustRequest {
  store_id: number;
  product_id: string;
  quantity: number;
  reason: string;
}

export interface InventoryReceiveRequest {
  store_id: number;
  product_id: string;
  quantity: number;
  reason: string;
}

export interface InventoryTransferRequest {
  from_store_id: number;
  to_store_id: number;
  product_id: string;
  quantity: number;
  reason: string;
}
