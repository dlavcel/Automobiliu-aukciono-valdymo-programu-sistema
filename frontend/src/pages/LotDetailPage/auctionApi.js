import axios from "axios";

export const BACKEND_BASE = "http://127.0.0.1:8001";
export const API_BASE_URL = `${BACKEND_BASE}/api/v1`;
export const WS_BASE_URL = "ws://127.0.0.1:8001";

export function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getAuction(auctionId) {
  const res = await axios.get(`${API_BASE_URL}/auctions/${auctionId}`);
  return res.data || null;
}

export async function getAuctionBids(auctionId) {
  const res = await axios.get(`${API_BASE_URL}/auctions/${auctionId}/bids`);
  return res.data || [];
}

export async function placeEnglishBid(auctionId, amount) {
  const res = await axios.post(
    `${API_BASE_URL}/auctions/${auctionId}/bids`,
    { amount },
    { headers: getAuthHeaders() }
  );
  return res.data;
}

export async function placeSealedBid(auctionId, amount) {
  const res = await axios.post(
    `${API_BASE_URL}/auctions/${auctionId}/sealed-bids`,
    { amount },
    { headers: getAuthHeaders() }
  );
  return res.data;
}

export async function analyzeListingImage(listingId, imageId) {
  const res = await axios.post(
    `${API_BASE_URL}/listings/${listingId}/images/${imageId}/analyze`,
    {},
    { headers: getAuthHeaders() }
  );

  return {
    ...res.data,
    annotatedUrl: `${BACKEND_BASE}${res.data.annotated_image_url}`,
  };
}
