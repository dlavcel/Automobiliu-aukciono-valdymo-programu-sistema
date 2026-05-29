const IMAGE_BASE_URL = "http://127.0.0.1:8001";

function getImageUrl(listing) {
  const raw = listing?.images?.[0]?.image_url || listing?.images?.[0]?.url;
  if (!raw) return null;
  return raw.startsWith("http") ? raw : `${IMAGE_BASE_URL}${raw}`;
}

export default function VehicleCard({
  listing,
  badge,
  meta,
  description,
  children,
  actions,
  imageAlt = "Automobilis",
}) {
  const imageUrl = getImageUrl(listing);
  const title = [listing?.make, listing?.model].filter(Boolean).join(" ");

  return (
    <div className="user-card">
      <div className="user-card__image-wrap">
        {badge && (
          <span
            className="user-card__status-badge"
            style={{ background: badge.color }}
          >
            {badge.text}
          </span>
        )}

        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title || imageAlt}
            className="user-card__image"
          />
        ) : (
          <div className="user-card__no-image">Nėra nuotraukos</div>
        )}
      </div>

      <div className="user-card__body">
        <h3 className="user-card__title">
          {title || listing?.title || "Automobilis"}
        </h3>

        {meta && <p className="user-card__meta">{meta}</p>}
        {description && <p className="user-card__description">{description}</p>}

        {children}

        {actions && <div className="user-card__actions">{actions}</div>}
      </div>
    </div>
  );
}
