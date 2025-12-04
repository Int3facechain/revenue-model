import type {ReactNode} from "react";

interface SettingFieldProps {
  label?: string;
  children: ReactNode;
}

export default function SettingField({label, children}: SettingFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      {label ? (
        <label className="text-xs text-gray-400 uppercase tracking-wide">
          {label}
        </label>
      ) : (
        <label className="text-xs opacity-0 select-none">.</label>
      )}

      {children}
    </div>
  );
}
