import axios from "axios";
import { API_BASE_URL } from "./constants";

function getAuthConfig(isMultipart = false) {
  const token = localStorage.getItem("token");
  const headers = {};

  if (token) headers.Authorization = `Bearer ${token}`;
  if (isMultipart) headers["Content-Type"] = "multipart/form-data";

  return { headers };
}

export async function createListing(payload) {
  const res = await axios.post(`${API_BASE_URL}/listings`, payload, getAuthConfig());
  return res.data;
}

export async function uploadListingImage(listingId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await axios.post(
    `${API_BASE_URL}/listings/${listingId}/images/upload`,
    formData,
    getAuthConfig(true)
  );

  return res.data;
}

export async function submitListing(listingId) {
  await axios.post(`${API_BASE_URL}/listings/${listingId}/submit`, {}, getAuthConfig());
}

export async function predictListingPrice(listingId, useCv) {
  const res = await axios.post(
    `${API_BASE_URL}/listings/${listingId}/predict-price`,
    { use_cv: useCv },
    getAuthConfig()
  );

  return res.data;
}

export async function analyzeListingImage(listingId, imageId) {
  const res = await axios.post(
    `${API_BASE_URL}/listings/${listingId}/images/${imageId}/analyze`,
    {},
    getAuthConfig()
  );

  return res.data;
}
