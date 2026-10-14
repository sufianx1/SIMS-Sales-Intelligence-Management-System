export interface OrderLine {
  order_detail_id?: number;
  order_id?: string;
  product_id: string;
  product_name?: string | null;
  category?: string | null;
  sub_category?: string | null;
  sales: number;
  quantity: number;
  discount: number;
  profit: number;
}

export interface OrderSummary {
  order_id: string;
  order_date: string;
  ship_date?: string | null;
  ship_mode?: string | null;
  customer_id: string;
  customer_name: string;
  company_id: number;
  store_id?: number | null;
  store_name?: string | null;
  country?: string | null;
  city?: string | null;
  state?: string | null;
  region?: string | null;
  total_sales: number;
  total_quantity: number;
  total_profit: number;
  line_count: number;
}

export interface OrderDetail {
  order: OrderSummary;
  lines: OrderLine[];
}

export interface OrderCreate {
  order_id: string;
  order_date: string;
  ship_date?: string;
  ship_mode?: string;
  customer_id: string;
  store_id?: number | null;
  country?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  region?: string;
  lines: {
    product_id: string;
    quantity: number;
    sales: number;
    discount: number;
    profit: number;
  }[];
}
