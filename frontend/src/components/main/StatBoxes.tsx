import { STAT_BOX_CONFIGS, type InventoryType, type StatusFilter } from '../../types/InventoryTypes.ts';

interface StatBoxesProps {
  totalItems: number;
  expiringItems: number;
  expiredItems: number;
  screenType: InventoryType;
  activeFilter: StatusFilter;
  onFilterSelect: (filter: StatusFilter) => void;
}

const cardBase =
  'rounded-lg p-2 md:p-6 shadow-sm border bg-white dark:bg-gray-800 text-left transition cursor-pointer hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500';
const cardActive = 'border-blue-500 ring-2 ring-blue-500';
const cardInactive = 'border-gray-200 dark:border-gray-700';

function StatBoxes({
  totalItems,
  expiringItems,
  expiredItems,
  screenType,
  activeFilter,
  onFilterSelect,
}: StatBoxesProps) {
  const config = STAT_BOX_CONFIGS[screenType];

  const cardClass = (filter: StatusFilter) =>
    `${cardBase} ${activeFilter === filter ? cardActive : cardInactive}`;

  return (
    <div className="grid grid-cols-3 gap-2 mb-4 md:gap-6 md:mb-8">
      <button
        type="button"
        onClick={() => onFilterSelect('all')}
        aria-pressed={activeFilter === 'all'}
        className={cardClass('all')}
      >
        <div className="text-center">
          <div className="text-2xl md:text-4xl font-bold text-gray-900 dark:text-gray-100">{totalItems}</div>
          <div className="text-xs md:text-sm text-gray-600 dark:text-gray-400 mt-0.5 md:mt-1 capitalize">Total {screenType}</div>
        </div>
      </button>

      <button
        type="button"
        onClick={() => onFilterSelect('expiring')}
        aria-pressed={activeFilter === 'expiring'}
        className={cardClass('expiring')}
      >
        <div className="text-center">
          <div className={`text-2xl md:text-4xl font-bold ${expiringItems > 0 ? 'text-amber-500' : 'text-gray-900 dark:text-gray-100'}`}>{expiringItems}</div>
          <div className="text-xs md:text-sm text-gray-600 dark:text-gray-400 mt-0.5 md:mt-1">{config.middleLabel}</div>
        </div>
      </button>

      <button
        type="button"
        onClick={() => onFilterSelect('expired')}
        aria-pressed={activeFilter === 'expired'}
        className={cardClass('expired')}
      >
        <div className="text-center">
          <div className={`text-2xl md:text-4xl font-bold ${expiredItems > 0 ? 'text-red-500' : 'text-gray-900 dark:text-gray-100'}`}>{expiredItems}</div>
          <div className="text-xs md:text-sm text-gray-600 dark:text-gray-400 mt-0.5 md:mt-1">{config.lastLabel}</div>
        </div>
      </button>
    </div>
  );
}

export default StatBoxes;
