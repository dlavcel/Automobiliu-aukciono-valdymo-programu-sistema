export default function DetailItem({ label, value }) {
  return (
    <div className="adminDetailItem">
      <span className="adminDetailLabel">{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}
