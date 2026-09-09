export default function CostDefaults({
  slippagePct,
  brokeragePerOrder,
  onSlippageChange,
  onBrokerageChange,
  onPersist,
  disabled = false,
}) {
  return (
    <div className="cost-defaults">
      <div className="cost-defaults-title">Default costs</div>
      <label>
        Brokerage ₹ / order
        <input
          type="number"
          min={0}
          step={0.01}
          value={brokeragePerOrder}
          onChange={(e) => onBrokerageChange(e.target.value)}
          onBlur={onPersist}
          disabled={disabled}
        />
      </label>
      <label>
        Slippage %
        <input
          type="number"
          min={0}
          max={100}
          step={0.1}
          value={slippagePct}
          onChange={(e) => onSlippageChange(e.target.value)}
          onBlur={onPersist}
          disabled={disabled}
        />
      </label>
      <p className="cost-defaults-hint">
        Slippage worsens fills: buy entry +% / exit −%; sell entry −% / exit +%. Needs
        entry/exit price, side, and qty (else skipped). Charges use 1.18 × 2 × brokerage
        plus side-aware transaction rates. Saved on blur; used on every upload / path load.
      </p>
    </div>
  );
}
