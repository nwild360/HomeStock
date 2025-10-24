export type InventoryType = 'food' | 'household';

export interface MenuItem {
  id: InventoryType;
  label: string;
  icon?: string; // For future icon support
}

export const MENU_ITEMS: MenuItem[] = [
  { id: 'food', label: 'Food' },
  { id: 'household', label: 'Household' },
];