import { css } from "lit";

/** Form field styles shared by the Add job dialog and its tabs. */
export const fieldStyles = css`
  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin: 12px 0;
  }
  .label {
    font-size: 13px;
    color: var(--secondary-text-color);
  }
  input,
  select,
  textarea {
    font: inherit;
    padding: 8px;
    color: var(--primary-text-color);
    background: var(--secondary-background-color, transparent);
    border: 1px solid var(--divider-color);
    border-radius: 4px;
  }
  textarea {
    font-family: monospace;
  }
  .inline-error {
    color: var(--error-color, #db4437);
    font-size: 13px;
  }
`;
