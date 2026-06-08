import '@testing-library/jest-dom/vitest';

const localStorageItems = new Map<string, string>();
const testLocalStorage = {
  get length() {
    return localStorageItems.size;
  },
  clear() {
    localStorageItems.clear();
  },
  getItem(key: string) {
    return localStorageItems.get(key) ?? null;
  },
  key(index: number) {
    return Array.from(localStorageItems.keys())[index] ?? null;
  },
  removeItem(key: string) {
    localStorageItems.delete(key);
  },
  setItem(key: string, value: string) {
    localStorageItems.set(key, String(value));
  },
} as Storage;

Object.defineProperty(window, 'localStorage', {
  value: testLocalStorage,
  configurable: true,
});

Object.defineProperty(globalThis, 'localStorage', {
  value: testLocalStorage,
  configurable: true,
});
