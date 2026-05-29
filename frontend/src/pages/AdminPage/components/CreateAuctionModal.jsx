import { useState } from "react";
import { EMPTY_AUCTION_FORM } from "../constants";

export default function CreateAuctionModal({ listingId, onClose, onSubmit, actionLoading }) {
  const [form, setForm] = useState(EMPTY_AUCTION_FORM);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const success = await onSubmit({
      listingId,
      startsAt: form.starts_at,
      endsAt: form.ends_at,
    });
    if (success) onClose();
  };

  return (
    <div className="adminModalOverlay">
      <form className="adminModal" onSubmit={handleSubmit}>
        <h2 className="adminModalTitle">Kurti aukcioną</h2>

        <label className="adminLabel">
          Pradžios laikas
          <input
            type="datetime-local"
            value={form.starts_at}
            onChange={(event) => updateField("starts_at", event.target.value)}
            className="adminInput"
            required
          />
        </label>

        <label className="adminLabel">
          Pabaigos laikas
          <input
            type="datetime-local"
            value={form.ends_at}
            onChange={(event) => updateField("ends_at", event.target.value)}
            className="adminInput"
            required
          />
        </label>

        <div className="adminModalActions">
          <button type="button" className="adminCancelBtn" onClick={onClose} disabled={actionLoading}>
            Atšaukti
          </button>

          <button type="submit" className="adminSaveBtn" disabled={actionLoading}>
            Sukurti aukcioną
          </button>
        </div>
      </form>
    </div>
  );
}
