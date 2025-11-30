/**
 * Item Types
 *
 * TypeScript types matching the backend API schemas for inventory items.
 */

export type ItemType = 'food' | 'household' | 'equipment';

export interface Item {
  item_id: number;
  item_name: string;
  item_type: ItemType;
  category_name: string | null;
  quantity: number;
  unit_name: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  mealie_food_id: string | null;
}

export interface ItemsPage {
  items: Item[];
  page: number;
  page_size: number;
  total: number;
}

export interface ItemCreate {
  item_name: string;
  item_type: ItemType;
  category_name?: string | null;
  quantity: number;
  unit_name?: string | null;
  notes?: string | null;
  mealie_food_id?: string | null;
}

export interface ItemPatch {
  name?: string;
  category_name?: string;
  quantity?: number;
  notes?: string;
}

export interface StockPatch {
  delta?: number;
  new_qty?: number;
}
