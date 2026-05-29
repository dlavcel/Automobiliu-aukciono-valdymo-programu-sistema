import { IMAGE_BASE_URL } from "../constants";
import { formatMoney, formatSeverity, getStatusText } from "../formatters";
import DetailItem from "./DetailItem";

export default function ListingDetailsModal({ listing, onClose, onApprove, onReject, actionLoading }) {
  if (!listing) return null;

  return (
    <div className="adminModalOverlay">
      <div className="adminLargeModal">
        <h2 className="adminModalTitle">
          {listing.make} {listing.model} {listing.year}
        </h2>

        <div className="adminDetailGrid">
          <DetailItem label="Pavadinimas" value={listing.title} />
          <DetailItem label="Statusas" value={getStatusText(listing.status)} />
          <DetailItem label="Lokacija" value={listing.location} />
          <DetailItem label="Rida" value={listing.mileage} />
          <DetailItem label="Kuras" value={listing.fuel_type} />
          <DetailItem label="Pavarų dėžė" value={listing.transmission} />
          <DetailItem label="Varantieji ratai" value={listing.drive_type} />
          <DetailItem label="Pirminis pažeidimas" value={listing.primary_damage} />
          <DetailItem label="Antrinis pažeidimas" value={listing.secondary_damage} />
          <DetailItem label="Pirminio pažeidimo sunkumas" value={formatSeverity(listing.primary_damage_severity)} />
          <DetailItem label="Antrinio pažeidimo sunkumas" value={formatSeverity(listing.secondary_damage_severity)} />
          <DetailItem label="Prognozuota kaina" value={formatMoney(listing.predicted_price)} />
          <DetailItem label="Atmetimo priežastis" value={listing.rejection_reason} />
        </div>

        <div className="adminDetailDescription">
          <strong>Aprašymas</strong>
          <p>{listing.description || "Aprašymas nepateiktas"}</p>
        </div>

        {listing.images?.length > 0 && (
          <div className="adminDetailImages">
            {listing.images.map((img) => (
              <img key={img.id} src={`${IMAGE_BASE_URL}${img.image_url}`} alt="" className="adminDetailImage" />
            ))}
          </div>
        )}

        <div className="adminModalActions">
          <button type="button" className="adminCancelBtn" onClick={onClose} disabled={actionLoading}>
            Uždaryti
          </button>

          {listing.status === "pending_review" && (
            <>
              <button type="button" className="adminRejectBtn" onClick={() => onReject(listing.id)} disabled={actionLoading}>
                Atmesti
              </button>

              <button type="button" className="adminSaveBtn" onClick={() => onApprove(listing.id)} disabled={actionLoading}>
                Patvirtinti
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
