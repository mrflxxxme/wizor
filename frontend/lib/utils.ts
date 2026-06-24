import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// shadcn/ui-совместимый хелпер слияния классов (используется компонентами с P7).
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
