import { formatMoney } from "../formatters";

export default function BidForm({
  title,
  description,
  amount,
  onAmountChange,
  onSubmit,
  loading,
  error,
  success,
  disabled,
  min,
  placeholder,
  submitLabel,
  loadingLabel,
  showMinimum = false,
}) {
  return (
    <div className="section">
      <h3 className="section-title">{title}</h3>

      {description && <p className="description">{description}</p>}

      <form onSubmit={onSubmit} className="bid-form">
        <label className="bid-label">
          Jūsų pasiūlymas
          <input
            type="number"
            min={min}
            step="1"
            value={amount}
            onChange={(event) => {
              const value = event.target.value;
              if (value === "" || /^[0-9]+$/.test(value)) onAmountChange(value);
            }}
            placeholder={placeholder}
            disabled={disabled || loading}
            className="bid-input"
          />
        </label>

        <button
          type="submit"
          disabled={disabled || loading}
          className="bid-button"
          style={{ opacity: disabled || loading ? 0.55 : 1 }}
        >
          {loading ? loadingLabel : submitLabel}
        </button>
      </form>

      {showMinimum && (
        <div className="minimum-text">
          Minimalus pasiūlymas: <strong>{formatMoney(min)}</strong>
        </div>
      )}

      {error && <div className="error-text">{error}</div>}
      {success && <div className="success-text">{success}</div>}
    </div>
  );
}
