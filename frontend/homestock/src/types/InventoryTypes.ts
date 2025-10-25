import FoodIcon from '../assets/FoodIcon.svg';
import HouseholdIcon from '../assets/HouseHoldIcon.svg';

export type InventoryType = 'food' | 'household'; // Could add equipment/tools later

export interface MenuItem {
  id: InventoryType;
  label: string;
  icon: string; 
}

export interface StatBoxConfig {
  middleLabel: string;
  lastLabel: string;
}

export const MENU_ITEMS: MenuItem[] = [
  { id: 'food', label: 'Food', icon: FoodIcon},
  { id: 'household', label: 'Household', icon: HouseholdIcon},
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