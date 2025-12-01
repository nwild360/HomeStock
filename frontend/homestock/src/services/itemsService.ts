/**
 * Items Service
 *
 * Handles all item-related API calls with authentication.
 * All requests include httpOnly cookie authentication via credentials: 'include'.
 */

import type { Item, ItemsPage, ItemCreate, ItemPatch, StockPatch } from '../types/ItemTypes';
import { AuthError } from './AuthService'; 

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export class ItemsError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'ItemsError';
    this.statusCode = statusCode;
  }
}

/**
 * Fetch paginated items list.
 * Requires authentication.
 */
export async function getItems(
  page: number = 1,
  pageSize: number = 20
): Promise<ItemsPage> {
  const response = await fetch(
    `${API_BASE_URL}/api/items?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      credentials: 'include', // Send httpOnly cookie
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    throw new ItemsError(`Failed to fetch items: ${response.statusText}`, response.status);
  }

  const data: ItemsPage = await response.json();
  return data;
}

/**
 * Fetch a single item by ID.
 * Requires authentication.
 */
export async function getItem(id: number): Promise<Item> {
  const response = await fetch(`${API_BASE_URL}/api/items/${id}`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new ItemsError('Item not found', 404);
    }
    throw new ItemsError(`Failed to fetch item: ${response.statusText}`, response.status);
  }

  const data: Item = await response.json();
  return data;
}

/**
 * Create a new item.
 * Requires authentication.
 */
export async function createItem(item: ItemCreate): Promise<Item> {
  const response = await fetch(`${API_BASE_URL}/api/items`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(item),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    throw new ItemsError(`Failed to create item: ${response.statusText}`, response.status);
  }

  const data: Item = await response.json();
  return data;
}

/**
 * Update an item.
 * Requires authentication.
 */
export async function updateItem(
  id: number,
  updates: ItemPatch,
  ifUnmodifiedSince?: string
): Promise<Item> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (ifUnmodifiedSince) {
    headers['If-Unmodified-Since'] = ifUnmodifiedSince;
  }

  const response = await fetch(`${API_BASE_URL}/api/items/${id}`, {
    method: 'PATCH',
    headers,
    credentials: 'include',
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new ItemsError('Item not found', 404);
    }
    if (response.status === 412) {
      throw new ItemsError('Item was modified by another user', 412);
    }
    throw new ItemsError(`Failed to update item: ${response.statusText}`, response.status);
  }

  const data: Item = await response.json();
  return data;
}

/**
 * Update item stock quantity.
 * Requires authentication.
 */
export async function updateStock(
  id: number,
  stockUpdate: StockPatch,
  ifUnmodifiedSince?: string
): Promise<Item> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (ifUnmodifiedSince) {
    headers['If-Unmodified-Since'] = ifUnmodifiedSince;
  }

  const response = await fetch(`${API_BASE_URL}/api/items/${id}/stock`, {
    method: 'PATCH',
    headers,
    credentials: 'include',
    body: JSON.stringify(stockUpdate),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new ItemsError('Item not found', 404);
    }
    if (response.status === 412) {
      throw new ItemsError('Item was modified by another user', 412);
    }
    throw new ItemsError(`Failed to update stock: ${response.statusText}`, response.status);
  }

  const data: Item = await response.json();
  return data;
}

/**
 * Delete an item.
 * Requires authentication.
 */
export async function deleteItem(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/items/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new ItemsError('Item not found', 404);
    }
    throw new ItemsError(`Failed to delete item: ${response.statusText}`, response.status);
  }
}
