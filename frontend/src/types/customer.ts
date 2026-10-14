export interface Customer {
  customer_id: string;
  customer_name: string;
  segment?: string | null;
  company_id: number;
  total_orders: number;
  total_sales: number;
  total_profit: number;
}

export interface CustomerOrderLine {
  order_id: string;
  order_date: string;
  product_name: string;
  category?: string | null;
  sales: number;
  quantity: number;
  profit: number;
}

export interface CustomerDetail {
  customer: Customer;
  recent_orders: CustomerOrderLine[];
}
