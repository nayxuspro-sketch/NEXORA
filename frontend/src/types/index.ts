export type UserRole = 'ADMIN' | 'MANAGER' | 'CASHIER' | 'STOCK_KEEPER' | 'ACCOUNTANT' | 'AUDITOR';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone?: string;
  company_id?: string;
  company_name?: string;
  is_active: boolean;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  currency: string;
  registration_number?: string;
  tax_identifier?: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
}

export interface Product {
  id: string;
  company?: string;
  name: string;
  sku: string;
  barcode: string;
  description: string;
  category?: string;
  category_name?: string;
  unit?: string;
  unit_symbol?: string;
  cost_price: string;
  selling_price: string;
  tax_rate: string;
  alert_threshold: string;
  is_active: boolean;
}

export interface Partner {
  id: string;
  name: string;
  partner_type: 'CUSTOMER' | 'SUPPLIER' | 'BOTH';
  email: string;
  phone: string;
  address: string;
  tax_number: string;
  credit_limit: string;
  current_balance: string;
  is_active: boolean;
}

export interface Store {
  id: string;
  name: string;
  code: string;
  address: string;
  phone: string;
  is_active: boolean;
}

export interface StockLevel {
  id: string;
  store: string;
  store_name: string;
  product: string;
  product_name: string;
  product_sku: string;
  quantity: string;
}

export interface StockMovement {
  id: string;
  store_name: string;
  product_name: string;
  product_sku: string;
  movement_type: string;
  quantity: string;
  quantity_before: string;
  quantity_after: string;
  reference: string;
  reason: string;
  user_email: string;
  created_at: string;
}

export interface SaleItem {
  id?: string;
  product: string;
  product_name?: string;
  product_sku?: string;
  quantity: number | string;
  unit_price: number | string;
  tax_rate?: number | string;
  discount_rate?: number | string;
  total?: number | string;
}

export interface Sale {
  id: string;
  reference: string;
  store: string;
  store_name?: string;
  customer?: string;
  customer_name?: string;
  seller_name?: string;
  status: 'DRAFT' | 'COMPLETED' | 'CANCELLED';
  payment_status: 'PENDING' | 'PARTIAL' | 'PAID' | 'REFUNDED';
  subtotal_amount: string;
  tax_amount: string;
  discount_amount: string;
  total_amount: string;
  paid_amount: string;
  notes?: string;
  items: SaleItem[];
  created_at: string;
}

export interface CashRegister {
  id: string;
  store: string;
  store_name: string;
  name: string;
  code: string;
  status: 'OPEN' | 'CLOSED';
  current_balance: string;
  cashier_name?: string;
}

export interface DashboardReport {
  weekly_chart?: Array<{ label: string; date: string; value: number }>;
  period_days: number;
  sales: {
    total_amount: string;
    count: number;
    tax_collected: string;
    discounts_granted: string;
  };
  purchases: {
    total_amount: string;
    count: number;
  };
  profitability: {
    gross_estimate: string;
  };
  inventory: {
    total_units_stocked: string;
    low_stock_alerts_count: number;
    low_stock_items: Array<{
      product_id: string;
      product_name: string;
      sku: string;
      store_name: string;
      current_stock: string;
      alert_threshold: string;
    }>;
  };
}

export interface PaginatedResponse<T> {
  status: string;
  pagination: {
    count: number;
    total_pages: number;
    current_page: number;
    page_size: number;
    next: string | null;
    previous: string | null;
  };
  results: T[];
}
