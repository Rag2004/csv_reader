export default function KpiCard({ title, rows }) {
  return (
    <div className="kpi-card">
      <h3>{title}</h3>
      {rows.map(([label, value]) => (
        <div className="row" key={label}>
          <span>{label}</span>
          <span>{value}</span>
        </div>
      ))}
    </div>
  );
}
