import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useState,
} from 'react';

interface HeaderSlotContextType {
  headerSlot: ReactNode;
  setHeaderSlot: (node: ReactNode) => void;
}

const HeaderSlotContext = createContext<HeaderSlotContextType | null>(null);

export function HeaderSlotProvider({ children }: { children: ReactNode }) {
  const [headerSlot, setHeaderSlotState] = useState<ReactNode>(null);

  const setHeaderSlot = useCallback((node: ReactNode) => {
    setHeaderSlotState(node);
  }, []);

  return (
    <HeaderSlotContext.Provider value={{ headerSlot, setHeaderSlot }}>
      {children}
    </HeaderSlotContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- hook colocated with its provider
export function useHeaderSlot() {
  const ctx = useContext(HeaderSlotContext);
  if (!ctx)
    throw new Error('useHeaderSlot must be used within HeaderSlotProvider');
  return ctx;
}
