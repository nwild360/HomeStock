const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export interface ReceiptScanConfig {
  enabled: boolean;
}

export interface ReceiptScanSettings {
  enabled: boolean;
  provider?: 'claude' | 'ollama' | null;
  api_key?: string | null;
  model?: string | null;
  endpoint_url?: string | null;
}

export interface CandidateItem {
  item_name: string;
  item_type: 'food' | 'household';
  category_name?: string | null;
  quantity: number;
  unit_name?: string | null;
  notes?: string | null;
}

export class ReceiptScanError extends Error {
  statusCode?: number;
  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'ReceiptScanError';
    this.statusCode = statusCode;
  }
}

export async function getReceiptScanConfig(): Promise<ReceiptScanConfig> {
  const response = await fetch(`${API_BASE_URL}/api/receipt/config`, {
    credentials: 'include',
  });
  if (!response.ok) throw new ReceiptScanError('Failed to fetch receipt scan config', response.status);
  return response.json();
}

export async function getReceiptScanSettings(): Promise<ReceiptScanSettings> {
  const response = await fetch(`${API_BASE_URL}/api/receipt/settings`, {
    credentials: 'include',
  });
  if (!response.ok) throw new ReceiptScanError('Failed to fetch receipt scan settings', response.status);
  return response.json();
}

export async function saveReceiptScanSettings(settings: ReceiptScanSettings): Promise<ReceiptScanSettings> {
  const response = await fetch(`${API_BASE_URL}/api/receipt/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(settings),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ReceiptScanError(data.detail ?? 'Failed to save receipt scan settings', response.status);
  }
  return response.json();
}

export async function scanReceipt(imageFile: File): Promise<CandidateItem[]> {
  const formData = new FormData();
  formData.append('image', imageFile);
  const response = await fetch(`${API_BASE_URL}/api/receipt/scan`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
    // No Content-Type header — browser sets multipart boundary automatically
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ReceiptScanError(data.detail ?? 'Receipt scan failed', response.status);
  }
  const data = await response.json();
  return data.items as CandidateItem[];
}
