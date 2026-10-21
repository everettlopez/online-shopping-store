// An address as it was when the order was placed (OrderAddress in the API)
export type OrderAddress = {
  full_name: string;
  phone?: string | null;
  line1: string;
  line2?: string | null;
  city: string;
  state: string;
  postal_code: string;
  county?: string | null;
  country: string;
};

export default function OrderAddressLines({ address }: { address: OrderAddress | null }) {
  if (!address) return <p className="text-gray-400">Not recorded</p>;

  return (
    <>
      <p>{address.full_name}</p>
      <p>{address.line1}</p>
      {address.line2 && <p>{address.line2}</p>}
      <p>{address.city}, {address.state} {address.postal_code}</p>
      {address.country !== "US" && <p>{address.country}</p>}
      {address.phone && <p>{address.phone}</p>}
    </>
  );
}
