export const BACKEND_BASE = "http://127.0.0.1:8001";
export const API_BASE_URL = `${BACKEND_BASE}/api/v1`;

export const MIN_IMAGE_WIDTH = 1280;
export const MIN_IMAGE_HEIGHT = 720;
export const MAX_ANALYSIS_IMAGES = 6;


export const auctionTypeOptions = [
  { value: "english", label: "Kylantis aukcionas" },
  { value: "sealed_first_price", label: "Uždaro pasiūlymo aukcionas" },
];

export const saleTypeOptions = [
  { value: "pure_sale", label: "Paprastas pardavimas" },
  { value: "reserve_price", label: "Su rezervine kaina" },
  { value: "on_approval", label: "Pardavimas su savininko patvirtinimu" },
];

export const fuelTypeOptions = [
  { value: "DIESEL", label: "Dyzelinas" },
  { value: "ELECTRIC", label: "Elektra" },
  { value: "FLEXIBLE FUEL", label: "Lankstus kuras" },
  { value: "GAS", label: "Benzinas" },
  { value: "HYBRID ENGINE", label: "Hibridas" },
  { value: "OTHER", label: "Kita" },
  { value: "UNKNOWN", label: "Nevizualus / nerasta" },
];

export const driveTypeOptions = [
  { value: "FWD", label: "Priekiniai varomi" },
  { value: "RWD", label: "Galiniai varomi" },
  { value: "AWD", label: "Visi varomi" },
  { value: "4WD", label: "Keturi varomi (4WD)" },
  { value: "4x2", label: "4x2" },
  { value: "UNKNOWN", label: "Nežinoma" },
];

export const transmissionOptions = [
  { value: "AUTOMATIC", label: "Automatinė" },
  { value: "MANUAL", label: "Mechaninė" },
  { value: "UNKNOWN", label: "Nežinoma" },
];

export const damageOptions = [
  { value: "ALL OVER", label: "Pažeista visur" },
  { value: "BIOHAZARD", label: "Biologinis užterštumas" },
  { value: "BURN", label: "Degimo pažeidimai" },
  { value: "BURN - ENGINE", label: "Variklio degimo pažeidimai" },
  { value: "BURN - INTERIOR", label: "Salono degimo pažeidimai" },
  { value: "CASH FOR CLUNKERS", label: "Sena transporto priemonė utilizacijai" },
  { value: "DAMAGE HISTORY", label: "Pažeidimų istorija" },
  { value: "ELECTRICAL", label: "Elektros sistemos gedimas" },
  { value: "ENGINE DAMAGE", label: "Variklio pažeidimas" },
  { value: "FRAME DAMAGE", label: "Rėmo pažeidimas" },
  { value: "FRONT & REAR", label: "Priekis ir galas" },
  { value: "FRONT END", label: "Priekio pažeidimas" },
  { value: "HAIL", label: "Krušos pažeidimai" },
  { value: "MECHANICAL", label: "Mechaninis gedimas" },
  { value: "MINOR DENT/SCRATCHES", label: "Smulkūs įlenkimai / įbrėžimai" },
  { value: "MISSING/ALTERED VIN", label: "Trūksta / pakeistas VIN" },
  { value: "NORMAL WEAR & TEAR", label: "Normalus nusidėvėjimas" },
  { value: "PARTIAL REPAIR", label: "Dalinis remontas" },
  { value: "REAR END", label: "Galo pažeidimas" },
  { value: "REJECTED REPAIR", label: "Netinkamas remontas" },
  { value: "REPLACED VIN", label: "Pakeistas VIN" },
  { value: "REPOSSESSION", label: "Susigrąžinta transporto priemonė" },
  { value: "ROLLOVER", label: "Apsivertimas" },
  { value: "ROOF", label: "Stogo pažeidimas" },
  { value: "SIDE", label: "Šono pažeidimas" },
  { value: "STORM DAMAGE", label: "Audros pažeidimai" },
  { value: "STRIPPED", label: "Išardyta" },
  { value: "SUSPENSION", label: "Pakabos pažeidimas" },
  { value: "THEFT", label: "Vagystė" },
  { value: "TRANSMISSION DAMAGE", label: "Pavarų dėžės pažeidimas" },
  { value: "UNDERCARRIAGE", label: "Važiuoklės apačios pažeidimas" },
  { value: "UNKNOWN", label: "Nežinoma" },
  { value: "VANDALISM", label: "Vandalizmas" },
  { value: "WATER/FLOOD", label: "Vandens / užliejimo pažeidimas" },
];

export const initialForm = {
  make: "",
  model: "",
  year: "",
  auction_type: "english",
  sale_type: "pure_sale",
  reserve_price: "",
  vin: "",
  mileage: "",
  fuel_type: "",
  engine_volume: "",
  cylinders: "",
  drive_type: "",
  transmission: "",
  body_type: "",
  color: "",
  primary_damage: "",
  secondary_damage: "",
  description: "",
  location: "",
};

