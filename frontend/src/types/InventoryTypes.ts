import FoodIcon from '../assets/FoodIcon.svg';
import HouseholdIcon from '../assets/HouseHoldIcon.svg';
import DataManagementIcon from '../assets/DataManagement.svg';
import PeopleIcon from '../assets/People.svg';

export type InventoryType = 'food' | 'household'; // Could add equipment/tools later
export type ScreenType = InventoryType | 'data' | 'users';

export interface MenuItem {
  id: ScreenType;
  label: string;
  icon: string;
  separator?: boolean; // Add separator line above this item
}

export interface StatBoxConfig {
  middleLabel: string;
  lastLabel: string;
}

// Inventory type items only (for AddItemOverlay dropdown)
export const INVENTORY_ITEMS: MenuItem[] = [
  { id: 'food', label: 'Food', icon: FoodIcon},
  { id: 'household', label: 'Household', icon: HouseholdIcon},
];

// All menu items including navigation items (for sidebar)
export const MENU_ITEMS: MenuItem[] = [
  ...INVENTORY_ITEMS,
  { id: 'data', label: 'Data', icon: DataManagementIcon, separator: true },
  { id: 'users', label: 'Users', icon: PeopleIcon },
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