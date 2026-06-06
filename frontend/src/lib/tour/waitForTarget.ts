export function queryHTMLElement(selector: string): HTMLElement | null {
  const element = document.querySelector(selector);
  return element instanceof HTMLElement ? element : null;
}

export function queryFirstSelector(...selectors: string[]): Element | null {
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element) {
      return element;
    }
  }
  return null;
}

export function queryFirstHTMLElement(
  ...selectors: string[]
): HTMLElement | null {
  for (const selector of selectors) {
    const element = queryHTMLElement(selector);
    if (element) {
      return element;
    }
  }
  return null;
}

export async function waitForTarget(
  selector: string,
  {
    timeout = 5000,
    interval = 50,
  }: { timeout?: number; interval?: number } = {}
): Promise<Element> {
  const start = Date.now();

  while (Date.now() - start < timeout) {
    const element = document.querySelector(selector);
    if (element) {
      return element;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Tour target not found: ${selector}`);
}

export async function waitForAnyTarget(
  selectors: string[],
  {
    timeout = 5000,
    interval = 50,
  }: { timeout?: number; interval?: number } = {}
): Promise<Element> {
  const start = Date.now();

  while (Date.now() - start < timeout) {
    const element = queryFirstSelector(...selectors);
    if (element) {
      return element;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Tour target not found: ${selectors.join(', ')}`);
}
