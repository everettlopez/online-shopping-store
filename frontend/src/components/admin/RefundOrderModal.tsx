import { useState } from "react";
import Modal from "@mui/material/Modal";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import TextField from "@mui/material/TextField";

interface Props {
  open: boolean;
  orderNumber: string;
  // What's left to refund on the order
  remaining: number;
  onClose: () => void;
  onConfirm: (amount: number, restock: boolean) => Promise<void>;
}

// Refunds go through Stripe, so they ask twice: choose the amount, then confirm it.
// Mount it with a fresh key per order so it starts from the order's remaining amount.
export default function RefundOrderModal({ open, orderNumber, remaining, onClose, onConfirm }: Props) {
  const [amountText, setAmountText] = useState(remaining.toFixed(2));
  const [restock, setRestock] = useState(true);
  const [confirming, setConfirming] = useState(false);
  const [saving, setSaving] = useState(false);

  const amount = Math.round(Number(amountText) * 100) / 100;
  const valid = Number.isFinite(amount) && amount > 0 && amount <= remaining;
  // Only a full refund returns the items to stock
  const full = valid && amount === remaining;

  async function refund() {
    setSaving(true);
    try {
      await onConfirm(amount, full && restock);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal open={open} onClose={saving ? undefined : onClose}>
      <div className="bg-white p-6 rounded-lg shadow-xl w-[420px] max-w-[calc(100vw-32px)] mx-auto mt-[20vh] flex flex-col gap-4">
        <h2 className="text-xl">Refund order #{orderNumber.toUpperCase()}</h2>

        {!confirming ? (
          <>
            <TextField
              label="Amount to refund"
              type="number"
              size="small"
              value={amountText}
              onChange={(e) => setAmountText(e.target.value)}
              slotProps={{ htmlInput: { min: 0.01, max: remaining, step: 0.01 } }}
              error={!valid}
              helperText={valid ? `Up to $${remaining.toFixed(2)}` : `Enter an amount from $0.01 to $${remaining.toFixed(2)}`}
            />
            <FormControlLabel
              control={<Checkbox checked={full && restock} disabled={!full} onChange={(e) => setRestock(e.target.checked)} />}
              label={full ? "Return the items to stock" : "Partial refunds keep the items out of stock"}
            />
            <div className="flex justify-end gap-4">
              <button onClick={onClose} className="border px-4 py-2 rounded-full">Cancel</button>
              <button onClick={() => setConfirming(true)} disabled={!valid} className="bg-black text-white px-4 py-2 rounded-full disabled:opacity-50">
                Review refund
              </button>
            </div>
          </>
        ) : (
          <>
            <p>
              Refund <strong>${amount.toFixed(2)}</strong> to the customer through Stripe? This can't be undone.
              {full && (restock ? " The items go back in stock." : " The items stay out of stock.")}
            </p>
            <p className="text-sm text-gray-600">The customer gets an email about the refund.</p>
            <div className="flex justify-end gap-4">
              <button onClick={() => setConfirming(false)} disabled={saving} className="border px-4 py-2 rounded-full">Back</button>
              <button onClick={refund} disabled={saving} className="bg-red-500 text-white px-4 py-2 rounded-full disabled:opacity-50">
                {saving ? "Refunding..." : `Refund $${amount.toFixed(2)}`}
              </button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}
