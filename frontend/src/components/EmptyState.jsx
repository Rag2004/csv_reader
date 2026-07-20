import { Link } from 'react-router-dom';

export default function EmptyState({ message }) {
  return (
    <div className="empty-state">
      <p>{message || 'No CSV loaded yet.'}</p>
      <p>
        <Link to="/upload">Go to Upload</Link> to load a trades file.
      </p>
    </div>
  );
}
