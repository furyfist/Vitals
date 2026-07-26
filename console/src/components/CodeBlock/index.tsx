import type React from "react";
import CopyButton from "../CopyButton";
import styles from "./CodeBlock.module.css";

export interface CodeBlockProps {
  code: string;
  withCopy?: boolean;
  className?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  withCopy = false,
  className = "",
}) => {
  return (
    <div className={`${styles.container} ${className}`}>
      {withCopy && (
        <div className={styles.copyWrapper}>
          <CopyButton value={code} variant="icon" size="sm" />
        </div>
      )}
      <code>{code}</code>
    </div>
  );
};

export default CodeBlock;
