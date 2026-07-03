const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export interface McpConfig {
  enabled: boolean;
}

export interface McpSettings {
  enabled: boolean;
  allow_api_keys: boolean;
  server_url?: string | null;
  required_scope?: string | null;
}

export class McpError extends Error {
  statusCode?: number;
  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'McpError';
    this.statusCode = statusCode;
  }
}

export async function getMcpConfig(): Promise<McpConfig> {
  const response = await fetch(`${API_BASE_URL}/api/mcp/config`, {
    credentials: 'include',
  });
  if (!response.ok) throw new McpError('Failed to fetch MCP config', response.status);
  return response.json();
}

export async function getMcpSettings(): Promise<McpSettings> {
  const response = await fetch(`${API_BASE_URL}/api/mcp/settings`, {
    credentials: 'include',
  });
  if (!response.ok) throw new McpError('Failed to fetch MCP settings', response.status);
  return response.json();
}

export async function saveMcpSettings(settings: McpSettings): Promise<McpSettings> {
  const response = await fetch(`${API_BASE_URL}/api/mcp/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(settings),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new McpError(data.detail ?? 'Failed to save MCP settings', response.status);
  }
  return response.json();
}
