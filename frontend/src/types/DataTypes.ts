/**
 * Data Types for Categories and Units
 */

export interface Category {
  id: number;
  name: string;
  description: string | null;
}

export interface Unit {
  id: number;
  name: string;
  abbreviation: string | null;
}

export interface CategoryCreate {
  name: string;
  description?: string | null;
}

export interface UnitCreate {
  name: string;
  abbreviation?: string | null;
}

export interface CategoriesPage {
  items: Category[];
  page: number;
  page_size: number;
  total: number;
}

export interface UnitsPage {
  items: Unit[];
  page: number;
  page_size: number;
  total: number;
}
