interface AddDataButtonsProps {
  onAddCategory?: () => void;
  onAddUnit?: () => void;
}

const AddDataButtons: React.FC<AddDataButtonsProps> = ({
  onAddCategory,
  onAddUnit,
}) => {
  const buttons = [
    { label: 'Category', onClick: onAddCategory },
    { label: 'Unit', onClick: onAddUnit },
  ];

  return (
    <div className="mb-4 md:mb-6 flex gap-2 md:gap-4">
      {buttons.map((button) => (
        <button
          key={button.label}
          onClick={button.onClick}
          className="px-3 md:px-4 py-2 text-sm md:text-base bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          + Add {button.label}
        </button>
      ))}
    </div>
  );
};

export default AddDataButtons;
