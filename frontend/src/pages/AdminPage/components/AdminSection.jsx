import AdminListingCard from "./AdminListingCard";

export default function AdminSection({
  title,
  listings,
  emptyText,
  actionType,
  onDetails,
  onApprove,
  onReject,
  onAuction,
  actionLoading,
}) {
  return (
    <section className="adminSection">
      <h2 className="adminSectionTitle">{title}</h2>

      {listings.length === 0 ? (
        <p className="adminEmpty">{emptyText}</p>
      ) : (
        <div className="adminGrid">
          {listings.map((listing) => (
            <AdminListingCard
              key={listing.id}
              listing={listing}
              actionType={actionType}
              onDetails={onDetails}
              onApprove={onApprove}
              onReject={onReject}
              onAuction={onAuction}
              actionLoading={actionLoading}
            />
          ))}
        </div>
      )}
    </section>
  );
}
