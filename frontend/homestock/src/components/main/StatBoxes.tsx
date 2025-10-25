import { STAT_BOX_CONFIGS, type InventoryType } from '../../types/InventoryTypes.ts';

interface StatBoxesProps {
  totalItems: number;
  expiringItems: number;
  expiredItems: number;
  screenType: InventoryType;
}
function StatBoxes({ totalItems, expiringItems, expiredItems, screenType }: StatBoxesProps) {
    const config = STAT_BOX_CONFIGS[screenType];

      return (
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-center mb-3">
            {/* Card Icon */}
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900">{totalItems}</div>
            <div className="text-sm text-gray-600 mt-1">Total {screenType}</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-center mb-3">
            {/* Card Icon */}
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900">{expiringItems}</div>
            <div className="text-sm text-gray-600 mt-1">{config.middleLabel}</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-center mb-3">
            {/* Card Icon */}
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900">{expiredItems}</div>
            <div className="text-sm text-gray-600 mt-1">{config.lastLabel}</div>
          </div>
        </div>
      </div>
      );
}

export default StatBoxes