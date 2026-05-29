export const API_BASE_URL = "http://127.0.0.1:8001/api/v1";
export const IMAGE_BASE_URL = "http://127.0.0.1:8001";

export const STATUS_LABELS = {
  pending_review: "Peržiūroje",
  approved: "Patvirtintas",
  rejected: "Atmestas",
  draft: "Juodraštis",
};

export const STATUS_CLASSES = {
  pending_review: "statusBadgePending",
  approved: "statusBadgeApproved",
  rejected: "statusBadgeRejected",
  draft: "statusBadgeDraft",
};

export const EMPTY_AUCTION_FORM = {
  starts_at: "",
  ends_at: "",
};
