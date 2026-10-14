export interface CompanyMembership {
  company_id: number;
  company_name: string;
  role_id: number;
  role_name: string;
  store_id: number | null;
  store_name: string | null;
  permissions: string[];
}

export interface UserProfile {
  user_id: number;
  name: string;
  email: string;
  is_system_admin: boolean;
  is_active: boolean;
  companies: CompanyMembership[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}
