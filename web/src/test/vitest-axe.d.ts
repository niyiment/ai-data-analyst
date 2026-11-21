import "vitest";

declare module "vitest" {
  // Type parameters must match vitest's own declaration for the interfaces to merge.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
  interface Assertion<T = any> {
    toHaveNoViolations(): void;
  }
}
