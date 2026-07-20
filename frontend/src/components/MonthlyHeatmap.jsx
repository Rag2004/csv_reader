import { MONTHS, cellClass, fmtNumber } from '../utils/format';

export default function MonthlyHeatmap({ years, grandTotal }) {
  if (!years?.length) {
    return <p style={{ color: 'var(--text-muted)' }}>No monthly data.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="heatmap-table">
        <thead>
          <tr>
            <th className="year-col">Year</th>
            {MONTHS.map((m) => (
              <th key={m}>{m}</th>
            ))}
            <th>Net</th>
          </tr>
        </thead>
        <tbody>
          {years.map((row) => (
            <tr key={row.year}>
              <td className="year-col">{row.year}</td>
              {row.months.map((cell) => (
                <td key={cell.month} className={cellClass(cell.pnl)}>
                  {cell.pnl === null || cell.pnl === undefined
                    ? '0'
                    : fmtNumber(cell.pnl, 0)}
                </td>
              ))}
              <td className={cellClass(row.net)}>{fmtNumber(row.net, 0)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td className="year-col">Total</td>
            <td colSpan={12} />
            <td className={cellClass(grandTotal)}>{fmtNumber(grandTotal, 0)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
