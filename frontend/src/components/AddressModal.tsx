import { useState, useEffect } from "react";
import axiosClient from "../api/axiosClient";

interface Address {
  address_id: number;
  user_id: number;
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postal_code: string;
  county?: string;
  address_type: string;
  created_at: string;
}

interface AddressModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: (data: { shipping: Address; billing: Address }) => void;
  shippingAddresses: Address[];
  billingAddresses: Address[];
}

export default function AddressModal({
  isOpen,
  onClose,
  onSaved,
  shippingAddresses = [],
  billingAddresses = [],
}: AddressModalProps) {
  if (!isOpen) return null;

  // Mode: select or create
  const [mode, setMode] = useState(
    shippingAddresses.length > 0 || billingAddresses.length > 0
      ? "select"
      : "create"
  );

  useEffect(() => {
    if (shippingAddresses.length > 0 || billingAddresses.length > 0) {
      setMode("select");
    } else {
      setMode("create");
    }
  }, [shippingAddresses, billingAddresses]);

  // Two selectors
  const [shippingAddressId, setShippingAddressId] = useState<string>("");
  const [billingAddressId, setBillingAddressId] = useState<string>("");

  // Create form
  const [form, setForm] = useState({
    line1: "",
    line2: "",
    city: "",
    state: "",
    postal_code: "",
    county: "",
    address_type: "shipping",
  });

  type FormState = typeof form;
  type FormKey = keyof FormState;

  function updateField(key: FormKey, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  // CREATE MODE — save new address
  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();

    try {
      const res = await axiosClient.post("/addresses", form, {
        withCredentials: true,
      });

      const newAddress: Address = res.data;

      // Return new address for both shipping + billing
      onSaved({ shipping: newAddress, billing: newAddress });
      onClose();
    } catch (err) {
      console.error("Error saving address:", err);
    }
  }

  // SELECT MODE — return chosen shipping + billing
  function handleSubmitSelection() {
    const shipping = shippingAddresses.find(
      (a) => a.address_id === Number(shippingAddressId)
    );
    const billing = billingAddresses.find(
      (a) => a.address_id === Number(billingAddressId)
    );

    if (!shipping || !billing) return;

    onSaved({ shipping, billing });
    onClose();
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg w-full max-w-md shadow-xl relative">

        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-xl"
        >
          ×
        </button>

        {/* SELECT MODE */}
        {mode === "select" && (
          <div className="flex flex-col gap-6">
            <h2 className="text-2xl font-semibold mb-2">Select Addresses</h2>

            {/* Shipping */}
            <div>
              <p className="font-medium mb-1">Shipping Address</p>
              <select
                className="border p-2 rounded w-full"
                value={shippingAddressId}
                onChange={(e) => setShippingAddressId(e.target.value)}
              >
                <option value="">Choose shipping address</option>
                {shippingAddresses.map((addr) => (
                  <option key={addr.address_id} value={addr.address_id}>
                    {addr.line1}, {addr.city}, {addr.state} {addr.postal_code}
                  </option>
                ))}
              </select>
            </div>

            {/* Billing */}
            <div>
              <p className="font-medium mb-1">Billing Address</p>
              <select
                className="border p-2 rounded w-full"
                value={billingAddressId}
                onChange={(e) => setBillingAddressId(e.target.value)}
              >
                <option value="">Choose billing address</option>
                {billingAddresses.map((addr) => (
                  <option key={addr.address_id} value={addr.address_id}>
                    {addr.line1}, {addr.city}, {addr.state} {addr.postal_code}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleSubmitSelection}
              className="bg-black text-white py-2 rounded"
            >
              Continue
            </button>

            <button
              onClick={() => setMode("create")}
              className="bg-gray-300 py-2 rounded"
            >
              Add New Address
            </button>
          </div>
        )}

        {/* CREATE MODE */}
        {mode === "create" && (
          <>
            <h2 className="text-2xl font-semibold mb-4">Add Address</h2>

            <form onSubmit={handleCreate} className="space-y-3">

              <input
                className="border p-2 w-full"
                placeholder="Address Line 1"
                value={form.line1}
                onChange={(e) => updateField("line1", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="Address Line 2"
                value={form.line2}
                onChange={(e) => updateField("line2", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="City"
                value={form.city}
                onChange={(e) => updateField("city", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="State"
                value={form.state}
                onChange={(e) => updateField("state", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="Postal Code"
                value={form.postal_code}
                onChange={(e) => updateField("postal_code", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="County"
                value={form.county}
                onChange={(e) => updateField("county", e.target.value)}
              />

              <button
                type="submit"
                className="bg-black text-white w-full py-2 rounded"
              >
                Save Address
              </button>
            </form>

            {(shippingAddresses.length > 0 || billingAddresses.length > 0) && (
              <button
                onClick={() => setMode("select")}
                className="mt-4 text-gray-600 underline w-full text-center"
              >
                Back to address list
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
