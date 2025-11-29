import { useState, type FormEvent } from 'react';
import logo from '../../assets/HomeStock.svg';
import LoginFields from './LoginFields';

interface LoginScreenProps {
  onLogin: (username: string, password: string) => Promise<void>;
}

function LoginScreen({ onLogin }: LoginScreenProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [loginError, setLoginError] = useState('');
  const [touched, setTouched] = useState({ username: false, password: false });

  // Validation pattern: alphanumeric, underscore, and hyphen only
  const VALID_PATTERN = /^[a-zA-Z0-9_-]+$/;
  const ERROR_MESSAGE = 'Only letters, numbers, hyphens, and underscores allowed';

  const validateField = (value: string): boolean => {
    return value.length > 0 && VALID_PATTERN.test(value);
  };

  const handleUsernameChange = (value: string) => {
    setUsername(value);
    if (touched.username) {
      if (value.length === 0) {
        setUsernameError('Username is required');
      } else if (!VALID_PATTERN.test(value)) {
        setUsernameError(ERROR_MESSAGE);
      } else {
        setUsernameError('');
      }
    }
  };

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    if (touched.password) {
      if (value.length === 0) {
        setPasswordError('Password is required');
      } else if (!VALID_PATTERN.test(value)) {
        setPasswordError(ERROR_MESSAGE);
      } else {
        setPasswordError('');
      }
    }
  };

  const handleUsernameBlur = () => {
    setTouched(prev => ({ ...prev, username: true }));
    if (username.length === 0) {
      setUsernameError('Username is required');
    } else if (!VALID_PATTERN.test(username)) {
      setUsernameError(ERROR_MESSAGE);
    } else {
      setUsernameError('');
    }
  };

  const handlePasswordBlur = () => {
    setTouched(prev => ({ ...prev, password: true }));
    if (password.length === 0) {
      setPasswordError('Password is required');
    } else if (!VALID_PATTERN.test(password)) {
      setPasswordError(ERROR_MESSAGE);
    } else {
      setPasswordError('');
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Clear any previous login errors
    setLoginError('');

    // Validate before submitting
    const isUsernameValid = validateField(username);
    const isPasswordValid = validateField(password);

    if (!isUsernameValid) {
      setUsernameError(username.length === 0 ? 'Username is required' : ERROR_MESSAGE);
      setTouched(prev => ({ ...prev, username: true }));
    }

    if (!isPasswordValid) {
      setPasswordError(password.length === 0 ? 'Password is required' : ERROR_MESSAGE);
      setTouched(prev => ({ ...prev, password: true }));
    }

    if (!isUsernameValid || !isPasswordValid) {
      return;
    }

    setIsLoading(true);
    try {
      await onLogin(username, password);
    } catch (error) {
      // Display backend authentication error
      if (error instanceof Error) {
        setLoginError(error.message);
      } else {
        setLoginError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const isFormValid = validateField(username) && validateField(password);

  return (
    <div className="min-h-screen bg-gray-700 flex flex-col items-center justify-center p-4">
      {/* Logo and App Name */}
      <div className="flex flex-col items-center gap-4 mb-8">
        <img
          src={logo}
          alt="HomeStock Logo"
          className="w-20 h-20 md:w-24 md:h-24"
        />
        <h1 className="text-4xl md:text-5xl font-semibold text-[#A3E635]">
          HomeStock
        </h1>
      </div>

      {/* Login Form Box */}
      <div className="w-full max-w-md">
        <form
          onSubmit={handleSubmit}
          className="bg-gray-800 rounded-lg p-6 md:p-8 shadow-lg border border-gray-600"
        >
          <h2 className="text-2xl font-semibold text-white mb-6 text-center">
            Sign In
          </h2>

          {/* Username Field */}
          <LoginFields
            id="username"
            label="Username"
            type="text"
            value={username}
            onChange={handleUsernameChange}
            onBlur={handleUsernameBlur}
            error={usernameError}
            placeholder="Enter your username"
            autoComplete="username"
            disabled={isLoading}
          />

          {/* Password Field */}
          <LoginFields
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={handlePasswordChange}
            onBlur={handlePasswordBlur}
            error={passwordError}
            placeholder="Enter your password"
            autoComplete="current-password"
            disabled={isLoading}
          />

          {/* Login Error Message */}
          {loginError && (
            <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg">
              <p className="text-red-200 text-sm">{loginError}</p>
            </div>
          )}

          {/* Login Button */}
          <button
            type="submit"
            disabled={isLoading || !isFormValid}
            className="w-full px-4 py-3 bg-[#A3E635] text-gray-900 font-semibold rounded-lg hover:bg-[#8BC82E] focus:outline-none focus:ring-2 focus:ring-[#A3E635] focus:ring-offset-2 focus:ring-offset-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>

      {/* Footer Text */}
      <p className="mt-8 text-gray-400 text-sm text-center">
        HomeStock Inventory Management System
      </p>
    </div>
  );
}

export default LoginScreen;
