import { type ChangeEvent } from 'react';

interface LoginFieldsProps {
  id: string;
  label: string;
  type: 'text' | 'password';
  value: string;
  onChange: (value: string) => void;
  onBlur: () => void;
  error?: string;
  placeholder: string;
  autoComplete: 'username' | 'current-password';
  disabled?: boolean;
}

function LoginFields({
  id,
  label,
  type,
  value,
  onChange,
  onBlur,
  error,
  placeholder,
  autoComplete,
  disabled = false,
}: LoginFieldsProps) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const handleBlur = () => {
    onBlur();
  };

  return (
    <div className="mb-4">
      <label
        htmlFor={id}
        className="block text-gray-300 text-sm font-medium mb-2"
      >
        {label}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={handleChange}
        onBlur={handleBlur}
        className={`w-full px-4 py-3 bg-gray-700 text-white rounded-lg border transition-all focus:outline-none focus:ring-2 ${
          error
            ? 'border-red-500 focus:ring-red-500'
            : 'border-gray-600 focus:ring-[#A3E635] focus:border-transparent'
        }`}
        placeholder={placeholder}
        required
        autoComplete={autoComplete}
        disabled={disabled}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
      />
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}

export default LoginFields;
