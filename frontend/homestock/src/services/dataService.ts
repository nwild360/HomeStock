/**
 * Data Service
 *
 * Handles all category and unit-related API calls with authentication.
 * All requests include httpOnly cookie authentication via credentials: 'include'.
 */

import type {
  Category,
  Unit,
  CategoriesPage,
  UnitsPage,
  CategoryCreate,
  UnitCreate,
} from '../types/DataTypes';
import { AuthError } from './AuthService';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export class DataError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'DataError';
    this.statusCode = statusCode;
  }
}

// ========== Categories API ==========

/**
 * Fetch paginated categories list.
 * Requires authentication.
 */
export async function getCategories(
  page: number = 1,
  pageSize: number = 20
): Promise<CategoriesPage> {
  const response = await fetch(
    `${API_BASE_URL}/api/data/categories?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      credentials: 'include',
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    throw new DataError(`Failed to fetch categories: ${response.statusText}`, response.status);
  }

  const data: CategoriesPage = await response.json();
  return data;
}

/**
 * Fetch a single category by ID.
 * Requires authentication.
 */
export async function getCategory(id: number): Promise<Category> {
  const response = await fetch(`${API_BASE_URL}/api/data/categories/${id}`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new DataError('Category not found', 404);
    }
    throw new DataError(`Failed to fetch category: ${response.statusText}`, response.status);
  }

  const data: Category = await response.json();
  return data;
}

/**
 * Create a new category.
 * Requires authentication.
 */
export async function createCategory(category: CategoryCreate): Promise<Category> {
  const response = await fetch(`${API_BASE_URL}/api/data/categories`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(category),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 409) {
      throw new DataError('A category with this name already exists', 409);
    }
    throw new DataError(`Failed to create category: ${response.statusText}`, response.status);
  }

  const data: Category = await response.json();
  return data;
}

/**
 * Update a category.
 * Requires authentication.
 */
export async function updateCategory(id: number, category: CategoryCreate): Promise<Category> {
  const response = await fetch(`${API_BASE_URL}/api/data/categories/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(category),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new DataError('Category not found', 404);
    }
    if (response.status === 409) {
      throw new DataError('A category with this name already exists', 409);
    }
    throw new DataError(`Failed to update category: ${response.statusText}`, response.status);
  }

  const data: Category = await response.json();
  return data;
}

/**
 * Delete a category.
 * Requires authentication.
 */
export async function deleteCategory(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/data/categories/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new DataError('Category not found', 404);
    }
    throw new DataError(`Failed to delete category: ${response.statusText}`, response.status);
  }
}

// ========== Units API ==========

/**
 * Fetch paginated units list.
 * Requires authentication.
 */
export async function getUnits(
  page: number = 1,
  pageSize: number = 20
): Promise<UnitsPage> {
  const response = await fetch(
    `${API_BASE_URL}/api/data/units?page=${page}&page_size=${pageSize}`,
    {
      method: 'GET',
      credentials: 'include',
    }
  );

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    throw new DataError(`Failed to fetch units: ${response.statusText}`, response.status);
  }

  const data: UnitsPage = await response.json();
  return data;
}

/**
 * Fetch a single unit by ID.
 * Requires authentication.
 */
export async function getUnit(id: number): Promise<Unit> {
  const response = await fetch(`${API_BASE_URL}/api/data/units/${id}`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new DataError('Unit not found', 404);
    }
    throw new DataError(`Failed to fetch unit: ${response.statusText}`, response.status);
  }

  const data: Unit = await response.json();
  return data;
}

/**
 * Create a new unit.
 * Requires authentication.
 */
export async function createUnit(unit: UnitCreate): Promise<Unit> {
  const response = await fetch(`${API_BASE_URL}/api/data/units`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(unit),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 409) {
      throw new DataError('A unit with this name or abbreviation already exists', 409);
    }
    throw new DataError(`Failed to create unit: ${response.statusText}`, response.status);
  }

  const data: Unit = await response.json();
  return data;
}

/**
 * Update a unit.
 * Requires authentication.
 */
export async function updateUnit(id: number, unit: UnitCreate): Promise<Unit> {
  const response = await fetch(`${API_BASE_URL}/api/data/units/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(unit),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new DataError('Unit not found', 404);
    }
    if (response.status === 409) {
      throw new DataError('A unit with this name or abbreviation already exists', 409);
    }
    throw new DataError(`Failed to update unit: ${response.statusText}`, response.status);
  }

  const data: Unit = await response.json();
  return data;
}

/**
 * Delete a unit.
 * Requires authentication.
 */
export async function deleteUnit(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/data/units/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new AuthError('Not authenticated', 401);
    }
    if (response.status === 404) {
      throw new DataError('Unit not found', 404);
    }
    throw new DataError(`Failed to delete unit: ${response.statusText}`, response.status);
  }
}
