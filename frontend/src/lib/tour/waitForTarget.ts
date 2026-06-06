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
