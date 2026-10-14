export interface Company {
  company_id: number;
  company_name: string;
  is_active: boolean;
  created_at?: string;
}

export interface Store {
  store_id: number;
  company_id: number;
  store_name: string;
  location?: string | null;
  city?: string | null;
  state?: string | null;
  is_active: boolean;
  created_at?: string;
}
