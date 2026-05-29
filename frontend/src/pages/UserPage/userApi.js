import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8001/api/v1";

const getAuthHeaders = () => {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const authConfig = () => ({ headers: getAuthHeaders() });

export async function getMyListings() {
  const res = await axios.get(`${API_BASE_URL}/my/listings`, authConfig());
  return (res.data || []).filter((listing) => listing.status !== "draft");
}

export async function getWonLots() {
  const res = await axios.get(`${API_BASE_URL}/users/me/won-lots`, authConfig());
  return res.data || [];
}

export async function getPendingApprovals() {
  const res = await axios.get(`${API_BASE_URL}/users/me/pending-approvals`, authConfig());
  return res.data || [];
}

export async function getUserPageData() {
  const [listings, wonLots, pendingApprovals] = await Promise.all([
    getMyListings(),
    getWonLots(),
    getPendingApprovals(),
  ]);

  return { listings, wonLots, pendingApprovals };
}

export async function approveAuction(auctionId) {
  await axios.post(
    `${API_BASE_URL}/users/me/auctions/${auctionId}/approve`,
    {},
    authConfig()
  );
}

export async function rejectAuction(auctionId) {
  await axios.post(
    `${API_BASE_URL}/users/me/auctions/${auctionId}/reject`,
    {},
    authConfig()
  );
}
