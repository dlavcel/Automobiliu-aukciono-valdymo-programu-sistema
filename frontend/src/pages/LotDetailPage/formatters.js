export function normalizeEnum(value) {
  if (value === null || value === undefined || value === "") return "";
  return String(value).toUpperCase().replace(/\s+/g, "_").replace(/&/g, "AND");
}

export function formatAuctionType(type) {
  switch (type) {
    case "english":
      return "Kylantis aukcionas";
    case "dutch":
      return "Mažėjantis aukcionas";
    case "sealed_first_price":
      return "Uždaro pasiūlymo aukcionas";
    default:
      return type || "-";
  }
}

export function formatSaleType(type) {
  switch (type) {
    case "pure_sale":
      return "Paprastas pardavimas";
    case "reserve_price":
      return "Su rezervine kaina";
    case "on_approval":
      return "Tvirtina pardavėjas";
    default:
      return type || "-";
  }
}

export function formatAuctionStatus(status) {
  switch (normalizeEnum(status)) {
    case "SCHEDULED":
      return "Suplanuotas";
    case "LIVE":
      return "Vyksta";
    case "ENDED":
      return "Baigėsi";
    case "CANCELLED":
      return "Atšauktas";
    default:
      return status || "-";
  }
}

export function formatFuelType(value) {
  switch (normalizeEnum(value)) {
    case "PETROL":
    case "GASOLINE":
      return "Benzinas";
    case "DIESEL":
      return "Dyzelinas";
    case "ELECTRIC":
      return "Elektra";
    case "HYBRID":
    case "HYBRID_ENGINE":
      return "Hibridas";
    case "LPG":
      return "Dujos";
    default:
      return value || "-";
  }
}

export function formatTransmission(value) {
  switch (normalizeEnum(value)) {
    case "AUTOMATIC":
      return "Automatinė";
    case "MANUAL":
      return "Mechaninė";
    default:
      return value || "-";
  }
}

export function formatDriveType(value) {
  switch (normalizeEnum(value)) {
    case "FWD":
      return "Priekiniai varantys ratai";
    case "RWD":
      return "Galiniai varantys ratai";
    case "AWD":
    case "4WD":
      return "Visi varantys ratai";
    default:
      return value || "-";
  }
}

export function formatDamage(value) {
  switch (normalizeEnum(value)) {
    case "NORMAL_WEAR":
    case "NORMAL_WEAR_AND_TEAR":
      return "Natūralus nusidėvėjimas";
    case "MINOR":
    case "MINOR_DENT_SCRATCHES":
      return "Smulkūs įlenkimai / įbrėžimai";
    case "FRONT":
    case "FRONT_END":
      return "Priekinės dalies pažeidimas";
    case "REAR":
    case "REAR_END":
      return "Galinės dalies pažeidimas";
    case "SIDE":
      return "Šoninis pažeidimas";
    case "FRONT_AND_REAR":
      return "Priekio ir galo pažeidimai";
    case "ELECTRICAL":
      return "Elektros sistemos pažeidimas";
    case "MECHANICAL":
      return "Mechaninis gedimas";
    case "WATER_FLOOD":
      return "Vandens / potvynio žala";
    case "BURN":
      return "Gaisro žala";
    case "HAIL":
      return "Krušos žala";
    case "VANDALISM":
      return "Vandalizmas";
    case "ROLLOVER":
      return "Apsivertimas";
    case "ALL_OVER":
      return "Pažeidimai visame kėbule";
    case "UNDERCARRIAGE":
      return "Dugno pažeidimas";
    case "ENGINE_DAMAGE":
      return "Variklio pažeidimas";
    case "FRAME_DAMAGE":
      return "Rėmo pažeidimas";
    case "TRANSMISSION_DAMAGE":
      return "Pavarų dėžės pažeidimas";
    case "DAMAGE_HISTORY":
      return "Pažeidimų istorija";
    case "BIOHAZARD":
      return "Biologinis pavojus";
    case "THEFT":
      return "Vagystė";
    case "UNKNOWN":
      return "Nežinoma";
    default:
      return value || "-";
  }
}

export function formatValue(value) {
  if (value === null || value === undefined || value === "") return "-";
  return value;
}

export function formatMoney(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (Number.isNaN(number)) return `${value} €`;
  return `${number.toFixed(2)} €`;
}

export function formatSeverity(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (Number(value) === -1) return "Nevizualus / nerasta";
  return Number(value).toFixed(1);
}

export function getDetectionLabel(det) {
  return det.label || det.class || "Aptikta";
}

export function getDetectionConfidence(det) {
  return det.confidence ?? det.conf ?? 0;
}

export function getDetectionSource(det) {
  return det.source || det.damage_source || "-";
}
