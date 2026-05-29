import { useState } from "react";

export default function RejectListingModal({ listingId, onClose, onSubmit, actionLoading }) {
  const [reason, setReason] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    const success = await onSubmit(listingId, reason);
    if (success) onClose();
  };

  return (
    <div className="adminModalOverlay">
      <form className="adminModal" onSubmit={handleSubmit}>
        <h2 className="adminModalTitle">Atmesti lotą</h2>

        <label className="adminLabel">
          Atmetimo priežastis
          <textarea
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            className="adminTextarea"
            required
            minLength={3}
            placeholder="Pvz. Nepakanka nuotraukų arba neteisingi duomenys"
          />
        </label>

        <div className="adminModalActions">
          <button type="button" className="adminCancelBtn" onClick={onClose} disabled={actionLoading}>
            Atšaukti
          </button>

          <button type="submit" className="adminRejectBtn" disabled={actionLoading}>
            Atmesti
          </button>
        </div>
      </form>
    </div>
  );
}
