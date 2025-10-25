export type InventoryType = 'food' | 'household'; // Could add equipment/tools later

export interface MenuItem {
  id: InventoryType;
  label: string;
  icon?: string; // For future icon support
}

export interface StatBoxConfig {
  middleLabel: string;
  lastLabel: string;
}

export const MENU_ITEMS: MenuItem[] = [
  { id: 'food', label: 'Food' },
  { id: 'household', label: 'Household' },
];

export const STAT_BOX_CONFIGS: Record<InventoryType, StatBoxConfig> = {
  food: {
    middleLabel: 'Expiring Soon',
    lastLabel: 'Expired',
  },
  household: {
    middleLabel: '6+ Months Old',
    lastLabel: '1+ Year Old',
  },
};