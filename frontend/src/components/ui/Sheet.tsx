import { ArrowLeft, X } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "./Button";

type SheetProps = {
  title: string;
  eyebrow: string;
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
};

export function Sheet({ title, eyebrow, isOpen, onClose, children, className = "" }: SheetProps) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="drawer-backdrop">
      <aside className={`app-sheet ${className}`} role="dialog" aria-label={title} aria-modal="true">
        <div className="drawer-header">
          <div>
            <p>{eyebrow}</p>
            <h2>{title}</h2>
          </div>
          <div className="sheet-header-actions">
            <Button variant="ghost" onClick={onClose}>
              <ArrowLeft data-icon="inline-start" aria-hidden="true" />
              Back
            </Button>
            <Button variant="icon" onClick={onClose} aria-label={`Close ${title}`}>
              <X aria-hidden="true" />
            </Button>
          </div>
        </div>
        {children}
      </aside>
    </div>
  );
}
