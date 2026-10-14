export interface Product {
  product_id: string;
  product_name: string;
  category?: string | null;
  sub_category?: string | null;
  company_id: number;
  total_sales: number;
  total_quantity: number;
  total_profit: number;
}

export interface ProductOrderLine {
  order_id: string;
  order_date: string;
  customer_name: string;
  sales: number;
  quantity: number;
  discount: number;
  profit: number;
}

export interface ProductDetail {
  product: Product;
  recent_transactions: ProductOrderLine[];
}
