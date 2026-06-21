import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "icon";
  fullWidth?: boolean;
  children: ReactNode;
};

export function Button({
  variant = "secondary",
  fullWidth = false,
  className = "",
  children,
  ...props
}: ButtonProps) {
  const classes = ["ui-button", `ui-button-${variant}`, fullWidth ? "full-width" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} type="button" {...props}>
      {children}
    </button>
  );
}
