// Plus Icon Component
export const PlusIcon = () => (
  <svg 
    width="16" 
    height="16" 
    viewBox="0 0 24 24" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <path 
      d="M12 5V19M5 12H19" 
      stroke="currentColor" 
      strokeWidth="3" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    />
  </svg>
);

// Minus Icon Component
export const MinusIcon = () => (
  <svg 
    width="16" 
    height="16" 
    viewBox="0 0 24 24" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <path 
      d="M5 12H19" 
      stroke="currentColor" 
      strokeWidth="3" 
      strokeLinecap="round" 
      strokeLinejoin="round"
    />
  </svg>
);

interface CircleButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  ariaLabel?: string;
}

function CircleButton({ onClick, children, ariaLabel }: CircleButtonProps) {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel}
      className="w-6 h-6 flex items-center justify-center rounded-full border-3 border-gray-900 text-gray-900 hover:border-gray-600 hover:text-gray-600 active:border-lime-600 active:text-lime-600 transition-colors"
    >
      {children}
    </button>
  );
}

export default CircleButton;