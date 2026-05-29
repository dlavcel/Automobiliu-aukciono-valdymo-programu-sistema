import { useCallback, useEffect, useState } from "react";
import {
  approveAdminListing,
  createAdminAuction,
  fetchAdminListing,
  fetchAdminListings,
  rejectAdminListing,
} from "./adminApi";

const getErrorMessage = (err, fallback) => err.response?.data?.detail || fallback;

export function useAdminListings() {
  const [pendingListings, setPendingListings] = useState([]);
  const [approvedListings, setApprovedListings] = useState([]);
  const [selectedListing, setSelectedListing] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadListings = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const data = await fetchAdminListings();
      setPendingListings(data.pendingListings);
      setApprovedListings(data.approvedListings);
    } catch (err) {
      setError(getErrorMessage(err, "Nepavyko užkrauti listingų"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadListings();
  }, [loadListings]);

  const openDetails = useCallback(async (listingId) => {
    try {
      setError("");
      const listing = await fetchAdminListing(listingId);
      setSelectedListing(listing);
      return listing;
    } catch (err) {
      setError(getErrorMessage(err, "Nepavyko užkrauti listingo"));
      return null;
    }
  }, []);

  const closeDetails = useCallback(() => {
    setSelectedListing(null);
  }, []);

  const approveListing = useCallback(
    async (listingId) => {
      try {
        setActionLoading(true);
        setError("");
        setSuccess("");

        await approveAdminListing(listingId);
        setSuccess("Listingas sėkmingai patvirtintas");
        closeDetails();
        await loadListings();
      } catch (err) {
        setError(getErrorMessage(err, "Nepavyko patvirtinti listingo"));
      } finally {
        setActionLoading(false);
      }
    },
    [closeDetails, loadListings]
  );

  const rejectListing = useCallback(
    async (listingId, reason) => {
      try {
        setActionLoading(true);
        setError("");
        setSuccess("");

        await rejectAdminListing(listingId, reason);
        setSuccess("Listingas atmestas");
        closeDetails();
        await loadListings();
        return true;
      } catch (err) {
        setError(getErrorMessage(err, "Nepavyko atmesti listingo"));
        return false;
      } finally {
        setActionLoading(false);
      }
    },
    [closeDetails, loadListings]
  );

  const createAuction = useCallback(async ({ listingId, startsAt, endsAt }) => {
    try {
      setActionLoading(true);
      setError("");
      setSuccess("");

      if (new Date(endsAt) <= new Date(startsAt)) {
        setError("Aukciono pabaiga turi būti vėliau už pradžią");
        return false;
      }

      await createAdminAuction({ listingId, startsAt, endsAt });
      setApprovedListings((prev) => prev.filter((listing) => listing.id !== listingId));
      setSuccess("Aukcionas sėkmingai sukurtas");
      return true;
    } catch (err) {
      setError(getErrorMessage(err, "Nepavyko sukurti aukciono"));
      return false;
    } finally {
      setActionLoading(false);
    }
  }, []);

  return {
    pendingListings,
    approvedListings,
    selectedListing,
    error,
    success,
    loading,
    actionLoading,
    openDetails,
    closeDetails,
    approveListing,
    rejectListing,
    createAuction,
  };
}
