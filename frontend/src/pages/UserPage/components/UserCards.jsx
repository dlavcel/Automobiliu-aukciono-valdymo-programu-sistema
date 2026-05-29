import VehicleCard from "./VehicleCard";
import {
  formatAuctionStatus,
  formatMoney,
  formatSaleResultStatus,
  getListingDisplayStatus,
} from "../listingFormatters.js";

export function PendingApprovalCard({ auction, navigate, loading, onApprove, onReject }) {
  const listing = auction.listing;

  return (
    <VehicleCard
      listing={listing}
      badge={{ text: "Laukia patvirtinimo", color: "#f59e0b" }}
      meta={`${listing?.year || "-"} • ${listing?.location || "Lokacija nenurodyta"}`}
      description={<>Aukščiausias pasiūlymas: <strong>{formatMoney(auction.current_price)}</strong></>}
      imageAlt="Aukcionas"
      actions={
        <>
          <button
            className="btn btn--secondary"
            onClick={() => navigate(`/lots/${auction.id}`)}
            disabled={loading}
          >
            Peržiūrėti
          </button>

          <button
            className="btn btn--success"
            onClick={onApprove}
            disabled={loading}
            style={{ opacity: loading ? 0.6 : 1 }}
          >
            {loading ? "Vykdoma..." : "Patvirtinti"}
          </button>

          <button
            className="btn btn--danger"
            onClick={onReject}
            disabled={loading}
            style={{ opacity: loading ? 0.6 : 1 }}
          >
            Atmesti
          </button>
        </>
      }
    >
      <p className="user-card__meta">
        Aukcionas baigėsi: {auction.ends_at ? new Date(auction.ends_at).toLocaleString() : "-"}
      </p>
    </VehicleCard>
  );
}

export function WonLotCard({ auction, navigate }) {
  const listing = auction.listing;

  return (
    <VehicleCard
      listing={listing}
      badge={{ text: "Laimėtas", color: "#16a34a" }}
      meta={`${listing?.year || "-"} • ${listing?.location || "Lokacija nenurodyta"}`}
      description={<>Galutinė kaina: <strong>{formatMoney(auction.current_price)}</strong></>}
      imageAlt="Laimėtas automobilis"
      actions={
        <button className="btn btn--secondary" onClick={() => navigate(`/lots/${auction.id}`)}>
          Peržiūrėti
        </button>
      }
    >
      <p className="user-card__meta">
        Aukcionas baigėsi: {auction.ends_at ? new Date(auction.ends_at).toLocaleString() : "-"}
      </p>
    </VehicleCard>
  );
}

export function ListingCard({ listing, navigate }) {
  const displayStatus = getListingDisplayStatus(listing);

  return (
    <VehicleCard
      listing={listing}
      badge={displayStatus}
      meta={`${listing.year || "-"} • ${listing.location || "Lokacija nenurodyta"}`}
      description={listing.description || "Aprašymas nepateiktas"}
      actions={
        listing.auction?.id ? (
          <button className="btn btn--secondary" onClick={() => navigate(`/lots/${listing.auction.id}`)}>
            Peržiūrėti aukcioną
          </button>
        ) : null
      }
    >
      {listing.rejection_reason && (
        <p className="user-card__reject-reason">
          Atmetimo priežastis: {listing.rejection_reason}
        </p>
      )}

      {listing.auction && (
        <div className="auction-info">
          <div>
            Aukciono statusas: <strong>{formatAuctionStatus(listing.auction.status)}</strong>
          </div>

          <div>
            Pardavimo rezultatas: <strong>{formatSaleResultStatus(listing.auction.sale_result_status)}</strong>
          </div>

          {listing.auction.current_price !== null && listing.auction.current_price !== undefined && (
            <div>
              Kaina: <strong>{formatMoney(listing.auction.current_price)}</strong>
            </div>
          )}
        </div>
      )}
    </VehicleCard>
  );
}
