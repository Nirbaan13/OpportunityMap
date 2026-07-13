import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

const fieldClass =
  "mt-1.5 w-full rounded-md border border-line bg-paper px-3 py-2.5 text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20";

type FieldProps = {
  label: string;
  error?: string;
} & InputHTMLAttributes<HTMLInputElement>;

export function TextField({ label, error, id, ...props }: FieldProps) {
  const fieldId = id ?? props.name;
  return (
    <label className="block text-sm font-medium text-ink" htmlFor={fieldId}>
      {label}
      <input id={fieldId} className={fieldClass} {...props} />
      {error ? <span className="mt-1 block text-sm text-danger">{error}</span> : null}
    </label>
  );
}

type AreaProps = {
  label: string;
  hint?: string;
} & TextareaHTMLAttributes<HTMLTextAreaElement>;

export function TextArea({ label, hint, id, ...props }: AreaProps) {
  const fieldId = id ?? props.name;
  return (
    <label className="block text-sm font-medium text-ink" htmlFor={fieldId}>
      {label}
      {hint ? <span className="mt-0.5 block text-xs font-normal text-ink-soft">{hint}</span> : null}
      <textarea id={fieldId} className={`${fieldClass} min-h-[96px] resize-y`} {...props} />
    </label>
  );
}

type SelectProps = {
  label: string;
  children: ReactNode;
} & SelectHTMLAttributes<HTMLSelectElement>;

export function SelectField({ label, id, children, ...props }: SelectProps) {
  const fieldId = id ?? props.name;
  return (
    <label className="block text-sm font-medium text-ink" htmlFor={fieldId}>
      {label}
      <select id={fieldId} className={fieldClass} {...props}>
        {children}
      </select>
    </label>
  );
}
