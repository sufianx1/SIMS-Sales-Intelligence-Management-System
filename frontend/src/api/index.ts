import apiClient from './client';
import {
  UserProfile,
  LoginRequest,
  TokenResponse,
  CompanyMembership,
} from '../types/auth';
import { Company, Store } from '../types/company';
import { Customer, CustomerDetail } from '../types/customer';
import { Product, ProductDetail } from '../types/product';
import { OrderSummary, OrderDetail, OrderCreate } from '../types/order';
import { PaginatedResponse } from '../types/api';

export const authApi = {
  login: async (creds: LoginRequest): Promise<TokenResponse> => {
    const res = await apiClient.post<TokenResponse>('/auth/login', creds);
    return res.data;
  },
  getMe: async (): Promise<UserProfile> => {
    const res = await apiClient.get<UserProfile>('/auth/me');
    return res.data;
  },
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },
};

export const companiesApi = {
  list: async (): Promise<Company[]> => {
    const res = await apiClient.get<Company[]>('/companies');
    return res.data;
  },
  getById: async (id: number): Promise<Company> => {
    const res = await apiClient.get<Company>(`/companies/${id}`);
    return res.data;
  },
  create: async (data: { company_name: string }): Promise<Company> => {
    const res = await apiClient.post<Company>('/companies', data);
    return res.data;
  },
};

export const storesApi = {
  list: async (): Promise<Store[]> => {
    const res = await apiClient.get<Store[]>('/stores');
    return res.data;
  },
  create: async (data: { store_name: string; location?: string }): Promise<Store> => {
    const res = await apiClient.post<Store>('/stores', data);
    return res.data;
  },
};

