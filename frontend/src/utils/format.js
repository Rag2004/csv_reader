export function fmtNumber(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return Number(n).toLocaleString('en-IN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function fmtInt(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString('en-IN');
}

export function fmtPct(n, digits = 2) {
  if (n === null || n === undefined) return '—';
  return `${Number(n).toFixed(digits)}%`;
}

export function pnlClass(n) {
  if (n === null || n === undefined) return '';
  if (n > 0) return 'pos';
  if (n < 0) return 'neg';
  return '';
}

export function cellClass(pnl) {
  if (pnl === null || pnl === undefined) return 'cell-empty';
  if (pnl > 0) return 'cell-pos';
  if (pnl < 0) return 'cell-neg';
  return 'cell-empty';
}

const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

export function monthName(m) {
  return MONTHS[m - 1] || String(m);
}

export { MONTHS };
