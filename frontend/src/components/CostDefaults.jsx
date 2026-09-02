export default function CostDefaults({
  slippagePct,
  chargePerTrade,
  onSlippageChange,
  onChargeChange,
  onPersist,
  disabled = false,
}) {
  return (
    <div className="cost-defaults">
      <div className="cost-defaults-title">Default costs</div>
      <label>
        Charge ₹ / trade
        <input
          type="number"
          min={0}
          step={0.01}
          value={chargePerTrade}
          onChange={(e) => onChargeChange(e.target.value)}
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
        Saved on blur. Used on every upload / path load until you change them.
      </p>
    </div>
  );
}
