import { useState } from "react";
import AdminSection from "./components/AdminSection";
import CreateAuctionModal from "./components/CreateAuctionModal";
import ListingDetailsModal from "./components/ListingDetailsModal";
import RejectListingModal from "./components/RejectListingModal";
import { useAdminListings } from "./useAdminListings";
import "./AdminPage.css";

export default function AdminPage() {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [rejectListingId, setRejectListingId] = useState(null);
  const [auctionListingId, setAuctionListingId] = useState(null);

  const {
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
  } = useAdminListings();

  const handleOpenDetails = async (listingId) => {
    const listing = await openDetails(listingId);
    if (listing) setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    closeDetails();
  };

  const handleOpenRejectModal = (listingId) => {
    setRejectListingId(listingId);
  };

  const handleCloseRejectModal = () => {
    setRejectListingId(null);
  };

  const handleOpenAuctionModal = (listingId) => {
    setAuctionListingId(listingId);
  };

  const handleCloseAuctionModal = () => {
    setAuctionListingId(null);
  };

  return (
    <div className="adminPage">
      <div className="adminHeader">
        <div>
          <h1 className="adminTitle">Admin panelė</h1>
          <p className="adminSubtitle">Peržiūrėk, patvirtink arba atmesk listingus</p>
        </div>

        <button className="adminSecondaryBtn" onClick={() => (window.location.href = "/")}>
          ← Pagrindinis
        </button>
      </div>

      {error && <div className="adminError">{error}</div>}
      {success && <div className="adminSuccess">{success}</div>}
      {loading && <div className="adminInfo">Kraunama...</div>}

      <AdminSection
        title="Laukiantys patvirtinimo"
        listings={pendingListings}
        emptyText="Nėra laukiančių listingų"
        actionType="review"
        onDetails={handleOpenDetails}
        onApprove={approveListing}
        onReject={handleOpenRejectModal}
        actionLoading={actionLoading}
      />

      <AdminSection
        title="Patvirtinti lotų"
        listings={approvedListings}
        emptyText="Nėra patvirtintų lotų"
        actionType="auction"
        onDetails={handleOpenDetails}
        onAuction={handleOpenAuctionModal}
        actionLoading={actionLoading}
      />

      {detailsOpen && selectedListing && (
        <ListingDetailsModal
          listing={selectedListing}
          onClose={handleCloseDetails}
          onApprove={approveListing}
          onReject={handleOpenRejectModal}
          actionLoading={actionLoading}
        />
      )}

      {rejectListingId && (
        <RejectListingModal
          listingId={rejectListingId}
          onClose={handleCloseRejectModal}
          onSubmit={rejectListing}
          actionLoading={actionLoading}
        />
      )}

      {auctionListingId && (
        <CreateAuctionModal
          listingId={auctionListingId}
          onClose={handleCloseAuctionModal}
          onSubmit={createAuction}
          actionLoading={actionLoading}
        />
      )}
    </div>
  );
}
