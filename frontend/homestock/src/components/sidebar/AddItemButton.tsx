interface AddItemButtonProps {
  onClick?: () => void;
}

function AddItemButton({ onClick }: AddItemButtonProps) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center justify-center bg-slate-950 hover:bg-lime-400 text-white hover:text-slate-950 font-medium py-3 px-4 rounded-lg transition-colors relative"
    >
      <svg 
        className="w-5 h-5 stroke-current absolute left-4 text-lime-400" 
        viewBox="0 0 99 99" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <line x1="49" y1="5" x2="49" y2="94" strokeWidth="15" strokeLinecap="round"/>
        <line x1="94" y1="49" x2="5" y2="49" strokeWidth="15" strokeLinecap="round"/>
      </svg>
      <span className="relative z-10">Add Item</span>
    </button>
  );
}

export default AddItemButton;