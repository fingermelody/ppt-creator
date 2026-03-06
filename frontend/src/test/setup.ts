import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock TDesign MessagePlugin
vi.mock('tdesign-react', async () => {
  const actual = await vi.importActual('tdesign-react');
  return {
    ...actual,
    MessagePlugin: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
    },
  };
});

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// Reset all mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
});
