import axios from "axios";
import { API_BASE_URL } from "./constants";

function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchAdminListings() {
  const headers = getAuthHeaders();

  const [pendingRes, approvedRes] = await Promise.all([
    axios.get(`${API_BASE_URL}/admin/listings/pending`, { headers }),
    axios.get(`${API_BASE_URL}/admin/listings/approved`, { headers }),
  ]);

  return {
    pendingListings: pendingRes.data || [],
    approvedListings: approvedRes.data || [],
  };
}

export async function fetchAdminListing(listingId) {
  const res = await axios.get(`${API_BASE_URL}/admin/listings/${listingId}`, {
    headers: getAuthHeaders(),
  });

  return res.data;
}

export async function approveAdminListing(listingId) {
  await axios.post(
    `${API_BASE_URL}/admin/listings/${listingId}/approve`,
    {},
    { headers: getAuthHeaders() }
  );
}

export async function rejectAdminListing(listingId, reason) {
  await axios.post(
    `${API_BASE_URL}/admin/listings/${listingId}/reject`,
    { reason },
    { headers: getAuthHeaders() }
  );
}

export async function createAdminAuction({ listingId, startsAt, endsAt }) {
  await axios.post(
    `${API_BASE_URL}/admin/auctions`,
    {
      listing_id: listingId,
      starts_at: new Date(startsAt).toISOString(),
      ends_at: new Date(endsAt).toISOString(),
    },
    { headers: getAuthHeaders() }
  );
}
