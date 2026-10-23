import { useMemo, useState } from "react";
import axiosClient from "../api/axiosClient";

interface Address {
  address_id: number;
  user_id: number;
  full_name: string;
  phone?: string | null;
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
  addresses: Address[];
}

const emptyForm = {
  full_name: "",
  phone: "",
  line1: "",
  line2: "",
  city: "",
  state: "",
  postal_code: "",
  county: "",
  // Required by the API; any saved address can be used for shipping or billing
  address_type: "shipping",
};

// Mounted only while open, so every opening starts from a fresh form
export default function AddressModal(props: AddressModalProps) {
  if (!props.isOpen) return null;
  return <AddressDialog {...props} />;
}

function AddressDialog({
  onClose,
  onSaved,
  addresses = [],
}: AddressModalProps) {
  // Addresses saved in this dialog; the list from the page may also arrive after it opens
  const [created, setCreated] = useState<Address[]>([]);

  // Every saved address, newest first
  const savedAddresses = useMemo(() => {
    const byId = new Map([...addresses, ...created].map((a) => [a.address_id, a]));
    return [...byId.values()].sort((a, b) => b.address_id - a.address_id);
  }, [addresses, created]);
  const newestId = savedAddresses.length > 0 ? String(savedAddresses[0].address_id) : "";

  // Mode: select or create
  const [mode, setMode] = useState<"select" | "create">(addresses.length > 0 ? "select" : "create");

  // What the shopper picked; until they pick, the newest address
  const [shippingChoice, setShippingAddressId] = useState<string>("");
  const [billingChoice, setBillingAddressId] = useState<string>("");
  const shippingAddressId = shippingChoice || newestId;
  const billingAddressId = billingChoice || newestId;
  const [billingSameAsShipping, setBillingSameAsShipping] = useState(true);
  const [error, setError] = useState("");

  // Create form
  const [form, setForm] = useState(emptyForm);

  type FormState = typeof form;
  type FormKey = keyof FormState;

  function updateField(key: FormKey, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  // CREATE MODE — save new address, then pick it in the select view
  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    try {
      // Optional fields left blank are sent as missing rather than empty text
      const res = await axiosClient.post("/addresses/", {
        ...form,
        phone: form.phone.trim() || null,
        line2: form.line2.trim() || null,
        county: form.county.trim() || null,
      }, {
        withCredentials: true,
      });

      const newAddress: Address = res.data;
      const newId = String(newAddress.address_id);

      setCreated((prev) => [newAddress, ...prev]);
      setShippingAddressId(newId);
      if (billingSameAsShipping || !billingAddressId) {
        setBillingAddressId(newId);
      }
      setForm(emptyForm);
      setMode("select");
    } catch (err) {
      console.error("Error saving address:", err);
      setError("Could not save the address. Please check the fields and try again.");
    }
  }

  // SELECT MODE — return chosen shipping + billing
  function handleSubmitSelection() {
    const shipping = savedAddresses.find(
      (a) => a.address_id === Number(shippingAddressId)
    );
    const billing = billingSameAsShipping
      ? shipping
      : savedAddresses.find((a) => a.address_id === Number(billingAddressId));

    if (!shipping) {
      setError("Please choose a shipping address.");
      return;
    }
    if (!billing) {
      setError("Please choose a billing address.");
      return;
    }

    onSaved({ shipping, billing });
    onClose();
  }

  function formatAddress(addr: Address) {
    const line2 = addr.line2 ? ` ${addr.line2}` : "";
    return `${addr.full_name}, ${addr.line1}${line2}, ${addr.city}, ${addr.state} ${addr.postal_code}`;
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
                className="border p-2 rounded-sm w-full"
                value={shippingAddressId}
                onChange={(e) => setShippingAddressId(e.target.value)}
              >
                <option value="">Choose shipping address</option>
                {savedAddresses.map((addr) => (
                  <option key={addr.address_id} value={addr.address_id}>
                    {formatAddress(addr)}
                  </option>
                ))}
              </select>
            </div>

            {/* Billing */}
            <div className="flex flex-col gap-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={billingSameAsShipping}
                  onChange={(e) => setBillingSameAsShipping(e.target.checked)}
                />
                Billing address same as shipping
              </label>

              {!billingSameAsShipping && (
                <div>
                  <p className="font-medium mb-1">Billing Address</p>
                  <select
                    className="border p-2 rounded-sm w-full"
                    value={billingAddressId}
                    onChange={(e) => setBillingAddressId(e.target.value)}
                  >
                    <option value="">Choose billing address</option>
                    {savedAddresses.map((addr) => (
                      <option key={addr.address_id} value={addr.address_id}>
                        {formatAddress(addr)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              onClick={handleSubmitSelection}
              className="bg-black text-white py-2 rounded-sm"
            >
              Continue
            </button>

            <button
              onClick={() => { setError(""); setMode("create"); }}
              className="bg-gray-300 py-2 rounded-sm"
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
                placeholder="Full Name"
                autoComplete="name"
                required
                value={form.full_name}
                onChange={(e) => updateField("full_name", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="Phone (for delivery questions)"
                type="tel"
                autoComplete="tel"
                value={form.phone}
                onChange={(e) => updateField("phone", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="Address Line 1"
                required
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
                required
                value={form.city}
                onChange={(e) => updateField("city", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="State"
                required
                value={form.state}
                onChange={(e) => updateField("state", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="Postal Code"
                required
                value={form.postal_code}
                onChange={(e) => updateField("postal_code", e.target.value)}
              />

              <input
                className="border p-2 w-full"
                placeholder="County"
                value={form.county}
                onChange={(e) => updateField("county", e.target.value)}
              />

              {error && <p className="text-sm text-red-600">{error}</p>}

              <button
                type="submit"
                className="bg-black text-white w-full py-2 rounded-sm"
              >
                Save Address
              </button>
            </form>

            {savedAddresses.length > 0 && (
              <button
                onClick={() => { setError(""); setMode("select"); }}
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
