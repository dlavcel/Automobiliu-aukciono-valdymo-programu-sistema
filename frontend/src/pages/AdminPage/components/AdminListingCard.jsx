import { IMAGE_BASE_URL, STATUS_CLASSES } from "../constants";
import { formatMoney, getStatusText } from "../formatters";

export default function AdminListingCard({
  listing,
  actionType,
  onDetails,
  onApprove,
  onReject,
  onAuction,
  actionLoading,
}) {
  const imageUrl = listing.images?.[0]?.image_url
    ? `${IMAGE_BASE_URL}${listing.images[0].image_url}`
    : null;

  const statusClass = STATUS_CLASSES[listing.status] || "statusBadgeDefault";

  return (
    <div className="adminCard">
      <div className="adminImageWrap">
        <span className={`adminStatusBadge ${statusClass}`}>{getStatusText(listing.status)}</span>

        {imageUrl ? (
          <img src={imageUrl} alt={listing.title} className="adminImage" />
        ) : (
          <div className="adminNoImage">Nėra nuotraukos</div>
        )}
      </div>

      <div className="adminCardBody">
        <h3 className="adminCardTitle">
          {listing.make} {listing.model}
        </h3>

        <p className="adminCardMeta">
          {listing.year} • {listing.location || "Lokacija nenurodyta"}
        </p>

        <p className="adminDescription">{listing.description || "Aprašymas nepateiktas"}</p>
        <p className="adminPrice">DI kaina: {formatMoney(listing.predicted_price)}</p>

        <div className="adminCardActions">
          <button className="adminDetailsBtn" onClick={() => onDetails(listing.id)} disabled={actionLoading}>
            Peržiūrėti
          </button>

          {actionType === "review" && (
            <>
              <button className="adminRejectBtnSmall" onClick={() => onReject(listing.id)} disabled={actionLoading}>
                Atmesti
              </button>
              <button className="adminApproveBtnSmall" onClick={() => onApprove(listing.id)} disabled={actionLoading}>
                Patvirtinti
              </button>
            </>
          )}

          {actionType === "auction" && (
            <button className="adminAuctionBtnSmall" onClick={() => onAuction(listing.id)} disabled={actionLoading}>
              Kurti aukcioną
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
