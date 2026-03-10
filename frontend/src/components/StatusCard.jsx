import './StatusCard.css'

export default function StatusCard({ icon, title, status, color }) {
  return (
    <div className="status-card">
      <div className="card-icon">{icon}</div>
      <div className="card-info">
        <div className="card-title">{title}</div>
        <div className="card-status" style={{ color: color }}>{status}</div>
      </div>
    </div>
  )
}