export const customersApi = {
  list: async (params?: {
    search?: string;
    segment?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Customer>> => {
    const res = await apiClient.get<PaginatedResponse<Customer>>('/customers', {
      params,
    });
    return res.data;
  },
  getById: async (id: string): Promise<CustomerDetail> => {
    const res = await apiClient.get<CustomerDetail>(`/customers/${id}`);
    return res.data;
  },
  create: async (data: {
    customer_id: string;
    customer_name: string;
    segment?: string;
  }): Promise<Customer> => {
    const res = await apiClient.post<Customer>('/customers', data);
    return res.data;
  },
};

export const productsApi = {
  list: async (params?: {
    search?: string;
    category?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<Product>> => {
    const res = await apiClient.get<PaginatedResponse<Product>>('/products', {
      params,
    });
    return res.data;
  },
  getById: async (id: string): Promise<ProductDetail> => {
    const res = await apiClient.get<ProductDetail>(`/products/${id}`);
    return res.data;
  },
  create: async (data: {
    product_id: string;
    product_name: string;
    category?: string;
    sub_category?: string;
  }): Promise<Product> => {
    const res = await apiClient.post<Product>('/products', data);
    return res.data;
  },
};

export const ordersApi = {
  list: async (params?: {
    region?: string;
    ship_mode?: string;
    customer_id?: string;
    store_id?: number;
    start_date?: string;
    end_date?: string;
    search?: string;
    page?: number;
    limit?: number;
  }): Promise<PaginatedResponse<OrderSummary>> => {
    const res = await apiClient.get<PaginatedResponse<OrderSummary>>('/orders', {
      params,
    });
    return res.data;
  },
  getById: async (id: string): Promise<OrderDetail> => {
    const res = await apiClient.get<OrderDetail>(`/orders/${id}`);
    return res.data;
  },
  create: async (data: OrderCreate): Promise<OrderDetail> => {
    const res = await apiClient.post<OrderDetail>('/orders', data);
    return res.data;
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/orders/${id}`);
  },
};

export const dashboardApi = {
  getMetrics: async () => {
    const res = await apiClient.get<{
      total_sales: number;
      total_profit: number;
      total_orders: number;
      average_order_value?: number;
      total_customers: number;
      total_products: number;
    }>('/dashboard/metrics');
    return res.data;
  },
  getCharts: async () => {
    const res = await apiClient.get<{
      sales_by_category: { category: string; total_sales: number; total_profit: number }[];
      profit_by_category: { category: string; total_sales: number; total_profit: number }[];
      sales_by_region: { region: string; total_sales: number; total_profit: number }[];
      top_products: { product_name: string; total_sales: number }[];
      top_customers: { customer_name: string; total_sales: number }[];
    }>('/dashboard/charts');
    return res.data;
  },
};

export interface BusinessInsight {
  insight_id: string;
  category: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  title: string;
  summary: string;
  explanation: string;
  supporting_data: Record<string, any>;
  limitations: string;
  recommended_action: string;
}

export const analyticsApi = {
  getTrends: async (params?: { start_date?: string; end_date?: string }) => {
    const res = await apiClient.get<{ month: string; sales: number; profit: number }[]>('/analytics/trends', { params });
    return res.data;
  },
  getInsights: async (params?: { store_id?: number }) => {
    const res = await apiClient.get<BusinessInsight[]>('/analytics/insights', { params });
    return res.data;
  },
};

export const inventoryApi = {
  list: async (params?: { store_id?: number; category?: string; low_stock_only?: boolean; search?: string }) => {
    const res = await apiClient.get<import('../types/inventory').InventoryItem[]>('/inventory', { params });
    return res.data;
  },
  listMovements: async (params?: { store_id?: number; product_id?: string; limit?: number }) => {
    const res = await apiClient.get<import('../types/inventory').InventoryMovement[]>('/inventory/movements', { params });
    return res.data;
  },
  getAlerts: async (params?: { store_id?: number }) => {
    const res = await apiClient.get<import('../types/inventory').InventoryAlert[]>('/inventory/alerts', { params });
    return res.data;
  },
  adjust: async (data: import('../types/inventory').InventoryAdjustRequest) => {
    const res = await apiClient.post<import('../types/inventory').InventoryItem>('/inventory/adjust', data);
    return res.data;
  },
  receive: async (data: import('../types/inventory').InventoryReceiveRequest) => {
    const res = await apiClient.post<import('../types/inventory').InventoryItem>('/inventory/receive', data);
    return res.data;
  },
  transfer: async (data: import('../types/inventory').InventoryTransferRequest) => {
    const res = await apiClient.post<import('../types/inventory').InventoryMovement>('/inventory/transfer', data);
    return res.data;
  },
  getRebalanceRecommendations: async (params?: { store_id?: number }) => {
    const res = await apiClient.get<import('../types/inventory').RebalanceRecommendation[]>('/inventory/rebalance-recommendations', {
      params,
    });
    return res.data;
  },
  exportCsvUrl: (storeId?: number) => {
    const base = '/api/v1/inventory/export';
    return storeId ? `${base}?store_id=${storeId}` : base;
  },
};

export const integrationsApi = {
  list: async () => {
    const res = await apiClient.get<import('../types/integrations').Integration[]>('/integrations');
    return res.data;
  },
  toggle: async (integrationId: string, isActive: boolean) => {
    const res = await apiClient.patch<import('../types/integrations').Integration>(`/integrations/${integrationId}/toggle?is_active=${isActive}`);
    return res.data;
  },
  triggerSync: async (integrationId: string) => {
    const res = await apiClient.post<import('../types/integrations').SyncExecutionResult>(`/integrations/${integrationId}/sync`);
    return res.data;
  },
  getLogs: async (integrationId: string) => {
    const res = await apiClient.get<import('../types/integrations').SyncLogItem[]>(`/integrations/${integrationId}/logs`);
    return res.data;
  },
};

export const importsApi = {
  preview: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<import('../types/imports').CsvPreview>('/imports/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  structuredImport: async (file: File, targetEntity: string, columnMappings: Record<string, string>, storeId?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_entity', targetEntity);
    formData.append('column_mapping_json', JSON.stringify(columnMappings));
    formData.append('column_mappings', JSON.stringify(columnMappings));
    if (storeId) {
      formData.append('store_id', storeId.toString());
    }
    const res = await apiClient.post<import('../types/imports').StructuredImportResult>('/imports/structured', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  rawImport: async (file: File, storeId?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (storeId) {
      formData.append('store_id', storeId.toString());
    }
    const res = await apiClient.post<import('../types/imports').RawDatasetItem>('/imports/raw', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  listRawDatasets: async (params?: { store_id?: number }) => {
    const res = await apiClient.get<import('../types/imports').RawDatasetItem[]>('/imports/raw', { params });
    return res.data;
  },
  getRawDatasetDetail: async (datasetId: string, params?: { query?: string; page?: number; limit?: number }) => {
    const res = await apiClient.get<{
      dataset_id: string;
      filename: string;
      row_count: number;
      column_names: string[];
      rows: Record<string, any>[];
      total_rows: number;
      page: number;
      limit: number;
    }>(`/imports/raw/${datasetId}`, { params });
    return res.data;
  },
  getHistory: async () => {
    const res = await apiClient.get<import('../types/imports').ImportHistory[]>('/imports/history');
    return res.data;
  },
  validate: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<{
      is_valid: boolean;
      total_rows: number;
      valid_rows: number;
      columns_detected: string[];
      missing_columns: string[];
      sample_preview: Record<string, any>[];
      validation_errors: string[];
    }>('/imports/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  execute: async (file: File, storeId?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (storeId) {
      formData.append('store_id', storeId.toString());
    }
    const res = await apiClient.post<{
      success: boolean;
      total_processed: number;
      customers_upserted: number;
      products_upserted: number;
      orders_upserted: number;
      order_details_inserted: number;
      message: string;
      duration_seconds: number;
    }>('/imports/execute', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};

